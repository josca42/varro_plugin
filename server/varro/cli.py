import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="varro", description="Run the varro dashboard HTTP server."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5011)
    parser.add_argument("--dir", default="dashboards", help="Dashboards folder")
    args = parser.parse_args()

    import uvicorn

    from varro.dashboard import build_app

    uvicorn.run(build_app(Path(args.dir)), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
