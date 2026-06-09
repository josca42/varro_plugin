import ast

from varro import notebook as nb
from varro.shell import JUPYTER_INITIAL_IMPORTS, get_shell


def test_embedded_marker_round_trips_to_one_cell():
    code = 'note = """\n# %% TODO\n"""'
    cells = nb.parse_cells(f"# %%\n{code}\n")
    assert cells == [code]


def test_comment_marker_inside_cell_not_a_separator():
    code = "x = 1  # %% not a marker\ny = 2"
    cells = nb.parse_cells(f"# %%\n{code}\n")
    assert cells == [code]


def test_two_real_markers_split_into_two_cells():
    cells = nb.parse_cells("# %%\na = 1\n# %%\nb = 2\n")
    assert cells == ["a = 1", "b = 2"]


def test_query_with_triple_quotes_serializes_to_parseable_python():
    query = 'SELECT """ AS q, \'x\' FROM t WHERE c = "y"'
    cell = f"df = run_sql({query.strip()!r})"
    ast.parse(cell)
    call = ast.parse(cell).body[0].value
    assert call.args[0].value == query


def test_startup_replay_with_failing_cell_does_not_raise(tmp_path):
    path = tmp_path / "broken.py"
    path.write_text("# %%\nimport a_package_that_does_not_exist\n# %%\nok = 123\n")
    shell = get_shell()
    shell.run_cell(JUPYTER_INITIAL_IMPORTS)
    for cell_src in nb.parse_cells(path.read_text()):
        result = shell.run_cell(cell_src)
        if result.error_in_exec:
            continue
    assert shell.user_ns.get("ok") == 123
