import logging
from http import HTTPStatus

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.schemas.schemas import (
    CompanyDefault,
    CompanyReturn,
    ContactUpdate,
    Message,
)
from app.services.company_service import (
    create_company,
    delete_company,
    fetch_client_by_name,
    get_clients_info,
    get_company_by_id,
    get_company_by_vat,
    update_company,
    update_contact_fields,
)
from app.utils.utils import clean_vat

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/company', tags=['company'])


@router.get('/', summary='Lista empresas cadastradas')
async def list_companies(limit: int = 100, offset=0):
    """
    Endpoint para listar todas as empresas cadastradas de forma assíncrona.

    Args:
        limit: Limite de registros a serem retornados
        offset: Deslocamento para paginação

    Returns:
        Lista de empresas encontradas

    Raises:
        HTTPException: Se nenhuma empresa for encontrada ou houver um erro
    """
    companies_info = await get_clients_info(limit, offset)

    if not companies_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma empresa localizada',
        )

    return {
        'companies': companies_info,
    }


@router.get('/vat', summary='Lista empresa por CNPJ')
async def list_companies_by_vat(vat: str):
    """
    Endpoint para buscar uma empresa pelo VAT (CNPJ) de forma assíncrona.

    Args:
        vat: Número do VAT (CNPJ)

    Returns:
        Empresa correspondente ao VAT

    Raises:
        HTTPException: Se a empresa não for encontrada ou houver um erro
    """
    try:
        vat = clean_vat(vat)
    except ValueError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))

    companies_info = await get_company_by_vat(vat)

    if not companies_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma empresa localizada',
        )

    return {
        'companies': companies_info,
    }


@router.get('/name', summary='Retorna clientes pelo nome da empresa')
async def get_clients_by_name(name: str, limit: int = 100, offset: int = 0):
    """
    Endpoint para buscar clientes pelo nome (ou parte do nome) da empresa de forma assíncrona.

    Args:
        name: Nome ou parte do nome da empresa
        limit: Limite de registros a serem retornados
        offset: Deslocamento para paginação

    Returns:
        Lista de clientes correspondentes ao nome

    Raises:
        HTTPException: Se nenhum cliente for encontrado ou houver um erro
    """
    companies_info = await fetch_client_by_name(
        name, limit=limit, offset=offset
    )

    if not companies_info:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Nenhuma empresa localizada com nome contendo "{name}"',
        )

    return {
        'clients': companies_info,
        'count': len(companies_info),
        'search_term': name,
    }


@router.get('/id', summary='Lista empresas cadastradas pelo ID')
async def list_companies_by_id(id: int):
    """
    Endpoint para buscar uma empresa pelo ID de forma assíncrona.

    Args:
        id: ID da empresa

    Returns:
        Empresa correspondente ao ID

    Raises:
        HTTPException: Se a empresa não for encontrada ou houver um erro
    """
    companies_info = await get_company_by_id(id)

    if not companies_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma empresa localizada',
        )

    return {
        'companies': companies_info,
    }


from fastapi import status


