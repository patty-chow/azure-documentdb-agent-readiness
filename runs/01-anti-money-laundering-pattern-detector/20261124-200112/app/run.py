"""CLI entrypoint for the AML agent sample."""
import argparse
from aml_agent.analysis import analyze
from aml_agent.llm import get_llm_client


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("analyze", nargs="?", help="run analysis")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM if configured via OPENAI_API_KEY")
    args = parser.parse_args()
    use_llm = args.use_llm
    llm = None
    if use_llm:
        llm = get_llm_client()
    results = analyze(use_llm=use_llm, llm_client=llm)
    print("Analysis results:")
    for r in results:
        print(r)

if __name__ == '__main__':
    main()
