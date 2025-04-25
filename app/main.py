from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

from app.routers.analytics_endpoints import router as analytics_router
from app.routers.company_endpoints import router as company_router
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

app = FastAPI(
    title='API Odoo',
    description='API para integração com o ERP do Odoo',
    version='0.1.0',
)

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


@app.on_event("startup")
async def startup_event():
    """
    Inicialização de recursos quando a aplicação é iniciada.
    Pode ser usado para pré-aquecer conexões, inicializar cache, etc.
    """
    # Se quiser pré-aquecer conexões ou fazer inicializações assíncronas
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """
    Limpeza de recursos quando a aplicação é encerrada.
    Importante para fechar conexões e liberar recursos.
    """
    # Fechar todas as instâncias do cliente Odoo assíncrono para liberar recursos
    for client in AsyncOdooClient._instances.values():
        client.close()

@app.get('/')
async def root():
    return {'message': 'API Odoo está ativa e funcionando'}


@app.get('/scalar', include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )
