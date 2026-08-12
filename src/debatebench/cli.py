import argparse
import sys

from dotenv import load_dotenv

from .config import load_config
from .debate import run_debate


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(prog="debatebench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a debate from a config file")
    run_parser.add_argument("config", help="Path to a YAML debate config")

    args = parser.parse_args()

    if args.command == "run":
        config = load_config(args.config)
        report = run_debate(config)
        print("Final stats (wins per agent):")
        for name, wins in sorted(report.items(), key=lambda kv: -kv[1]):
            print(f"  {name}: {wins}")


if __name__ == "__main__":
    sys.exit(main())
