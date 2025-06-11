import logging

from fastapi import APIRouter, BackgroundTasks, status

from app.services.stale_opportunities_service import (
    check_and_report_stale_opportunities,
)

router = APIRouter(prefix='/cron', tags=['Tarefas Agendadas'])
logger = logging.getLogger(__name__)


@router.post(
    '/stale-opportunities-report',
    summary='Aciona o relatório de oportunidades estagnadas',
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_stale_opportunities_report(
    background_tasks: BackgroundTasks,
):
    """
    Aciona a tarefa em background para gerar e enviar o relatório
    de oportunidades estagnadas por mais de 72 horas.
    """
    logger.info('Endpoint de relatório de oportunidades estagnadas acionado.')
    background_tasks.add_task(check_and_report_stale_opportunities)
    return {
        'message': 'A geração do relatório de oportunidades estagnadas foi iniciada em background.'
    }
