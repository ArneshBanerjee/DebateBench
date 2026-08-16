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

    web_parser = subparsers.add_parser("web", help="Run a debate in the browser")
    web_parser.add_argument(
        "config", nargs="?", help="Optional YAML config to prefill the form with"
    )
    web_parser.add_argument("--port", type=int, default=7777, help="Port to listen on")
    web_parser.add_argument(
        "--no-browser", action="store_true", help="Do not open a browser window"
    )

    args = parser.parse_args()

    if args.command == "run":
        config = load_config(args.config)
        report = run_debate(config)
        print("Final stats (wins per agent):")
        for name, wins in sorted(report.items(), key=lambda kv: -kv[1]):
            print(f"  {name}: {wins}")
    elif args.command == "web":
        # Imported lazily so `run` does not pay to set up the server module.
        from .web import serve

        serve(port=args.port, config_path=args.config, open_browser=not args.no_browser)


if __name__ == "__main__":
    sys.exit(main())
