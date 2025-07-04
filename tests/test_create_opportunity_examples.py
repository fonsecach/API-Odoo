"""
Exemplos práticos de testes para criação de oportunidades.
Este arquivo demonstra os casos de uso específicos solicitados.
"""

from unittest.mock import patch, AsyncMock
import pytest
from app.services.crm_service import create_opportunity_unified
from app.schemas.schemas import OpportunityCreateUnified


class TestCreateOpportunityExamples:
    """Exemplos específicos de criação de oportunidades conforme solicitado"""
    
    @pytest.mark.asyncio
    async def test_create_opportunity_apenas_nome_exemplo(self):
        """
        EXEMPLO 1: Criação de oportunidade considerando apenas o nome
        
        Requisição:
        {
            "name": "Minha Nova Oportunidade"
        }
        """
        # Dados de entrada - APENAS NOME (conforme solicitado)
        opportunity_data = OpportunityCreateUnified(
            name="Minha Nova Oportunidade"
        )
        
        # Mock do cliente Odoo
        mock_odoo_client = AsyncMock()
        mock_odoo_client.create.return_value = 12345
        mock_odoo_client.search_read.return_value = [{
            'name': 'Minha Nova Oportunidade',
            'partner_id': False,
            'user_id': [3, 'Vendedor Padrão'],  # user_id default = 3
            'team_id': False,
            'stage_id': [1, 'Novo'],
            'expected_revenue': 0.0
        }]
        
        # Execução
        with patch('app.services.crm_service.get_odoo_client', return_value=mock_odoo_client):
            resultado = await create_opportunity_unified(opportunity_data)
        
        # Verificações
        assert resultado.opportunity_id == 12345
        assert resultado.name == "Minha Nova Oportunidade"
        assert resultado.partner_id is None  # Sem empresa vinculada
        assert resultado.user_id == 3  # Default
        assert resultado.team_id is None  # Sem equipe específica
        
        # Verifica dados enviados para o Odoo
        call_args = mock_odoo_client.create.call_args[0]
        opp_data = call_args[1]
        assert opp_data['name'] == 'Minha Nova Oportunidade'
        assert opp_data['type'] == 'opportunity'  # Sempre opportunity
        assert opp_data['active'] == True
        assert opp_data['user_id'] == 3
        assert 'partner_id' not in opp_data  # Não deve ter parceiro
        
        print("✅ EXEMPLO 1 PASSOU: Oportunidade criada apenas com nome")

    @pytest.mark.asyncio 
    async def test_create_opportunity_completa_exemplo(self):
        """
        EXEMPLO 2: Criação com todos os campos solicitados
        
        Requisição:
        {
            "name": "Oportunidade INSS Empresa ABC",
            "company_name": "EMPRESA ABC LTDA",
            "company_cnpj": "12345678000195", 
            "x_studio_tese": "inss",
            "team_id": 6,
            "x_studio_selection_field_37f_1ibrq64l3": "32"
        }
        """
        # Dados de entrada - CASO COMPLETO (conforme solicitado)
        opportunity_data = OpportunityCreateUnified(
            name="Oportunidade INSS Empresa ABC",
            company_name="EMPRESA ABC LTDA", 
            company_cnpj="12345678000195",
            x_studio_tese="inss",  # Tese = INSS
            team_id=6,  # Team ID = 6
            x_studio_selection_field_37f_1ibrq64l3="32"  # Parceiro comercial = '32'
        )
        
        # Mocks
        mock_odoo_client = AsyncMock()
        mock_odoo_client.create.return_value = 98765
        mock_odoo_client.search_read.return_value = [{
            'name': 'Oportunidade INSS Empresa ABC',
            'partner_id': [555, 'EMPRESA ABC LTDA'],
            'user_id': [3, 'Vendedor Padrão'],
            'team_id': [6, 'Equipe INSS'],
            'stage_id': [1, 'Novo'],
            'expected_revenue': 0.0
        }]
        
        # Execução
        with patch('app.services.crm_service.get_odoo_client', return_value=mock_odoo_client), \
             patch('app.services.crm_service.get_or_create_partner_by_vat', return_value=555) as mock_partner:
            
            resultado = await create_opportunity_unified(opportunity_data)
        
        # Verificações
        assert resultado.opportunity_id == 98765
        assert resultado.name == "Oportunidade INSS Empresa ABC"
        assert resultado.partner_id == 555  # Cliente criado/encontrado
        assert resultado.user_id == 3
        assert resultado.team_id == 6  # Equipe específica
        
        # Verifica criação de parceiro
        mock_partner.assert_called_once_with(
            vat_number="12345678000195",
            company_name="EMPRESA ABC LTDA"
        )
        
        # Verifica dados enviados para o Odoo
        call_args = mock_odoo_client.create.call_args[0]
        opp_data = call_args[1]
        assert opp_data['name'] == 'Oportunidade INSS Empresa ABC'
        assert opp_data['partner_id'] == 555
        assert opp_data['team_id'] == 6
        assert opp_data['x_studio_tese'] == 'inss'
        assert opp_data['x_studio_selection_field_37f_1ibrq64l3'] == '32'
        assert opp_data['type'] == 'opportunity'
        assert opp_data['active'] == True
        
        print("✅ EXEMPLO 2 PASSOU: Oportunidade criada com empresa, CNPJ, tese INSS, team_id=6 e parceiro comercial='32'")

    @pytest.mark.asyncio
    async def test_create_opportunity_com_cpf_exemplo(self):
        """
        EXEMPLO 3: Criação com CPF (11 dígitos)
        
        Requisição:
        {
            "name": "Oportunidade Pessoa Física",
            "company_name": "João Silva",
            "company_cnpj": "12345678901",
            "team_id": 6
        }
        """
        # Dados de entrada - COM CPF
        opportunity_data = OpportunityCreateUnified(
            name="Oportunidade Pessoa Física",
            company_name="João Silva",
            company_cnpj="12345678901",  # CPF com 11 dígitos
            team_id=6
        )
        
        # Mocks
        mock_odoo_client = AsyncMock()
        mock_odoo_client.create.return_value = 55555
        mock_odoo_client.search_read.return_value = [{
            'name': 'Oportunidade Pessoa Física',
            'partner_id': [777, 'João Silva'],
            'user_id': [3, 'Vendedor Padrão'],
            'team_id': [6, 'Equipe Vendas'],
            'stage_id': [1, 'Novo'],
            'expected_revenue': 0.0
        }]
        
        # Execução
        with patch('app.services.crm_service.get_odoo_client', return_value=mock_odoo_client), \
             patch('app.services.crm_service.get_or_create_partner_by_vat', return_value=777) as mock_partner:
            
            resultado = await create_opportunity_unified(opportunity_data)
        
        # Verificações
        assert resultado.opportunity_id == 55555
        assert resultado.partner_id == 777
        assert resultado.team_id == 6
        
        # Verifica se CPF foi processado corretamente
        mock_partner.assert_called_once_with(
            vat_number="12345678901",  # CPF limpo
            company_name="João Silva"
        )
        
        print("✅ EXEMPLO 3 PASSOU: Oportunidade criada com CPF (11 dígitos)")


# Para executar os exemplos:
# uv run pytest tests/test_create_opportunity_examples.py -v -s