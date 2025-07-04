import logging
from typing import List
import base64

from fastapi import APIRouter, HTTPException, status

from app.schemas.schemas import OpportunityPowerBIData, OpportunityCreateUnified, OpportunityReturn
from app.services.crm_service import (
    fetch_opportunities_for_powerbi, 
    fetch_opportunity_by_id_for_powerbi,
    create_opportunity_unified
)
from app.services.crm_service_optimized import (
    fetch_opportunities_for_powerbi_with_pt_names_optimized,
    fetch_opportunity_by_id_for_powerbi_with_pt_names_optimized
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/opportunities', tags=['Oportunidades'])


@router.get(
    '/powerbi',
    summary='Buscar dados de oportunidades para PowerBI (OTIMIZADO)',
    description='Endpoint especializado para fornecer dados das oportunidades CRM formatados para consumo pelo PowerBI com nomes em português. Versão otimizada para performance.',
    response_model=List[dict]
)
async def get_opportunities_powerbi_endpoint():
    """
    Retorna todas as oportunidades do CRM com todos os campos necessários para análise no PowerBI.
    Os campos são retornados com nomes em português e remove campos: probability, street, country_id.
    
    Returns:
        Lista completa de oportunidades com todos os campos de negócio formatados.
    """
    try:
        opportunities = await fetch_opportunities_for_powerbi_with_pt_names_optimized()
        
        if not opportunities:
            logger.info("Nenhuma oportunidade encontrada para PowerBI")
            return []
        
        logger.debug(f"Retornando {len(opportunities)} oportunidades para PowerBI (otimizado)")
        return opportunities
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado no endpoint PowerBI: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor ao buscar dados para PowerBI"
        )



@router.get(
    '/powerbi/{opportunity_id}',
    summary='Buscar uma oportunidade específica por ID para PowerBI (OTIMIZADO)',
    description='Endpoint otimizado para buscar uma oportunidade específica por ID formatada para PowerBI com nomes em português',
    response_model=dict,
)
async def get_opportunity_powerbi_by_id_endpoint(opportunity_id: int):
    """
    Retorna uma oportunidade específica do CRM formatada para PowerBI.
    Os campos são retornados com nomes em português. Versão otimizada para performance.
    
    Args:
        opportunity_id: ID da oportunidade para buscar.
    
    Returns:
        Dicionário da oportunidade especificada com nomes em português.
    
    Raises:
        HTTPException: 404 se a oportunidade não for encontrada.
    """
    try:
        opportunity = await fetch_opportunity_by_id_for_powerbi_with_pt_names_optimized(opportunity_id)
        logger.debug(f"Oportunidade ID {opportunity_id} retornada para PowerBI (otimizado)")
        return opportunity
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado no endpoint PowerBI para oportunidade {opportunity_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor ao buscar oportunidade {opportunity_id} para PowerBI"
        )


@router.post(
    "/create",
    summary="Criar nova oportunidade (Unificado)",
    description="Endpoint unificado para criação de oportunidades. Apenas 'name' é obrigatório. Criação automática de cliente por CPF/CNPJ opcional.",
    status_code=status.HTTP_201_CREATED,
    response_model=OpportunityReturn,
)
async def create_opportunity_unified_endpoint(opportunity_data: OpportunityCreateUnified):
    """
    Cria uma nova oportunidade com validação e criação automática de cliente.
    
    Funcionalidades:
    - Campo obrigatório: apenas 'name' (nome da oportunidade)
    - Campos opcionais: company_name, company_cnpj, team_id, expected_revenue
    - Valida CPF (11 dígitos) ou CNPJ (14 dígitos) se fornecido
    - Verifica se cliente existe, senão cria automaticamente (se company_cnpj fornecido)
    - Cria oportunidade com type='opportunity' sempre
    - Cria oportunidade com campos personalizados
    - Suporte a anexos em base64
    
    Args:
        opportunity_data: Dados da oportunidade (apenas 'name' obrigatório)
    
    Returns:
        Detalhes da oportunidade criada
    """
    try:
        result = await create_opportunity_unified(opportunity_data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao criar oportunidade: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )

