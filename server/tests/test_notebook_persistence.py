import asyncio
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from varro.sql import read_sql_connection_string

PROJECT_ROOT = Path(__file__).resolve().parents[2]


async def _call_jupyter(server_cwd, args, env=None):
    params = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "--project",
            str(PROJECT_ROOT / "server"),
            "python",
            "-m",
            "varro.main",
        ],
        cwd=server_cwd,
        env=env,
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool("jupyter", args)


def test_jupyter_saves_cells_under_project_notebooks_dir(tmp_path):
    project_dir = tmp_path / "project"
    server_cwd = tmp_path / "launcher"
    server_cwd.mkdir()

    result = asyncio.run(
        _call_jupyter(
            server_cwd,
            {"code": "value = 10\nprint(value)", "notebook": "rooted"},
            env={"VARRO_PROJECT_DIR": str(project_dir)},
        )
    )

    saved = project_dir / "notebooks" / "rooted.py"
    assert result.content[0].text == "10"
    assert saved.read_text() == "\n# %%\nvalue = 10\nprint(value)\n"
    assert not (server_cwd / "notebooks" / "rooted.py").exists()


def test_sql_connection_file_lives_under_project_root(tmp_path):
    project_dir = tmp_path / "project"
    config = project_dir / ".varro" / "sql_connection.txt"
    config.parent.mkdir(parents=True)
    config.write_text("# local\nsqlite:///analysis.db\n")

    assert read_sql_connection_string(project_dir) == "sqlite:///analysis.db"
