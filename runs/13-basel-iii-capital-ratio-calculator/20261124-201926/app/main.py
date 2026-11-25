"""Run aggregation and produce a board-ready Basel III commentary.

If OPENAI_API_KEY is present, the code will attempt to use LangChain + OpenAI
via an agent/tool pattern. To keep verification simple when the key is absent,
this script falls back to a deterministic commentary generator.
"""
import os
from pprint import pformat
from dotenv import load_dotenv

load_dotenv()

from tools.aggregation_tool import aggregate_totals

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")

if not DOCUMENTDB_URI:
    raise RuntimeError("DOCUMENTDB_URI environment variable is required to connect to Azure DocumentDB")

# Basel III thresholds (simple reference values used for commentary)
BASEL_THRESHOLDS = {
    "CET1_min": 0.045,      # 4.5% minimum
    "CET1_buffer": 0.025,   # 2.5% conservation buffer
    "Tier1_min": 0.06,      # 6.0% (CET1 + AT1 where applicable)
    "Total_capital_min": 0.08 # 8.0% minimum
}


def compute_ratios(agg: dict) -> dict:
    rwa = agg.get("rwa", 0.0)
    cet1 = agg.get("cet1", 0.0)
    total = agg.get("total_capital", 0.0)
    if rwa <= 0:
        return {"cet1_ratio": None, "total_ratio": None}
    return {"cet1_ratio": cet1 / rwa, "total_ratio": total / rwa}


def deterministic_board_commentary(agg: dict, ratios: dict) -> str:
    """Generate a short deterministic board-ready commentary given aggregated numbers."""
    cet1_ratio = ratios.get("cet1_ratio")
    total_ratio = ratios.get("total_ratio")
    lines = []
    lines.append("Basel III Capital Adequacy Commentary\n")
    lines.append(f"Aggregated positions: count={agg.get('count')}, RWA={agg.get('rwa'):.2f}")
    lines.append(f"Aggregated CET1: {agg.get('cet1'):.2f}")
    lines.append(f"Aggregated Total Capital: {agg.get('total_capital'):.2f}\n")
    if cet1_ratio is None:
        lines.append("Insufficient RWA to compute ratios.")
        return "\n".join(lines)

    lines.append(f"CET1 ratio (CET1/RWA): {cet1_ratio*100:.2f}%")
    lines.append(f"Total capital ratio (Total/RWA): {total_ratio*100:.2f}%\n")

    # Interpret against thresholds
    cet1_min = BASEL_THRESHOLDS["CET1_min"]
    cet1_buffer = BASEL_THRESHOLDS["CET1_buffer"]
    total_min = BASEL_THRESHOLDS["Total_capital_min"]

    if cet1_ratio >= cet1_min + cet1_buffer:
        lines.append("CET1 position: comfortably above regulatory minimum plus conservation buffer.")
    elif cet1_ratio >= cet1_min:
        lines.append("CET1 position: above regulatory minimum but below conservation buffer — monitor capital generation.")
    else:
        lines.append("CET1 position: below regulatory minimum — immediate remediation and capital actions recommended.")

    if total_ratio >= total_min:
        lines.append("Total capital: meets or exceeds the Basel III total capital minimum.")
    else:
        lines.append("Total capital: below the Basel III minimum — capital raising or risk reduction required.")

    # Short recommendation
    lines.append("\nRecommendation: Maintain close monitoring of CET1 trajectory and prepare a capital plan to restore buffer if needed. Consider targeted risk-weighted-asset reduction or capital issuance depending on the driver of any shortfall.")
    return "\n".join(lines)


def run_agent_with_langchain(agg: dict, ratios: dict) -> str:
    """If OpenAI and LangChain are available and configured, use them to generate a more polished commentary.

    This function is best-effort: the sample keeps LangChain optional so that
    repository verification can run without LLM credentials.
    """
    try:
        from langchain import OpenAI
        from langchain.agents import Tool, initialize_agent, AgentType
    except Exception as e:
        print("LangChain/OpenAI not installed or import failed:", e)
        raise

    # Simple tool that returns the aggregated numbers when invoked by the agent
    def agg_tool_call(_query: str) -> str:
        # return a stable, small JSON-like string representation for the LLM to consume
        return (f"AGGREGATES:\ncount={agg.get('count')}\nRWA={agg.get('rwa'):.2f}\nCET1={agg.get('cet1'):.2f}\nTOTAL={agg.get('total_capital'):.2f}\n"
                f"RATIOS:\nCET1={ratios.get('cet1_ratio'):.4f}\nTOTAL={ratios.get('total_ratio'):.4f}")

    tool = Tool(name="aggregate_totals", func=agg_tool_call, description="Returns aggregated RWA and capital totals; call with no args")

    llm = OpenAI(openai_api_key=OPENAI_KEY, temperature=0.2)
    agent = initialize_agent([tool], llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=False)

    # Craft a prompt-style user request for the agent
    user_request = (
        "You are the bank CFO preparing a short board commentary on capital adequacy. "
        "Using the aggregate_totals tool to fetch numbers, produce a concise (4-8 sentence) board-ready commentary that: "
        "(1) states CET1 and Total Capital ratios as percentages, (2) interprets them against Basel III thresholds: CET1 min 4.5%, conservation buffer 2.5%, Total capital min 8%, and (3) gives 1-2 high-level recommendations. "
        "Call the aggregation tool as needed and then respond with the commentary only."
    )

    return agent.run(user_request)


def main():
    print("Connecting to DocumentDB and running aggregation...")
    agg = aggregate_totals()
    print("Aggregates:")
    print(pformat(agg))
    ratios = compute_ratios(agg)

    # If OPENAI_KEY is present and langchain is installed, try to use it; otherwise produce deterministic commentary
    if OPENAI_KEY:
        try:
            commentary = run_agent_with_langchain(agg, ratios)
        except Exception as e:
            print("LangChain agent failed or not installed; falling back to deterministic commentary:", e)
            commentary = deterministic_board_commentary(agg, ratios)
    else:
        commentary = deterministic_board_commentary(agg, ratios)

    print("\n--- Board-ready commentary ---\n")
    print(commentary)


if __name__ == "__main__":
    main()
