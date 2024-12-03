from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

from app.routers.company_endpoints import router as company_router
from app.routers.crm_endpoints import router as crm_router
from app.routers.helpdesk_endpoints import router as helpdesk_router
from app.routers.tasks_endpoints import router as tasks_router

app = FastAPI()

app.include_router(company_router)
app.include_router(crm_router)
app.include_router(tasks_router)
app.include_router(helpdesk_router)


@app.get('/')
async def root():
    return {'message': 'API Odoo está ativa e funcionando'}


@app.get('/scalar', include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )
