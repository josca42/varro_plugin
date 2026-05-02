from functools import cache
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from varro.dashboard import Metric, output

DATA = Path(__file__).resolve().parents[2] / "data" / "train.csv"
FARE_LABELS = ["low", "mid-low", "mid-high", "high"]


def _fare_band(fare: pd.Series) -> pd.Series:
    unique = fare.dropna().nunique()
    if unique < 2:
        return pd.Series(pd.NA, index=fare.index, dtype="category")
    codes = pd.qcut(fare, min(4, unique), labels=False, duplicates="drop")
    return codes.map(dict(enumerate(FARE_LABELS))).astype("category")


@cache
def _dataset() -> pd.DataFrame:
    return pd.read_csv(DATA)


def _load(filters: dict) -> pd.DataFrame:
    df = _dataset()
    sex = filters.get("sex", "all")
    pclass = filters.get("pclass", "all")
    embarked = filters.get("embarked", "all")

    if sex and sex != "all":
        df = df[df.Sex == sex]
    if pclass and pclass != "all":
        df = df[df.Pclass == int(pclass)]
    if embarked and embarked != "all":
        df = df[df.Embarked == embarked]

    df = df.copy()
    df["Title"] = df.Name.str.extract(r",\s*([^.]+)\.")
    df["Title"] = df["Title"].replace({"Mlle": "Miss", "Ms": "Miss", "Mme": "Mrs"})
    rare = df.Title.value_counts()
    df.loc[df.Title.isin(rare[rare < 10].index), "Title"] = "Rare"
    df["FamilySize"] = df.SibSp + df.Parch + 1
    df["FamilyGroup"] = pd.cut(
        df.FamilySize,
        [0, 1, 4, 20],
        labels=["alone", "small family", "large family"],
    )
    df["AgeBand"] = pd.cut(
        df.Age,
        [0, 12, 18, 35, 60, 100],
        labels=["child", "teen", "young adult", "adult", "senior"],
    )
    df["FareBand"] = _fare_band(df.Fare)
    return df


def _rate_table(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    grouped = df.groupby(columns, observed=True).Survived
    out = grouped.agg(passengers="count", survivors="sum", survival_rate="mean")
    out = out.reset_index()
    out["survival_rate"] = (out.survival_rate * 100).round(1)
    return out


def _format_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "survival_rate" in out:
        out["survival_rate"] = out.survival_rate.map(lambda v: f"{v:.1f}%")
    return out


@output
def passengers(filters: dict) -> Metric:
    return Metric(value=len(_load(filters)), label="Passengers", format="number")


@output
def survival_rate(filters: dict) -> Metric:
    df = _load(filters)
    return Metric(
        value=float(df.Survived.mean()) if len(df) else 0,
        label="Survival rate",
        format="percent",
    )


@output
def survivors(filters: dict) -> Metric:
    df = _load(filters)
    return Metric(value=int(df.Survived.sum()), label="Survivors", format="number")


@output
def median_fare(filters: dict) -> Metric:
    df = _load(filters)
    return Metric(
        value=float(df.Fare.median()) if len(df) else 0,
        label="Median fare",
        format="currency",
    )


@output
def sex_class_survival(filters: dict):
    df = _load(filters)
    data = _rate_table(df, ["Sex", "Pclass"])
    fig = go.Figure()
    colors = {"female": "#059669", "male": "#18181b"}
    for sex, group in data.groupby("Sex"):
        fig.add_bar(
            name=sex,
            x=group.Pclass.astype(str),
            y=group.survival_rate,
            text=[f"{v:.1f}%" for v in group.survival_rate],
            marker_color=colors.get(sex, "#577590"),
            textposition="outside",
        )
    fig.update_layout(
        title="Survival by sex and class",
        xaxis_title="Class",
        yaxis_title="Survival rate (%)",
        barmode="group",
        height=360,
        yaxis_range=[0, 105],
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=48, r=24, t=64, b=48),
    )
    return fig


@output
def survival_counts(filters: dict):
    df = _load(filters)
    data = df.assign(Outcome=df.Survived.map({0: "died", 1: "survived"}))
    data = data.groupby(["Pclass", "Outcome"], as_index=False).PassengerId.count()
    fig = go.Figure()
    colors = {"survived": "#059669", "died": "#a1a1aa"}
    for outcome, group in data.groupby("Outcome"):
        fig.add_bar(
            name=outcome,
            x=group.Pclass.astype(str),
            y=group.PassengerId,
            text=group.PassengerId,
            marker_color=colors[outcome],
            textposition="outside",
        )
    fig.update_layout(
        title="Outcome counts by class",
        xaxis_title="Class",
        yaxis_title="Passengers",
        barmode="group",
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=48, r=24, t=64, b=48),
    )
    return fig