@router.post(
    '/',
    summary='Cadastrar uma empresa',
    status_code=status.HTTP_201_CREATED,
    response_model=CompanyReturn,
)
async def create_company_route(
    company_info: CompanyDefault,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Endpoint para criar uma nova empresa no Odoo de forma assíncrona.

    Args:
        company_info: Dados da empresa a ser criada
        request: Objeto de requisição para identificação do cliente
        background_tasks: Gerenciador de tarefas em background do FastAPI

    Returns:
        Dados da empresa criada

    Raises:
        HTTPException: Se houver um erro na criação
    """
    client_ip = request.client.host
    logger.info(
        f"Requisição para criar empresa '{company_info.name}' recebida de {client_ip}"
    )

    # Limpar e validar VAT
    try:
        company_info.vat = clean_vat(company_info.vat)
    except ValueError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))

    # Verificar se já existe uma empresa com o mesmo VAT
    existing_companies = await get_company_by_vat(company_info.vat)

    if existing_companies:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f'Empresa com VAT {company_info.vat} já está cadastrada',
        )

    # Criar a empresa
    company_id = await create_company(company_info)

    if not company_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail='Nenhuma empresa criada'
        )

    logger.info(
        f"Empresa '{company_info.name}' criada com sucesso, ID: {company_id}"
    )

    return {
        'company_id': company_id,
        'name': company_info.name,
        'vat': company_info.vat,
        'country_id': company_info.country_id,
        'phone': company_info.phone,
        'email': company_info.email,
    }


@router.put(
    '/{id}',
    summary='Atualizar uma empresa',
    status_code=HTTPStatus.OK,
)
async def update_company_route(company_id: int, company_info: CompanyDefault):
    """
    Endpoint para atualizar uma empresa existente de forma assíncrona.

    Args:
        company_id: ID da empresa a ser atualizada
        company_info: Dados atualizados da empresa

    Returns:
        Confirmação da atualização

    Raises:
        HTTPException: Se a empresa não for encontrada ou houver um erro na atualização
    """
    # Verificar se a empresa existe
    company = await get_company_by_id(company_id)

    if not company:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Empresa com ID {company_id} não encontrada',
        )

    # Atualizar a empresa
    success = await update_company(company_id, company_info)

    if not success:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma empresa atualizada',
        )

    logger.info(f'Empresa ID {company_id} atualizada com sucesso')

    return {'company_id': company_id}


@router.delete(
    '/',
    summary='Excluir uma empresa',
    status_code=status.HTTP_200_OK,
    response_model=Message,
)
async def delete_company_route(company_id: int):
    """
    Endpoint para excluir uma empresa de forma assíncrona.

    Args:
        company_id: ID da empresa a ser excluída

    Returns:
        Mensagem de confirmação

    Raises:
        HTTPException: Se a empresa não for encontrada ou houver um erro na exclusão
    """
    # Verificar se a empresa existe
    company = await get_company_by_id(company_id)

    if not company:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Empresa com ID {company_id} não encontrada',
        )

    # Excluir a empresa
    success = await delete_company(company_id)

    if not success:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma empresa excluída',
        )

    logger.info(f'Empresa ID {company_id} excluída com sucesso')

    return {'message': 'User deleted'}


@router.patch(
    '/{id}',
    summary='Atualizar dados do cliente',
    response_description='Cliente atualizado com sucesso!',
)
async def update_client_fields_route(id: int, contact_update: ContactUpdate):
    """
    Endpoint para atualizar campos específicos de um cliente de forma assíncrona.

    Args:
        id: ID do cliente a ser atualizado
        contact_update: Dados para atualização

    Returns:
        Confirmação da atualização

    Raises:
        HTTPException: Se o cliente não for encontrado ou houver um erro na atualização
    """
    logger.info(f'Recebida requisição para atualizar cliente ID {id}')

    # Verificar se o cliente existe
    contact_info = await get_company_by_id(id)

    if not contact_info:
        logger.warning(f'Cliente ID {id} não encontrado no Odoo')
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Cliente não encontrado no Odoo',
        )

    # Preparar dados para atualização
    update_data = {
        'x_studio_certificado': contact_update.x_studio_certificado or '',
        'x_studio_validade_da_procuracao': (
            contact_update.x_studio_validade_da_procuracao.strftime('%Y-%m-%d')
            if contact_update.x_studio_validade_da_procuracao
            else ''
        ),
    }

    logger.info(
        f'Tentando atualizar cliente ID {id} com os seguintes valores: {update_data}'
    )

    # Atualizar o cliente
    success = await update_contact_fields(id, contact_update)

    if not success:
        logger.error(f'Falha ao atualizar cliente ID {id}')
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Falha ao atualizar o cliente',
        )

    logger.info(f'Cliente ID {id} atualizado com sucesso')

    # Buscar cliente atualizado para log
    updated_contact = await get_company_by_id(id)
    logger.info(f'Dados após atualização: {updated_contact}')

    return {
        'message': 'Cliente atualizado com sucesso!',
        'updated_fields': update_data,
    }
