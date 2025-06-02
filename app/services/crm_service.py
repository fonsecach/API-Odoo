# Conteúdo para app/services/crm_service.py

import logging
from http import HTTPStatus
from typing import Optional, Dict, Any

from fastapi import HTTPException

# Importa a classe AsyncOdooClient
from app.services.async_odoo_client import AsyncOdooClient 
# Importa as configurações de conexão do Odoo
from app.config.settings import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD 

from app.schemas.schemas import OpportunityCreateIntelligent, OpportunityReturn
from app.services.company_service import get_or_create_partner_by_vat

logger = logging.getLogger(__name__) # Mantenha apenas uma atribuição para o logger

# Definição da função get_odoo_client que estava faltando neste arquivo
async def get_odoo_client() -> AsyncOdooClient:
    """
    Obtém uma instância do cliente Odoo assíncrono.
    Reutiliza conexões existentes quando possível.
    """
    return await AsyncOdooClient.get_instance(
        ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
    )

# --- Funções síncronas existentes ---
def get_opportunities_info(models, db, uid, password, limit=100, offset=0):
    try:
        opportunities_info = models.execute_kw(
            db,
            uid,
            password,
            'crm.lead',
            'search_read',
            [[]],
            {'limit': limit, 'offset': offset},
        )
        return opportunities_info
    except Exception as e:
        # Para consistência e melhor depuração, considere usar logger.error aqui também
        print(f'Erro ao buscar e ler informações das oportunidades: {e}')
        return []


def fetch_opportunity_by_id(models, db, uid, password, opportunity_id):
    try:
        opportunities_info = models.execute_kw(
            db, uid, password, 'crm.lead', 'read', [opportunity_id]
        )
        return opportunities_info
    except Exception as e:
        print(f'Erro ao buscar e ler informações da oportunidade: {e}')
        return []


def create_opportunity_in_crm(opportunity_info, models, db, uid, password):
    try:
        return models.execute_kw(
            db, uid, password, 'crm.lead', 'create', [opportunity_info]
        )
    except Exception as e:
        # Considere loggar o erro antes de levantar a HTTPException
        logger.error(f"Erro ao criar oportunidade síncrona: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Erro ao criar oportunidade: {str(e)}',
        )

