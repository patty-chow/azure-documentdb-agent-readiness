import os
from typing import Dict, Any
from langchain import OpenAI, LLMChain
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

# This module provides a scaffold for a LangChain agent that can query DocumentDB
# The agent wiring uses OpenAI; the actual tool implementations call into the DB
# via helper functions passed in by the runner. This file intentionally keeps
# the database-implementation decoupled so tests can mock the tools.


def build_agent(tools, verbose: bool = False):
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY is not set - the agent cannot run without an LLM key')
    llm = OpenAI(openai_api_key=api_key, temperature=0)
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=verbose,
        memory=memory,
    )
    return agent
