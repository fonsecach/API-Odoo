from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_models():
    return Mock()


@pytest.fixture
def mock_execute_kw(mock_models):
    mock_models.execute_kw = Mock()
    return mock_models.execute_kw
