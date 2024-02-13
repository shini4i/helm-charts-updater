import pytest

from helm_charts_updater.models import Chart
from helm_charts_updater.models import Dependency
from helm_charts_updater.models import Maintainer


@pytest.mark.parametrize(
    "model, kwargs, expected",
    [
        (
            Maintainer,
            {"name": "John Doe", "email": "john.doe@example.com", "url": "https://example.com"},
            {"name": "John Doe", "email": "john.doe@example.com", "url": "https://example.com"},
        ),
        (Dependency, {"name": "dep1", "version": "1.0.0"}, {"name": "dep1", "version": "1.0.0"}),
        (
            Chart,
            {"name": "chart1", "description": "A test chart", "version": "1.0.0"},
            {"name": "chart1", "description": "A test chart", "version": "1.0.0"},
        ),
    ],
)
def test_models(model, kwargs, expected):
    instance = model(**kwargs)
    for key, value in expected.items():
        assert getattr(instance, key) == value


@pytest.mark.parametrize(
    "model, kwargs",
    [
        (Dependency, {"name": "dep2", "version": "invalid_version"}),
        (
            Chart,
            {"name": "chart2", "description": "Another test chart", "version": "invalid_version"},
        ),
    ],
)
def test_models_invalid_version(model, kwargs):
    with pytest.raises(ValueError):
        model(**kwargs)
