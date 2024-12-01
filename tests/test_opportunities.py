from unittest.mock import patch

import pytest

from app.Services.crm_service import get_opportunities_info


def test_get_opportunities_info_sucesso(mock_models, mock_execute_kw):
    resultado_esperado = [
        {'id': 1, 'name': 'Oportunidade 1'},
        {'id': 2, 'name': 'Oportunidade 2'},
    ]
    mock_execute_kw.return_value = resultado_esperado

    resultado = get_opportunities_info(mock_models, 'test_db', 1, 'senha')

    assert resultado == resultado_esperado
    mock_execute_kw.assert_called_once_with(
        'test_db',
        1,
        'senha',
        'crm.lead',
        'search_read',
        [[]],
        {'limit': 100, 'offset': 0},
    )


def test_get_opportunities_info_com_limite_e_offset_personalizados(
    mock_models, mock_execute_kw
):
    resultado_esperado = [{'id': 3, 'name': 'Oportunidade 3'}]
    mock_execute_kw.return_value = resultado_esperado

    resultado = get_opportunities_info(
        mock_models, 'test_db', 1, 'senha', limit=1, offset=2
    )

    assert resultado == resultado_esperado
    mock_execute_kw.assert_called_once_with(
        'test_db',
        1,
        'senha',
        'crm.lead',
        'search_read',
        [[]],
        {'limit': 1, 'offset': 2},
    )


def test_get_opportunities_info_resultado_vazio(mock_models, mock_execute_kw):
    mock_execute_kw.return_value = []

    resultado = get_opportunities_info(mock_models, 'test_db', 1, 'senha')

    assert resultado == []
    mock_execute_kw.assert_called_once()


def test_get_opportunities_info_tratamento_de_excecao(
    mock_models, mock_execute_kw
):
    mock_execute_kw.side_effect = Exception('Erro de teste')

    with patch('builtins.print') as mock_print:
        resultado = get_opportunities_info(mock_models, 'test_db', 1, 'senha')

    assert resultado == []
    mock_print.assert_called_once_with(
        'Erro ao buscar e ler informações das oportunidades: Erro de teste'
    )


@pytest.mark.parametrize(
    'limit, offset',
    [
        (50, 0),
        (100, 50),
        (200, 100),
    ],
)
def test_get_opportunities_info_parametrizado(
    mock_models, mock_execute_kw, limit, offset
):
    resultado_esperado = [
        {'id': i, 'name': f'Oportunidade {i}'} for i in range(1, limit + 1)
    ]
    mock_execute_kw.return_value = resultado_esperado

    resultado = get_opportunities_info(
        mock_models, 'test_db', 1, 'senha', limit=limit, offset=offset
    )

    assert resultado == resultado_esperado
    mock_execute_kw.assert_called_once_with(
        'test_db',
        1,
        'senha',
        'crm.lead',
        'search_read',
        [[]],
        {'limit': limit, 'offset': offset},
    )
