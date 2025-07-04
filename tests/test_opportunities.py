from unittest.mock import patch, AsyncMock

import pytest
from fastapi import HTTPException

from app.services.crm_service import get_opportunities_info, create_opportunity_unified, validate_cpf_cnpj
from app.schemas.schemas import OpportunityCreateUnified, OpportunityReturn


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


# ============== TESTES PARA CRIAÇÃO DE OPORTUNIDADES UNIFICADAS ==============

class TestValidateCpfCnpj:
    """Testes para a função validate_cpf_cnpj"""
    
    def test_validate_cnpj_valido(self):
        """Testa validação de CNPJ válido"""
        cnpj = "12345678000195"
        resultado = validate_cpf_cnpj(cnpj)
        assert resultado == "12345678000195"
    
    def test_validate_cpf_valido(self):
        """Testa validação de CPF válido"""
        cpf = "12345678901"
        resultado = validate_cpf_cnpj(cpf)
        assert resultado == "12345678901"
    
    def test_validate_cnpj_com_formatacao(self):
        """Testa validação de CNPJ com máscara"""
        cnpj = "12.345.678/0001-95"
        resultado = validate_cpf_cnpj(cnpj)
        assert resultado == "12345678000195"
    
    def test_validate_cpf_com_formatacao(self):
        """Testa validação de CPF com máscara"""
        cpf = "123.456.789-01"
        resultado = validate_cpf_cnpj(cpf)
        assert resultado == "12345678901"
    
    def test_validate_documento_vazio(self):
        """Testa erro para documento vazio"""
        with pytest.raises(ValueError, match="CPF/CNPJ não pode estar vazio"):
            validate_cpf_cnpj("")
    
    def test_validate_documento_none(self):
        """Testa erro para documento None"""
        with pytest.raises(ValueError, match="CPF/CNPJ não pode estar vazio"):
            validate_cpf_cnpj(None)
    
    def test_validate_documento_tamanho_invalido(self):
        """Testa erro para documento com tamanho inválido"""
        with pytest.raises(ValueError, match="Documento deve conter 11 dígitos \\(CPF\\) ou 14 dígitos \\(CNPJ\\)"):
            validate_cpf_cnpj("123456789")  # 9 dígitos
    
    def test_validate_documento_apenas_letras(self):
        """Testa documento com apenas letras"""
        with pytest.raises(ValueError, match="Documento deve conter 11 dígitos \\(CPF\\) ou 14 dígitos \\(CNPJ\\)"):
            validate_cpf_cnpj("abcdefghijk")  # 11 letras