# --- Função assíncrona para criação inteligente ---
async def create_opportunity_intelligent_async(
    opportunity_payload: OpportunityCreateIntelligent
) -> Optional[Dict[str, Any]]:
    """
    Cria uma oportunidade de forma inteligente:
    1. Verifica/Cria a empresa associada pelo CNPJ.
    2. Cria a oportunidade no Odoo associada a essa empresa.
    Args:
        opportunity_payload: Dados da oportunidade e da empresa.
    Returns:
        Um dicionário com os detalhes da oportunidade criada, ou levanta HTTPException em caso de erro.
    Raises:
        HTTPException: Em caso de erros específicos (ex: falha ao obter/criar parceiro, erro no Odoo).
    """
    # Agora esta chamada funcionará, pois get_odoo_client() está definido acima neste arquivo.
    odoo_async_client = await get_odoo_client() 

    # Passo 1: Obter ou criar o parceiro (empresa)
    try:
        partner_id = await get_or_create_partner_by_vat(
            vat_number=opportunity_payload.company_vat,
            company_name=opportunity_payload.company_name
        )
    except ValueError as ve: # Erro de validação do VAT (ex: CNPJ inválido)
        logger.error(f"ValueError ao obter/criar parceiro para VAT {opportunity_payload.company_vat}: {str(ve)}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(ve))
    except Exception as e_partner: # Outros erros ao obter/criar parceiro
        logger.exception(f"Erro inesperado ao obter/criar parceiro para VAT {opportunity_payload.company_vat}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar dados da empresa: {str(e_partner)}"
        )


    if not partner_id: # Se get_or_create_partner_by_vat retornar None (apesar de agora levantar exceção)
        logger.error(f"Não foi possível obter ou criar o parceiro (ID nulo retornado) para VAT {opportunity_payload.company_vat} e nome {opportunity_payload.company_name}.")
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, # Ou 500 se for uma falha inesperada do serviço de empresa
            detail=f"Falha ao processar dados da empresa para VAT: {opportunity_payload.company_vat}"
        )

    # Passo 2: Preparar dados da oportunidade para o Odoo
    opportunity_data_odoo = {
        'name': opportunity_payload.name,
        'partner_id': partner_id,
        'user_id': opportunity_payload.user_id,
        'team_id': opportunity_payload.team_id, # Se opcional e None, será removido abaixo
        'stage_id': opportunity_payload.stage_id, # Se opcional e None, será removido abaixo
        'type': 'opportunity',
        # Odoo pode interpretar False como "não definido" ou um valor booleano literal.
        # Se o campo x_studio_tese for um campo de texto, enviar False pode não ser o ideal.
        # Enviar o valor original ou omitir se None.
        'x_studio_tese': opportunity_payload.x_studio_tese,
        'expected_revenue': opportunity_payload.expected_revenue,
    }
    # Remove chaves com valor None para que Odoo use seus padrões, se houver.
    opportunity_data_odoo = {k: v for k, v in opportunity_data_odoo.items() if v is not None}


    # Passo 3: Criar a oportunidade no CRM usando AsyncOdooClient
    try:
        opportunity_id = await odoo_async_client.create('crm.lead', opportunity_data_odoo)
        
        if not opportunity_id: # Checagem caso o Odoo retorne algo falsy sem erro
            logger.error(f"Falha ao criar oportunidade '{opportunity_payload.name}' no Odoo (nenhum ID retornado).")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="O Odoo não retornou um ID para a oportunidade criada."
            )
        
        logger.info(f"Oportunidade '{opportunity_payload.name}' criada com sucesso, ID: {opportunity_id}.")

        # Passo 4: Ler os dados da oportunidade criada para retornar
        fields_to_read = ['name', 'partner_id', 'x_studio_tese', 'user_id', 'team_id', 'stage_id', 'expected_revenue']
        created_opportunity_data_list = await odoo_async_client.search_read(
            'crm.lead',
            [['id', '=', opportunity_id]],
            fields=fields_to_read
        )

        if not created_opportunity_data_list:
            logger.error(f"Oportunidade ID {opportunity_id} criada, mas falha ao reler os dados.")
            # É crítico não conseguir reler, pode indicar um problema.
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Falha ao obter detalhes da oportunidade recém-criada."
            )

        details = created_opportunity_data_list[0]
        
        # Função auxiliar para extrair ID de campos relacionais [ID, "Nome"] ou retornar o valor se já for ID
        def get_id_from_relational(field_value, fallback_id=None):
            if isinstance(field_value, list) and field_value:
                return field_value[0]
            # Se o Odoo não retornar o campo (ex: se era opcional e não foi setado),
            # podemos usar o fallback_id que veio do payload original (se aplicável e desejado)
            # ou deixar como None se o schema de retorno permitir.
            return fallback_id if field_value is False or field_value is None else field_value


        return_data = {
            "opportunity_id": opportunity_id,
            "name": details.get('name'),
            "partner_id": get_id_from_relational(details.get('partner_id'), partner_id), # partner_id é o ID que já temos
            "x_studio_tese": details.get('x_studio_tese') if details.get('x_studio_tese') is not False else None,
            "user_id": get_id_from_relational(details.get('user_id'), opportunity_payload.user_id),
            "team_id": get_id_from_relational(details.get('team_id'), opportunity_payload.team_id),
            "stage_id": get_id_from_relational(details.get('stage_id'), opportunity_payload.stage_id),
            "expected_revenue": details.get('expected_revenue'),
        }
        return return_data

    except HTTPException: # Re-levanta HTTPExceptions já tratadas (ex: de get_or_create_partner_by_vat)
        raise
    except Exception as e: # Captura outras exceções da interação com Odoo (create, search_read)
        logger.exception(f"Exceção ao interagir com Odoo para oportunidade '{opportunity_payload.name}'")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao interagir com o Odoo para criar/ler oportunidade: {str(e)}"
        )
        