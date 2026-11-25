"""The only module that talks to Microsoft Agent Framework's model clients."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Sequence, TypeVar

from agent_framework import Agent, FileSkillsSource, SkillsProvider
from pydantic import BaseModel, ValidationError

from .config import Settings

T = TypeVar("T", bound=BaseModel)


class StageError(RuntimeError):
    """A stage could not produce a usable result."""


def make_client(settings: Settings, max_iterations: int | None = None) -> Any:
    """Create a chat client for the configured provider, with the run's timeout applied."""
    client = _make_client(settings, max_iterations)
    # The OpenAI SDK's default is 10 minutes per request. A reasoning model writing a long
    # structured answer in one piece can exceed that, so the limit is raised here.
    sdk_client = getattr(client, "client", None)
    if sdk_client is not None and hasattr(sdk_client, "timeout"):
        sdk_client.timeout = float(settings.request_timeout_seconds)
        sdk_client.max_retries = settings.request_retries
    return client


def _make_client(settings: Settings, max_iterations: int | None = None) -> Any:
    # max_consecutive_errors_per_request: the framework's default of 3 switched the builder's tools off
    # after three malformed log_decision calls in a row (seen in 4 of the first 25 gpt-5-mini builds),
    # leaving a partial build that says nothing about the service. Raised so the agent can recover.
    loop = {"max_iterations": max_iterations or settings.max_iterations, "max_consecutive_errors_per_request": 10}
    if not settings.model:
        raise StageError("FACTORY_MODEL is not set. Copy .env.example to .env and fill it in.")

    if settings.provider == "azure_openai":
        from agent_framework.openai import OpenAIChatClient

        if not settings.azure_openai_endpoint:
            raise StageError("AZURE_OPENAI_ENDPOINT is not set.")
        if settings.azure_openai_api_key:
            return OpenAIChatClient(
                model=settings.model,
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                function_invocation_configuration=loop,
            )
        from azure.identity import AzureCliCredential

        return OpenAIChatClient(
            model=settings.model,
            azure_endpoint=settings.azure_openai_endpoint,
            credential=AzureCliCredential(),
            function_invocation_configuration=loop,
        )

    if settings.provider == "foundry":
        from agent_framework.foundry import FoundryChatClient
        from azure.identity import AzureCliCredential

        if not settings.foundry_project_endpoint:
            raise StageError("FOUNDRY_PROJECT_ENDPOINT is not set.")
        return FoundryChatClient(
            project_endpoint=settings.foundry_project_endpoint,
            model=settings.model,
            credential=AzureCliCredential(),
            function_invocation_configuration=loop,
        )

    if settings.provider == "openai":
        # OpenAI itself, or any endpoint that speaks the OpenAI API (set OPENAI_BASE_URL).
        from agent_framework.openai import OpenAIChatClient, OpenAIChatCompletionClient

        if not settings.openai_api_key:
            raise StageError("OPENAI_API_KEY is not set.")
        if settings.openai_api_style not in ("responses", "chat_completions"):
            raise StageError("OPENAI_API_STYLE must be 'responses' or 'chat_completions'.")
        client_type = OpenAIChatClient if settings.openai_api_style == "responses" else OpenAIChatCompletionClient
        return client_type(
            model=settings.model,
            api_key=settings.openai_api_key,
            # Always explicit, so an empty OPENAI_BASE_URL in the environment cannot leak in.
            base_url=settings.openai_base_url or "https://api.openai.com/v1",
            function_invocation_configuration=loop,
        )

    raise StageError(f"Unknown FACTORY_PROVIDER '{settings.provider}'. Use azure_openai, foundry or openai.")


def skills_provider(skill_roots: Sequence[Path]) -> SkillsProvider | None:
    """Give an agent the installed agent skills (loaded on demand)."""
    if not skill_roots:
        return None
    return SkillsProvider(
        FileSkillsSource([str(p) for p in skill_roots], search_depth=4),
        disable_load_skill_approval=True,
        disable_read_skill_resource_approval=True,
    )


async def run_agent(
    client: Any,
    *,
    name: str,
    instructions: str,
    task: str,
    output_type: type[T],
    tools: Sequence[Any] = (),
    context_providers: Sequence[Any] = (),
    middleware: Sequence[Any] = (),
) -> T:
    """Run one agent to completion and return its structured result."""
    agent = Agent(
        client,
        instructions,
        name=name,
        tools=list(tools) or None,
        context_providers=[p for p in context_providers if p is not None] or None,
        middleware=list(middleware) or None,
    )
    async with agent:
        response = await agent.run(task, options={"response_format": output_type})

    try:
        value = response.value
    except Exception:  # the framework raises if the text is not valid for the schema
        value = None
    if isinstance(value, output_type):
        return value
    return parse_structured(response.text or "", output_type, name)


def parse_structured(text: str, output_type: type[T], agent_name: str = "agent") -> T:
    """Fallback for providers that return the JSON as plain text."""
    candidate = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", candidate, re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
    elif not candidate.startswith("{"):
        start, end = candidate.find("{"), candidate.rfind("}")
        if start != -1 and end > start:
            candidate = candidate[start : end + 1]
    try:
        return output_type.model_validate(json.loads(candidate))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise StageError(
            f"{agent_name} did not return a valid {output_type.__name__}.\n{exc}\n--- response ---\n{text[:2000]}"
        ) from exc