@output
def age_band_survival(filters: dict):
    df = _load(filters).dropna(subset=["AgeBand"])
    data = _rate_table(df, ["AgeBand"])
    fig = go.Figure(
        go.Bar(
            x=data.AgeBand.astype(str),
            y=data.survival_rate,
            text=[f"{v:.1f}%" for v in data.survival_rate],
            marker_color="#059669",
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Survival by age band",
        xaxis_title="Age band",
        yaxis_title="Survival rate (%)",
        height=360,
        yaxis_range=[0, 100],
        margin=dict(l=48, r=24, t=64, b=48),
    )
    return fig


@output
def family_survival(filters: dict):
    df = _load(filters)
    data = _rate_table(df, ["FamilyGroup"])
    colors = ["#18181b", "#059669", "#a1a1aa"]
    fig = go.Figure(
        go.Bar(
            x=data.FamilyGroup.astype(str),
            y=data.survival_rate,
            text=[f"{v:.1f}%" for v in data.survival_rate],
            marker_color=colors[: len(data)],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Survival by travel party size",
        xaxis_title="Travel party",
        yaxis_title="Survival rate (%)",
        height=360,
        yaxis_range=[0, 100],
        margin=dict(l=48, r=24, t=64, b=48),
    )
    return fig


@output
def fare_band_survival(filters: dict):
    df = _load(filters)
    data = _rate_table(df, ["FareBand"])
    fig = go.Figure(
        go.Bar(
            x=data.FareBand.astype(str),
            y=data.survival_rate,
            text=[f"{v:.1f}%" for v in data.survival_rate],
            marker_color="#059669",
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Survival by fare quartile",
        xaxis_title="Fare quartile",
        yaxis_title="Survival rate (%)",
        height=360,
        yaxis_range=[0, 100],
        margin=dict(l=48, r=24, t=64, b=48),
    )
    return fig


@output
def embarked_class_mix(filters: dict):
    df = _load(filters).dropna(subset=["Embarked"])
    data = df.groupby(["Embarked", "Pclass"], as_index=False).PassengerId.count()
    fig = go.Figure()
    colors = {1: "#059669", 2: "#18181b", 3: "#a1a1aa"}
    for pclass, group in data.groupby("Pclass"):
        fig.add_bar(
            name=f"Class {pclass}",
            x=group.Embarked,
            y=group.PassengerId,
            text=group.PassengerId,
            marker_color=colors[pclass],
            textposition="inside",
        )
    fig.update_layout(
        title="Class mix by embarkation port",
        xaxis_title="Embarked",
        yaxis_title="Passengers",
        barmode="stack",
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=48, r=24, t=64, b=48),
    )
    return fig


@output
def rule_accuracy(filters: dict) -> pd.DataFrame:
    df = _load(filters)
    rules = [
        ("gender only: female survives", df.Sex.eq("female")),
        ("female or child under 10", df.Sex.eq("female") | df.Age.lt(10)),
        (
            "female or class 1/2 child under 10",
            df.Sex.eq("female") | (df.Age.lt(10) & df.Pclass.isin([1, 2])),
        ),
        (
            "female class 1/2 plus children under 10",
            (df.Sex.eq("female") & df.Pclass.isin([1, 2])) | df.Age.lt(10),
        ),
    ]
    rows = []
    for rule, pred in rules:
        rows.append(
            {
                "rule": rule,
                "accuracy": f"{(pred.astype(int).eq(df.Survived).mean() * 100):.1f}%",
                "predicted_survivors": int(pred.sum()),
            }
        )
    return pd.DataFrame(rows).sort_values("accuracy", ascending=False)


@output
def cohort_summary(filters: dict) -> pd.DataFrame:
    df = _load(filters)
    data = _rate_table(df, ["Sex", "Pclass"])
    data = data.sort_values(["Sex", "Pclass"])
    return _format_table(data)


@output
def raw_rows(filters: dict) -> pd.DataFrame:
    df = _load(filters)
    cols = [
        "PassengerId",
        "Survived",
        "Pclass",
        "Name",
        "Sex",
        "Age",
        "SibSp",
        "Parch",
        "Fare",
        "Embarked",
        "Title",
        "FamilySize",
    ]
    return df[cols].head(100).reset_index(drop=True)
