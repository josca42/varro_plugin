import argparse
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="varro", description="Run the varro dashboard HTTP server."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5011)
    parser.add_argument("--project-dir", required=True, help="Project folder")
    args = parser.parse_args()

    os.environ["VARRO_PROJECT_DIR"] = str(Path(args.project_dir).resolve())

    import uvicorn

    from varro.dashboard import build_app

    uvicorn.run(build_app(Path(args.project_dir)), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
