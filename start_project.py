import argparse

from pathlib import Path
from src.sandbox.instantiate import PythonSandbox, FrontendSandbox, DatabaseSandbox

ROOT = Path(__file__).parent


def start(command_line_args):
    folder = command_line_args.project_name

    print("Starting database container...")
    DatabaseSandbox(command_line_args.project_name)

    sandbox_backend = PythonSandbox(command_line_args.project_name)
    sandbox_frontend = FrontendSandbox(command_line_args.project_name)

    with open(ROOT / f"projects/{folder}/backend/index.py", "r") as f:
        backend_string = f.read()

    with open(ROOT / f"projects/{folder}/frontend/index.html", "r") as f:
        frontend_string = f.read()

    print("Starting backend container...")
    sandbox_backend.trigger_execution_pipeline(
        backend_string,
        dependencies=["FastAPI", "uvicorn", "asyncpg", "pydantic", "pandas", "numpy"],
    )

    print("Starting frontend container...")
    sandbox_frontend.trigger_execution_pipeline(frontend_string)
    print("Successfully started all containers. Enjoy!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="argparse")
    parser.add_argument(
        "-p",
        "--project_name",
        type=str,
        help="Folder name (project name) of the project you want to start",
        required=True,
    )

    start(parser.parse_args())
