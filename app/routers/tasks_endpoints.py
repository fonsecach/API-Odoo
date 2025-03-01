import base64
from http import HTTPStatus

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.schemas.schemas import TarefaCreate, TarefaUpdate, TaskSaleOrderUpdate
from app.Services.authentication import authenticate_odoo, connect_to_odoo
from app.Services.sales_orders import get_sales_order_by_id
from app.Services.tasks_project_service import (
    create_task,
    create_task_attachment,
    get_task_by_id,
    get_task_by_project_and_id,
    get_tasks_info,
    update_task_fields,
    update_task_sale_order,
)

router = APIRouter(prefix='/projects', tags=['Projetos'])


@router.get('/', summary='Lista tarefas cadastradas')
async def list_tasks(limit: int = 100, offset: int = 0):

    # Endpoint para listar todas as tarefas cadastradas.
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    # Busca as tarefas
    tasks_info = get_tasks_info(
        models, ODOO_DB, uid, ODOO_PASSWORD, limit, offset
    )

    if not tasks_info:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Nenhuma tarefa localizada',
        )

    return {'tasks': tasks_info}


@router.get(
    '/{project_id}/tasks/{task_id}',
    summary='Busca tarefa por ID dentro de um projeto específico',
)
async def get_task_by_project_and_id_route(project_id: int, task_id: int):

    # Endpoint para buscar uma tarefa específica dentro de um projeto.
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    task_info = get_task_by_project_and_id(
        models, ODOO_DB, uid, ODOO_PASSWORD, project_id, task_id
    )

    if not task_info:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Tarefa não localizada no projeto especificado',
        )

    return {'task': task_info}


@router.post('/', summary='Cria uma nova tarefa em um projeto')
async def create_new_task(tarefa: TarefaCreate) -> dict:

    # Endpoint para criar uma nova tarefa em um projeto.
    try:
        common, models = connect_to_odoo(ODOO_URL)
        uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

        if not uid:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Falha na autenticação no Odoo',
            )

        # Cria a tarefa no Odoo
        task_data = {
            'name': tarefa.name,
            'project_id': tarefa.project_id,
            'stage_id': tarefa.stage_id,
            'x_studio_tese_2': tarefa.x_studio_tese_2,
            'x_studio_segmento': tarefa.x_studio_segmento,
        }

        task_id = create_task(
            models, ODOO_DB, uid, ODOO_PASSWORD, task_data
        )

        if not task_id:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail='Erro ao criar tarefa',
            )

        return {
            'mensagem': 'Tarefa criada com sucesso!',
            'tarefa_id': task_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Erro ao criar tarefa: {str(e)}',
        )


@router.patch(
    '/{project_id}/tasks/{task_id}',
    summary='Atualiza campos específicos de uma tarefa',
    response_description='Campos atualizados com sucesso',
)
async def update_task_fields_route(
    project_id: int,
    task_id: int,
    tarefa_update: TarefaUpdate,
):

    # Endpoint para atualizar campos específicos de uma tarefa.
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    # Verifica se a tarefa existe no projeto
    task_info = get_task_by_project_and_id(
        models, ODOO_DB, uid, ODOO_PASSWORD, project_id, task_id
    )

    if not task_info:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Tarefa não encontrada no projeto especificado',
        )

    # Atualiza os campos no Odoo
    fields_data = {
        'partner_id': tarefa_update.partner_id,
        'x_studio_tese_2': tarefa_update.x_studio_tese_2,
        'x_studio_segmento': tarefa_update.x_studio_segmento,
    }

    success = update_task_fields(
        models, ODOO_DB, uid, ODOO_PASSWORD, task_id, fields_data
    )

    if not success:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Falha ao atualizar a tarefa',
        )

    return {
        'message': 'Campos atualizados com sucesso',
        'updated_fields': {
            'partner_id': tarefa_update.partner_id,
            'x_studio_tese_2': tarefa_update.x_studio_tese_2,
            'x_studio_segmento': tarefa_update.x_studio_segmento,
        },
    }


@router.patch(
    '/tasks/link-order',
    summary='Vincula um pedido de venda a uma tarefa de projeto',
    response_description='Tarefa atualizada com o pedido de venda',
)
async def link_task_to_sales_order(update_data: TaskSaleOrderUpdate):

    # Endpoint para vincular um pedido de venda a uma tarefa.
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    # Verifica se a tarefa existe
    task_info = get_task_by_id(
        models, ODOO_DB, uid, ODOO_PASSWORD, update_data.task_id
    )

    if not task_info:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Tarefa com ID {update_data.task_id} não encontrada',
        )

    # Verifica se o pedido de venda existe
    sale_order = get_sales_order_by_id(
        models, ODOO_DB, uid, ODOO_PASSWORD, update_data.sale_order_id
    )

    if not sale_order:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'''Pedido de venda com ID {update_data.sale_order_id}
            não encontrado''',
        )

    # Atualiza a tarefa com o ID do pedido de venda
    success = update_task_sale_order(
        models,
        ODOO_DB,
        uid,
        ODOO_PASSWORD,
        update_data.task_id,
        update_data.sale_order_id,
    )

    if not success:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Falha ao atualizar tarefa com ID do pedido de venda',
        )

    return {
        'message': 'Tarefa vinculada ao pedido de venda com sucesso',
        'task_id': update_data.task_id,
        'sale_order_id': update_data.sale_order_id,
    }


@router.post(
    "/{project_id}/tasks/{task_id}/attachment",
    summary="Adiciona um arquivo anexo à tarefa",
    response_description="Arquivo anexado com sucesso",
)
async def add_task_attachment_route(
    project_id: int,
    task_id: int,
    file: UploadFile = File(...),
):

    # Endpoint para adicionar um anexo a uma tarefa no Odoo.
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Falha na autenticação no Odoo",
        )

    # Verificar se a tarefa existe no projeto
    task_info = get_task_by_project_and_id(
        models, ODOO_DB, uid, ODOO_PASSWORD, project_id, task_id
    )

    if not task_info:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Tarefa não encontrada no projeto especificado",
        )

    try:
        # Ler e codificar o arquivo em base64
        file_content = await file.read()
        encoded_content = base64.b64encode(file_content).decode("utf-8")

        # Criar anexo no Odoo
        attachment_id = create_task_attachment(
            models,
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            task_id,
            file.filename,
            encoded_content
        )

        if not attachment_id:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Falha ao anexar arquivo à tarefa",
            )

        return {
            "message": "Arquivo anexado com sucesso",
            "attachment_id": attachment_id,
            "filename": file.filename,
        }

    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao anexar arquivo: {str(e)}",
        )
