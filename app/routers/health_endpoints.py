from http import HTTPStatus

from fastapi import APIRouter

from app.schemas.schemas import HealthCheck as HealthCheckSchema
from app.schemas.schemas import PingResponse
from app.Services.health_service import HealthCheck

router = APIRouter(prefix='/health', tags=['Healthcheck'])
health_check_service = HealthCheck()


@router.get(
    '/',
    summary='Health check',
    response_model=HealthCheckSchema,
    status_code=HTTPStatus.OK,
)
async def health_check_route():
    return health_check_service.get_health_check()


@router.get(
    '/ping',
    summary='Ping',
    response_model=PingResponse,
    status_code=HTTPStatus.OK,
)
async def ping_route():
    return health_check_service.get_ping_status()
