from sqlalchemy import Boolean, Date, String

from varro.dashboard.queries import _infer_param_type


def test_ordinary_names_are_strings():
    for name in ("store", "customer", "total", "top", "tom", "autonomy", "token", "stop"):
        assert _infer_param_type(name, "x") is String


def test_date_filter_names_are_dates():
    for name in ("date", "period_from", "period_to", "sale_date"):
        assert _infer_param_type(name, "2024-01-01") is Date


def test_bool_value_is_boolean():
    assert _infer_param_type("active", True) is Boolean
