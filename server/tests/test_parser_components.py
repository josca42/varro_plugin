from pathlib import Path

from varro.dashboard.parser import (
    ComponentNode,
    MarkdownNode,
    extract_outputs,
    parse_dashboard_md,
)

TITANIC = (
    Path(__file__).resolve().parents[2]
    / "test_sample"
    / "dashboards"
    / "titanic"
    / "dashboard.md"
)


def test_inline_tag_in_prose_keeps_sentence():
    ast = parse_dashboard_md("Here is some prose mentioning <br /> in the middle.")
    assert len(ast) == 1
    assert isinstance(ast[0], MarkdownNode)
    assert ast[0].content == "Here is some prose mentioning <br /> in the middle."


def test_foreign_open_tag_does_not_swallow_next_component():
    ast = parse_dashboard_md('<span>inline note\n<metric name="real" />')
    metrics = [n for n in ast if isinstance(n, ComponentNode) and n.type == "metric"]
    assert len(metrics) == 1
    assert metrics[0].attrs["name"] == "real"
    assert any(
        isinstance(n, MarkdownNode) and "inline note" in n.content for n in ast
    )


def test_two_tags_on_one_line_emit_both():
    ast = parse_dashboard_md('<metric name="a" /> <metric name="b" />')
    metrics = [n for n in ast if isinstance(n, ComponentNode) and n.type == "metric"]
    assert [m.attrs["name"] for m in metrics] == ["a", "b"]


def test_titanic_dashboard_outputs_all_extracted():
    ast = parse_dashboard_md(TITANIC.read_text())
    outputs = {(o.type, o.name) for o in extract_outputs(ast)}
    expected = {
        ("metric", "passengers"),
        ("metric", "survival_rate"),
        ("metric", "survivors"),
        ("metric", "median_fare"),
        ("fig", "sex_class_survival"),
        ("fig", "survival_counts"),
        ("fig", "age_band_survival"),
        ("fig", "family_survival"),
        ("fig", "fare_band_survival"),
        ("fig", "embarked_class_mix"),
        ("table", "rule_accuracy"),
        ("table", "cohort_summary"),
        ("table", "raw_rows"),
    }
    assert outputs == expected
