import base64
from http import HTTPStatus

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.schemas.schemas import TarefaCreate, TarefaUpdate
from app.Services.authentication import authenticate_odoo, connect_to_odoo
from app.Services.tasks_project_service import (
    get_task_by_project_and_id,
    get_tasks_info,
)

router = APIRouter(prefix='/projects', tags=['Projetos'])


@router.get('/', summary='Lista tarefas cadastradas')
async def list_tasks(limit: int = 100, offset: int = 0):
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
async def criar_tarefa(tarefa: TarefaCreate) -> dict:
    try:
        common, models = connect_to_odoo(ODOO_URL)
        uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

        if not uid:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Falha na autenticação no Odoo',
            )

        # Cria a tarefa no Odoo
        tarefa_id = models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            'project.task',
            'create',
            [
                {
                    'name': tarefa.name,
                    'project_id': tarefa.project_id,
                    'stage_id': tarefa.stage_id,
                    'x_studio_tese_2': tarefa.x_studio_tese_2,
                    'x_studio_segmento': tarefa.x_studio_segmento,
                }
            ],
        )

        return {
            'mensagem': 'Tarefa criada com sucesso!',
            'tarefa_id': tarefa_id,
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
async def update_task_fields(
    project_id: int,
    task_id: int,
    tarefa_update: TarefaUpdate,
):
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
    try:
        models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            'project.task',
            'write',
            [
                [task_id],
                {  # Lista de IDs e campos para atualizar
                    'partner_id': tarefa_update.partner_id,
                    'x_studio_tese_2': tarefa_update.x_studio_tese_2,
                    'x_studio_segmento': tarefa_update.x_studio_segmento,
                },
            ],
        )
        return {
            'message': 'Campos atualizados com sucesso',
            'updated_fields': {
                'partner_id': tarefa_update.partner_id,
                'x_studio_tese_2': tarefa_update.x_studio_tese_2,
                'x_studio_segmento': tarefa_update.x_studio_segmento,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Falha ao atualizar a tarefa: {str(e)}',
        )


@router.post(
    "/{project_id}/tasks/{task_id}/attachment",
    summary="Adiciona um arquivo anexo à tarefa",
    response_description="Arquivo anexado com sucesso",
)
async def add_task_attachment(
    project_id: int,
    task_id: int,
    file: UploadFile = File(...),
):
    """
    Adiciona um anexo a uma tarefa no Odoo.
    """
    # Conectar ao Odoo
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Falha na autenticação no Odoo",
        )

    # Verificar se a tarefa existe no projeto
    task_info = get_task_by_project_and_id(models, ODOO_DB, uid, ODOO_PASSWORD, project_id, task_id)
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
        attachment_data = {
            "name": file.filename,
            "datas": encoded_content,
            "res_model": "project.task",
            "res_id": task_id,
        }

        attachment_id = models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            "ir.attachment",
            "create",
            [attachment_data],
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