class TestCreateOpportunityUnified:
    """Testes para a função create_opportunity_unified"""
    
    @pytest.mark.asyncio
    async def test_create_opportunity_apenas_nome(self):
        """Testa criação de oportunidade apenas com nome"""
        # Dados de entrada
        opportunity_data = OpportunityCreateUnified(name="Minha Oportunidade Teste")
        
        # Mocks
        mock_odoo_client = AsyncMock()
        mock_odoo_client.create.return_value = 12345
        mock_odoo_client.search_read.return_value = [{
            'name': 'Minha Oportunidade Teste',
            'partner_id': False,
            'user_id': [3, 'Vendedor Padrão'],
            'team_id': False,
            'stage_id': [1, 'Novo'],
            'expected_revenue': 0.0
        }]
        
        with patch('app.services.crm_service.get_odoo_client', return_value=mock_odoo_client):
            resultado = await create_opportunity_unified(opportunity_data)
        
        # Verificações
        assert isinstance(resultado, OpportunityReturn)
        assert resultado.opportunity_id == 12345
        assert resultado.name == "Minha Oportunidade Teste"
        assert resultado.partner_id is None
        assert resultado.user_id == 3
        assert resultado.team_id is None
        assert resultado.stage_id == 1
        assert resultado.expected_revenue == 0.0
        
        # Verifica se create foi chamado com dados corretos
        mock_odoo_client.create.assert_called_once()
        call_args = mock_odoo_client.create.call_args[0]
        assert call_args[0] == 'crm.lead'
        assert call_args[1]['name'] == 'Minha Oportunidade Teste'
        assert call_args[1]['type'] == 'opportunity'
        assert call_args[1]['active'] == True
        assert call_args[1]['user_id'] == 3
        assert 'partner_id' not in call_args[1]  # Não deve ter partner_id
    
    @pytest.mark.asyncio
    async def test_create_opportunity_com_empresa_e_cnpj(self):
        """Testa criação de oportunidade com empresa e CNPJ"""
        # Dados de entrada
        opportunity_data = OpportunityCreateUnified(
            name="Oportunidade INSS",
            company_name="Empresa Teste LTDA",
            company_cnpj="12345678000195",
            x_studio_tese="inss",
            team_id=6,
            x_studio_selection_field_37f_1ibrq64l3="32"
        )
        
        # Mocks
        mock_odoo_client = AsyncMock()
        mock_odoo_client.create.return_value = 98765
        mock_odoo_client.search_read.return_value = [{
            'name': 'Oportunidade INSS',
            'partner_id': [555, 'Empresa Teste LTDA'],
            'user_id': [3, 'Vendedor Padrão'],
            'team_id': [6, 'Equipe Vendas'],
            'stage_id': [1, 'Novo'],
            'expected_revenue': 0.0
        }]
        
        with patch('app.services.crm_service.get_odoo_client', return_value=mock_odoo_client), \
             patch('app.services.crm_service.get_or_create_partner_by_vat', return_value=555) as mock_partner:
            
            resultado = await create_opportunity_unified(opportunity_data)
        
        # Verificações
        assert isinstance(resultado, OpportunityReturn)
        assert resultado.opportunity_id == 98765
        assert resultado.name == "Oportunidade INSS"
        assert resultado.partner_id == 555
        assert resultado.user_id == 3
        assert resultado.team_id == 6
        assert resultado.stage_id == 1
        
        # Verifica se partner foi buscado/criado
        mock_partner.assert_called_once_with(
            vat_number="12345678000195",
            company_name="Empresa Teste LTDA"
        )
        
        # Verifica se create foi chamado com dados corretos
        mock_odoo_client.create.assert_called_once()
        call_args = mock_odoo_client.create.call_args[0]
        assert call_args[0] == 'crm.lead'
        opp_data = call_args[1]
        assert opp_data['name'] == 'Oportunidade INSS'
        assert opp_data['partner_id'] == 555
        assert opp_data['user_id'] == 3
        assert opp_data['team_id'] == 6
        assert opp_data['type'] == 'opportunity'
        assert opp_data['active'] == True
        assert opp_data['x_studio_tese'] == 'inss'
        assert opp_data['x_studio_selection_field_37f_1ibrq64l3'] == '32'
    
    @pytest.mark.asyncio
    async def test_create_opportunity_com_expected_revenue(self):
        """Testa criação de oportunidade com receita esperada"""
        # Dados de entrada
        opportunity_data = OpportunityCreateUnified(
            name="Oportunidade com Receita",
            expected_revenue=50000.75
        )
        
        # Mocks
        mock_odoo_client = AsyncMock()
        mock_odoo_client.create.return_value = 11111
        mock_odoo_client.search_read.return_value = [{
            'name': 'Oportunidade com Receita',
            'partner_id': False,
            'user_id': [3, 'Vendedor Padrão'],
            'team_id': False,
            'stage_id': [1, 'Novo'],
            'expected_revenue': 50000.75
        }]
        
        with patch('app.services.crm_service.get_odoo_client', return_value=mock_odoo_client):
            resultado = await create_opportunity_unified(opportunity_data)
        
        # Verificações
        assert resultado.expected_revenue == 50000.75
        
        # Verifica se create foi chamado com receita
        call_args = mock_odoo_client.create.call_args[0]
        assert call_args[1]['expected_revenue'] == 50000.75
    
    @pytest.mark.asyncio
    async def test_create_opportunity_cnpj_invalido(self):
        """Testa erro para CNPJ inválido"""
        opportunity_data = OpportunityCreateUnified(
            name="Oportunidade Teste",
            company_cnpj="123456789"  # CNPJ inválido
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await create_opportunity_unified(opportunity_data)
        
        assert exc_info.value.status_code == 400
        assert "Documento deve conter 11 dígitos" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_create_opportunity_falha_criar_partner(self):
        """Testa erro quando falha ao criar parceiro"""
        opportunity_data = OpportunityCreateUnified(
            name="Oportunidade Teste",
            company_name="Empresa Teste",
            company_cnpj="12345678000195"
        )
        
        with patch('app.services.crm_service.get_odoo_client'), \
             patch('app.services.crm_service.get_or_create_partner_by_vat', return_value=None):
            
            with pytest.raises(HTTPException) as exc_info:
                await create_opportunity_unified(opportunity_data)
        
        assert exc_info.value.status_code == 400
        assert "Não foi possível criar/encontrar cliente" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_create_opportunity_falha_odoo_create(self):
        """Testa erro quando Odoo falha ao criar oportunidade"""
        opportunity_data = OpportunityCreateUnified(name="Oportunidade Teste")
        
        mock_odoo_client = AsyncMock()
        mock_odoo_client.create.return_value = None  # Falha ao criar
        
        with patch('app.services.crm_service.get_odoo_client', return_value=mock_odoo_client):
            with pytest.raises(HTTPException) as exc_info:
                await create_opportunity_unified(opportunity_data)
        
        assert exc_info.value.status_code == 400
        assert "Não foi possível criar a oportunidade" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_create_opportunity_falha_buscar_detalhes(self):
        """Testa erro quando falha ao buscar detalhes da oportunidade criada"""
        opportunity_data = OpportunityCreateUnified(name="Oportunidade Teste")
        
        mock_odoo_client = AsyncMock()
        mock_odoo_client.create.return_value = 12345
        mock_odoo_client.search_read.return_value = []  # Não encontra a oportunidade criada
        
        with patch('app.services.crm_service.get_odoo_client', return_value=mock_odoo_client):
            with pytest.raises(HTTPException) as exc_info:
                await create_opportunity_unified(opportunity_data)
        
        assert exc_info.value.status_code == 500
        assert "Oportunidade criada mas não foi possível buscar detalhes" in str(exc_info.value.detail)
