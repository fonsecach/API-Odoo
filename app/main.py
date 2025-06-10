# app/main.py

import logging
import os
from contextlib import asynccontextmanager

# Removido: from sched import scheduler
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from app.routers.analytics_endpoints import router as analytics_router
from app.routers.company_endpoints import router as company_router
from app.routers.cron_jobs_endpoints import router as cron_jobs_router
from app.routers.crm_endpoints import router as crm_router
from app.routers.custom_fields_endpoints import router as custom_fields_router
from app.routers.fields_inspection_endpoints import (
    router as fields_inspection_router,
)
from app.routers.health_endpoints import router as health_router
from app.routers.helpdesk_endpoints import router as helpdesk_router
from app.routers.migracao_endpoints import router as migracao_router
from app.routers.sales_orders_endpoints import router as sales_orders_router
from app.routers.tasks_endpoints import router as tasks_router
from app.services.async_odoo_client import AsyncOdooClient
from app.services.stale_opportunities_service import check_and_report_stale_opportunities

is_production = os.getenv('ENVIRONMENT', 'development').lower() == 'production'

# CORREÇÃO: Instanciando o agendador corretamente
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: inicialização de recursos
    logger = logging.getLogger("uvicorn.info")
    logger.info("Iniciando agendador de tarefas...")
    
    # Adiciona a tarefa ao agendador
    scheduler.add_job(
        check_and_report_stale_opportunities,
        'cron',
        day_of_week='mon-fri',
        hour=8, # Ajuste o horário conforme necessário
        minute=15,
        timezone=pytz.timezone('America/Sao_Paulo'),
        id="report_stale_opportunities_job",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Agendador iniciado com sucesso.")
    
    yield
    
    # Shutdown: liberar recursos
    logger.info("Desligando agendador...")
    scheduler.shutdown()
    logger.info("Agendador desligado.")
    
    for client in AsyncOdooClient._instances.values():
        client.close()


# CORREÇÃO: Passando a função 'lifespan' para o FastAPI
app = FastAPI(
    lifespan=lifespan,
    title='API Odoo',
    description='API para integração com o ERP do Odoo',
    version='0.1.0',
    docs_url=None if is_production else '/docs',
    openapi_url=None if is_production else '/openapi.json',
)

# Configure CORS middleware
origins = os.getenv('CORS_ORIGINS', '*').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Inclusão dos routers
app.include_router(company_router)
app.include_router(crm_router)
app.include_router(tasks_router)
app.include_router(helpdesk_router)
app.include_router(sales_orders_router)
app.include_router(health_router)
app.include_router(migracao_router)
app.include_router(fields_inspection_router)
app.include_router(analytics_router)
app.include_router(custom_fields_router)
app.include_router(cron_jobs_router)


@app.get('/')
async def root():
    return {'message': 'API Odoo está ativa e funcionando'}


@app.get('/scalar', include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )