from http import HTTPStatus
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from app.routers.helpdesk_endpoints import (
    list_tickets,
)
from app.services.authentication import authenticate_odoo, connect_to_odoo
from app.services.helpdesk_service import (
    get_helpdesk_info,
    get_helpdesk_info_by_team_and_id,
    get_helpdesk_info_by_team_id,
)


# Testes para helpdesk_service.py
class TestHelpdeskService:
    def test_get_helpdesk_info_success(self, mock_models, mock_execute_kw):
        # Arrange
        expected_data = [
            {'id': 1, 'name': 'Ticket 1'},
            {'id': 2, 'name': 'Ticket 2'},
        ]
        mock_execute_kw.return_value = expected_data

        # Act
        result = get_helpdesk_info(mock_models, 'test_db', 1, 'password')

        # Assert
        assert result == expected_data
        mock_execute_kw.assert_called_once_with(
            'test_db',
            1,
            'password',
            'helpdesk.ticket',
            'search_read',
            [[]],
            {'limit': 100, 'offset': 0},
        )

    def test_get_helpdesk_info_empty(self, mock_models, mock_execute_kw):
        # Arrange
        mock_execute_kw.return_value = []

        # Act
        result = get_helpdesk_info(mock_models, 'test_db', 1, 'password')

        # Assert
        assert result == []

    def test_get_helpdesk_info_exception(self, mock_models, mock_execute_kw):
        # Arrange
        mock_execute_kw.side_effect = Exception('Test error')

        # Act
        result = get_helpdesk_info(mock_models, 'test_db', 1, 'password')

        # Assert
        assert result == []

    def test_get_helpdesk_info_by_team_id_success(
        self, mock_models, mock_execute_kw
    ):
        # Arrange
        expected_data = [
            {'id': 1, 'name': 'Ticket 1', 'team_id': 1},
            {'id': 2, 'name': 'Ticket 2', 'team_id': 1},
        ]
        mock_execute_kw.return_value = expected_data

        # Act
        result = get_helpdesk_info_by_team_id(
            mock_models, 'test_db', 1, 'password', 1
        )

        # Assert
        assert result == expected_data
        mock_execute_kw.assert_called_once_with(
            'test_db',
            1,
            'password',
            'helpdesk.ticket',
            'search_read',
            [[['team_id', '=', 1]]],
            {'limit': 100, 'offset': 0},
        )

    def test_get_helpdesk_info_by_team_and_id_success(
        self, mock_models, mock_execute_kw
    ):
        # Arrange
        expected_data = [{'id': 1, 'name': 'Ticket 1', 'team_id': 1}]
        mock_execute_kw.return_value = expected_data

        # Act
        result = get_helpdesk_info_by_team_and_id(
            mock_models, 'test_db', 1, 'password', 1, 1
        )

        # Assert
        assert result == expected_data
        mock_execute_kw.assert_called_once_with(
            'test_db',
            1,
            'password',
            'helpdesk.ticket',
            'search_read',
            [[['id', '=', 1], ['team_id', '=', 1]]],
        )


# Testes para helpdesk_endpoints.py
class TestHelpdeskEndpoints:
    @pytest.fixture
    def mock_auth(self):
        with patch('app.routers.helpdesk_endpoints.authenticate_odoo') as mock:
            yield mock

    @pytest.fixture
    def mock_connect(self):
        with patch('app.routers.helpdesk_endpoints.connect_to_odoo') as mock:
            mock.return_value = (Mock(), Mock())
            yield mock

    async def test_list_tickets_success(self, mock_auth, mock_connect):
        # Arrange
        mock_auth.return_value = 1
        expected_data = [{'id': 1, 'name': 'Ticket 1'}]

        with patch(
            'app.routers.helpdesk_endpoints.get_helpdesk_info'
        ) as mock_get:
            mock_get.return_value = expected_data

            # Act
            result = await list_tickets()

            # Assert
            assert result == {'chamados': expected_data}

    async def test_list_tickets_auth_failure(self, mock_auth, mock_connect):
        # Arrange
        mock_auth.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await list_tickets()

        assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED

    async def test_list_tickets_no_data(self, mock_auth, mock_connect):
        # Arrange
        mock_auth.return_value = 1

        with patch(
            'app.routers.helpdesk_endpoints.get_helpdesk_info'
        ) as mock_get:
            mock_get.return_value = []

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await list_tickets()

            assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST


# Testes para authentication.py
class TestAuthentication:
    def test_connect_to_odoo_success(self):
        with patch('xmlrpc.client.ServerProxy') as mock_proxy:
            # Act
            common, models = connect_to_odoo('http://test.url')

            # Assert
            assert mock_proxy.call_count == 2
            mock_proxy.assert_any_call('http://test.url/xmlrpc/2/common')
            mock_proxy.assert_any_call('http://test.url/xmlrpc/2/object')

    def test_authenticate_odoo_success(self):
        # Arrange
        mock_common = Mock()
        mock_common.authenticate.return_value = 1

        # Act
        result = authenticate_odoo(mock_common, 'test_db', 'user', 'pass')

        # Assert
        assert result == 1
        mock_common.authenticate.assert_called_once_with(
            'test_db', 'user', 'pass', {}
        )

    def test_authenticate_odoo_failure(self):
        # Arrange
        mock_common = Mock()
        mock_common.authenticate.return_value = False

        # Act
        result = authenticate_odoo(mock_common, 'test_db', 'user', 'pass')

        # Assert
        assert result == False
