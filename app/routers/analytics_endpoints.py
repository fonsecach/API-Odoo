"""
Endpoints para funcionalidades de análise de vendas.

Este módulo fornece endpoints para obtenção de métricas
de desempenho de vendas por equipe, vendedor e produto.
"""

from http import HTTPStatus
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.schemas.schemas import DateRangeParams, SalesAnalyticsResponse
from app.services.authentication import authenticate_odoo, connect_to_odoo
from app.services.sales_analytics_service import get_sales_analytics

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/analytics', tags=['Analytics'])


def validate_date_params(
    start_date: str = Query(..., description="Data inicial no formato dd-mm-aaaa"),
    end_date: str = Query(..., description="Data final no formato dd-mm-aaaa"),
    use_sample_data: bool = Query(False, description="Usar dados de exemplo quando não há dados reais")
) -> tuple:
    """
    Valida os parâmetros de data usando o modelo Pydantic.
    
    Args:
        start_date: Data inicial no formato dd-mm-aaaa
        end_date: Data final no formato dd-mm-aaaa
        use_sample_data: Flag para usar dados de exemplo quando não há dados reais
        
    Returns:
        Objeto DateRangeParams validado e flag de dados de exemplo
    
    Raises:
        HTTPException: Se as datas forem inválidas
    """
    try:
        return DateRangeParams(start_date=start_date, end_date=end_date), use_sample_data
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    '/sales',
    summary='Relatório de análise de vendas ganhas',
    description='Obtém métricas de vendas ganhas por equipe, vendedor e produto em um período específico',
    response_model=SalesAnalyticsResponse
)
async def sales_analytics(params_tuple: tuple = Depends(validate_date_params)):
    """
    Endpoint para obter análise de vendas no período especificado.
    
    Args:
        params_tuple: Tupla contendo parâmetros de data validados e flag de uso de dados de exemplo
        
    Returns:
        Dicionário com métricas de vendas
        
    Raises:
        HTTPException: Em caso de falha na autenticação ou erro interno
    """
    date_params, use_sample_data = params_tuple
    
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo'
        )
    
    try:
        logger.info(f"Iniciando análise para o período: {date_params.start_date} até {date_params.end_date}")
        
        analytics_data = get_sales_analytics(
            models, 
            ODOO_DB, 
            uid, 
            ODOO_PASSWORD,
            date_params.start_date,
            date_params.end_date,
            use_sample_data
        )
        
        # Garantir que o campo 'opportunities' existe na resposta
        if 'opportunities' not in analytics_data:
            analytics_data['opportunities'] = []
            logger.warning("Campo 'opportunities' não encontrado na resposta. Adicionando lista vazia.")
        
        logger.info(f"Análise concluída: {len(analytics_data.get('teams', []))} equipes, "
                   f"{len(analytics_data.get('users', []))} usuários, "
                   f"{len(analytics_data.get('products', []))} produtos, "
                   f"{len(analytics_data.get('opportunities', []))} oportunidades")
        
        return analytics_data
    
    except Exception as e:
        logger.error(f'Erro ao gerar análise de vendas: {str(e)}', exc_info=True)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Erro ao gerar análise de vendas: {str(e)}'
        )
        
