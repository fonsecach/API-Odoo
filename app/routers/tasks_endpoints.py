import base64
import logging
from http import HTTPStatus

from fastapi import (
    APIRouter,
    # BackgroundTasks,
    # File,
    HTTPException,
    # Request,
    # UploadFile,
)

# from app.schemas.schemas import (
#     # TarefaCreate,
#     # TarefaUpdate,
#     # TaskMessageTransfer,
#     # TaskSaleOrderUpdate,
#     # TaskStageUpdate,
# )
from app.services.tasks_project_service import (
    get_tasks_by_client_vat_in_projects,
)
from app.utils.utils import clean_vat

# Configuração de logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/projects', tags=['Projetos'])


# @router.get('/', summary='Lista tarefas cadastradas')
# async def list_tasks(limit: int = 100, offset: int = 0):
#     """
#     Endpoint para listar todas as tarefas cadastradas de forma assíncrona.

#     Args:
#         limit: Limite de registros a serem retornados
#         offset: Deslocamento para paginação

#     Returns:
#         Lista de tarefas encontradas

#     Raises:
#         HTTPException: Se nenhuma tarefa for encontrada ou houver um erro
#     """
#     # Busca as tarefas de forma assíncrona
#     tasks_info = await get_tasks_info(limit, offset)

#     if not tasks_info:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail='Nenhuma tarefa localizada',
#         )

#     return {'tasks': tasks_info}


# @router.get(
#     '/{project_id}/tasks/{task_id}',
#     summary='Busca tarefa por ID dentro de um projeto específico',
# )
# async def get_task_by_project_and_id_route(project_id: int, task_id: int):
#     """
#     Endpoint para buscar uma tarefa específica dentro de um projeto de forma assíncrona.

#     Args:
#         project_id: ID do projeto
#         task_id: ID da tarefa

#     Returns:
#         Detalhes da tarefa encontrada

#     Raises:
#         HTTPException: Se a tarefa não for encontrada ou houver um erro
#     """
#     task_info = await get_task_by_project_and_id(project_id, task_id)

#     if not task_info:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail='Tarefa não localizada no projeto especificado',
#         )

#     return {'task': task_info}


# @router.post('/', summary='Cria uma nova tarefa em um projeto')
# async def create_new_task(
#     tarefa: TarefaCreate, request: Request, background_tasks: BackgroundTasks
# ) -> dict:
#     """
#     Endpoint para criar uma nova tarefa em um projeto de forma assíncrona.

#     Args:
#         tarefa: Dados da tarefa a ser criada
#         request: Objeto de requisição para identificação do cliente
#         background_tasks: Gerenciador de tarefas em background do FastAPI

#     Returns:
#         Mensagem de sucesso e ID da tarefa criada

#     Raises:
#         HTTPException: Em caso de erro na criação
#     """
#     client_ip = request.client.host
#     logger.info(
#         f"Requisição para criar tarefa '{tarefa.name}' recebida de {client_ip}"
#     )

#     try:
#         # Validação adicional dos dados
#         if not tarefa.name or not tarefa.project_id:
#             raise HTTPException(
#                 status_code=HTTPStatus.BAD_REQUEST,
#                 detail='Nome da tarefa e ID do projeto são obrigatórios',
#             )

#         # Criar a tarefa passando diretamente o modelo Pydantic
#         task_id = await create_task(tarefa)

#         if not task_id:
#             raise HTTPException(
#                 status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#                 detail='Erro ao criar tarefa no Odoo',
#             )

#         logger.info(
#             f"Tarefa '{tarefa.name}' criada com sucesso, ID: {task_id}"
#         )

#         return {
#             'mensagem': 'Tarefa criada com sucesso!',
#             'tarefa_id': task_id,
#         }

#     except HTTPException:
#         # Repassamos exceções HTTP já formatadas
#         raise
#     except Exception as e:
#         logger.error(
#             f'Erro não tratado ao criar tarefa: {str(e)}', exc_info=True
#         )
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail=f'Erro ao criar tarefa: {str(e)}',
#         )


# @router.patch(
#     '/{project_id}/tasks/{task_id}',
#     summary='Atualiza campos específicos de uma tarefa',
#     response_description='Campos atualizados com sucesso',
# )
# async def update_task_fields_route(
#     project_id: int,
#     task_id: int,
#     tarefa_update: TarefaUpdate,
# ):
#     """
#     Endpoint para atualizar campos específicos de uma tarefa de forma assíncrona.

#     Args:
#         project_id: ID do projeto
#         task_id: ID da tarefa
#         tarefa_update: Dados para atualização

#     Returns:
#         Confirmação da atualização com os campos modificados

#     Raises:
#         HTTPException: Se a tarefa não for encontrada ou houver erro na atualização
#     """
#     # Verifica se a tarefa existe no projeto
#     task_info = await get_task_by_project_and_id(project_id, task_id)

#     if not task_info:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail='Tarefa não encontrada no projeto especificado',
#         )

#     # Atualiza os campos no Odoo
#     success = await update_task_fields(task_id, tarefa_update)

#     if not success:
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail='Falha ao atualizar a tarefa',
#         )

#     return {
#         'message': 'Campos atualizados com sucesso',
#         'updated_fields': {
#             'partner_id': tarefa_update.partner_id,
#             'x_studio_tese_2': tarefa_update.x_studio_tese_2,
#             'x_studio_segmento': tarefa_update.x_studio_segmento,
#         },
#     }


# @router.patch(
#     '/tasks/link-order',
#     summary='Vincula um pedido de venda a uma tarefa de projeto',
#     response_description='Tarefa atualizada com o pedido de venda',
# )
# async def link_task_to_sales_order(update_data: TaskSaleOrderUpdate):
#     """
#     Endpoint para vincular um pedido de venda a uma tarefa de forma assíncrona.

#     Args:
#         update_data: Dados contendo os IDs da tarefa e do pedido de venda

#     Returns:
#         Confirmação do vínculo criado

#     Raises:
#         HTTPException: Se a tarefa ou o pedido não forem encontrados ou houver erro
#     """
#     # Verifica se a tarefa existe
#     task_info = await get_task_by_id(update_data.task_id)

#     if not task_info:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail=f'Tarefa com ID {update_data.task_id} não encontrada',
#         )

#     # Atualiza a tarefa com o ID do pedido de venda
#     success = await update_task_sale_order(
#         update_data.task_id,
#         update_data.sale_order_id,
#     )

#     if not success:
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail='Falha ao atualizar tarefa com ID do pedido de venda',
#         )

#     return {
#         'message': 'Tarefa vinculada ao pedido de venda com sucesso',
#         'task_id': update_data.task_id,
#         'sale_order_id': update_data.sale_order_id,
#     }


# @router.post(
#     '/{project_id}/tasks/{task_id}/attachment',
#     summary='Adiciona um arquivo anexo à tarefa',
#     response_description='Arquivo anexado com sucesso',
# )
# async def add_task_attachment_route(
#     project_id: int,
#     task_id: int,
#     file: UploadFile = File(...),
# ):
#     """
#     Endpoint para adicionar um anexo a uma tarefa no Odoo de forma assíncrona.

#     Args:
#         project_id: ID do projeto
#         task_id: ID da tarefa
#         file: Arquivo a ser anexado

#     Returns:
#         Confirmação do anexo criado

#     Raises:
#         HTTPException: Se a tarefa não for encontrada ou houver erro ao anexar
#     """
#     # Verificar se a tarefa existe no projeto
#     task_info = await get_task_by_project_and_id(project_id, task_id)

#     if not task_info:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail='Tarefa não encontrada no projeto especificado',
#         )

#     try:
#         # Ler e codificar o arquivo em base64
#         file_content = await file.read()
#         encoded_content = base64.b64encode(file_content).decode('utf-8')

#         # Criar anexo no Odoo
#         attachment_id = await create_task_attachment(
#             task_id, file.filename, encoded_content
#         )

#         if not attachment_id:
#             raise HTTPException(
#                 status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#                 detail='Falha ao anexar arquivo à tarefa',
#             )

#         return {
#             'message': 'Arquivo anexado com sucesso',
#             'attachment_id': attachment_id,
#             'filename': file.filename,
#         }

#     except Exception as e:
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail=f'Erro ao anexar arquivo: {str(e)}',
#         )


# @router.get(
#     '/{project_id}/tasks/stage/{stage_name}',
#     summary='Busca tarefas por nome do estágio dentro de um projeto',
#     response_description='Lista de tarefas no estágio especificado',
# )
# async def get_tasks_by_stage_name_route(
#     project_id: int, stage_name: str, limit: int = 100, offset: int = 0
# ):
#     """
#     Endpoint para buscar tarefas por nome do estágio dentro de um projeto específico de forma assíncrona.

#     Args:
#         project_id: ID do projeto
#         stage_name: Nome do estágio para filtrar
#         limit: Limite de registros a serem retornados
#         offset: Deslocamento para paginação

#     Returns:
#         Lista de tarefas que correspondem ao filtro

#     Raises:
#         HTTPException: Se nenhuma tarefa for encontrada ou houver erro
#     """
#     tasks_info = await get_tasks_by_stage_name(
#         project_id, stage_name, limit, offset
#     )

#     if not tasks_info:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail=f'Nenhuma tarefa encontrada no estágio "{stage_name}" para o projeto especificado',
#         )

#     return {
#         'project_id': project_id,
#         'stage_name': stage_name,
#         'tasks': tasks_info,
#         'count': len(tasks_info),
#     }


# @router.patch(
#     '/tasks/{task_id}/stage',
#     summary='Atualiza o estágio de uma tarefa',
#     response_description='Estágio da tarefa atualizado com sucesso',
# )
# async def update_task_stage_route(
#     task_id: int, task_stage_update: TaskStageUpdate
# ):
#     """
#     Endpoint para atualizar o estágio de uma tarefa específica de forma assíncrona.

#     Args:
#         task_id: ID da tarefa a ser atualizada
#         task_stage_update: Dados para atualização contendo o novo stage_id

#     Returns:
#         Confirmação da atualização

#     Raises:
#         HTTPException: Se a tarefa não for encontrada ou houver erro
#     """
#     # Verifica se a tarefa existe
#     task_info = await get_task_by_id(task_id)

#     if not task_info:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail=f'Tarefa com ID {task_id} não encontrada',
#         )

#     # Atualiza o estágio da tarefa
#     success = await update_task_stage(task_id, task_stage_update.stage_id)

#     if not success:
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail='Falha ao atualizar o estágio da tarefa',
#         )

#     stage_name = 'Novo estágio'  # Placeholder - na realidade seria buscado de forma assíncrona

#     return {
#         'message': 'Estágio da tarefa atualizado com sucesso',
#         'task_id': task_id,
#         'old_stage_id': task_info['stage_id'][0]
#         if isinstance(task_info['stage_id'], list)
#         else task_info['stage_id'],
#         'new_stage_id': task_stage_update.stage_id,
#         'new_stage_name': stage_name,
#     }


# @router.post(
#     '/tasks/transfer-messages',
#     summary='Transfere mensagens de uma tarefa para outra',
#     response_description='Mensagens transferidas com sucesso',
# )
# async def transfer_task_messages_route(transfer_data: TaskMessageTransfer):
#     """
#     Endpoint para transferir mensagens (message_ids) de uma tarefa para outra de forma assíncrona.

#     Args:
#         transfer_data: Dados contendo os IDs das tarefas de origem e destino

#     Returns:
#         Confirmação da transferência

#     Raises:
#         HTTPException: Se as tarefas não forem encontradas ou houver erro
#     """
#     # Verificar se a tarefa de origem existe
#     source_task = await get_task_by_id(transfer_data.source_task_id)

#     if not source_task:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail=f'Tarefa de origem com ID {transfer_data.source_task_id} não encontrada',
#         )

#     # Verificar se a tarefa de destino existe
#     target_task = await get_task_by_id(transfer_data.target_task_id)

#     if not target_task:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail=f'Tarefa de destino com ID {transfer_data.target_task_id} não encontrada',
#         )

#     # Transferir as mensagens
#     success = await transfer_task_messages(
#         transfer_data.source_task_id, transfer_data.target_task_id
#     )

#     if not success:
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail='Falha ao transferir mensagens entre as tarefas',
#         )

#     return {
#         'message': 'Mensagens transferidas com sucesso',
#         'source_task_id': transfer_data.source_task_id,
#         'target_task_id': transfer_data.target_task_id,
#     }


@router.get(
    '/by-vat/{vat}',
    summary='Busca tarefas dos projetos 25 e 26 pelo CNPJ do cliente',
    response_description='Lista de tarefas encontradas para o CNPJ informado',
)
async def get_tasks_by_client_vat(vat: str):
    """
    Endpoint para buscar tarefas nos projetos 25 e 26 filtrando pelo CNPJ do cliente.

    Args:
        vat: CNPJ do cliente (será limpo automaticamente)

    Returns:
        Lista de tarefas com informações detalhadas

    Raises:
        HTTPException: Se o CNPJ for inválido ou nenhuma tarefa for encontrada
    """
    try:
        cleaned_vat = clean_vat(vat)
    except ValueError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))

    # Buscar tarefas usando o serviço
    tasks = await get_tasks_by_client_vat_in_projects(cleaned_vat, [25, 26])

    if not tasks:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Nenhuma tarefa encontrada nos projetos 25 e 26 para o CNPJ {vat}',
        )

    formatted_tasks = []
    for task in tasks:
        formatted_task = {
            'id': task['id'],
            'name': task['name'],
            'partner_name': task.get('partner_id')
            and task['partner_id'][1]
            or 'Sem cliente',
            'stage_name': task.get('stage_id')
            and task['stage_id'][1]
            or 'Sem estágio',
            'project_name': task.get('project_id')
            and task['project_id'][1]
            or 'Sem projeto',
            'x_studio_numero_do_perdcomp': task.get(
                'x_studio_numero_do_perdcomp'
            )
            or '',
            'date_last_stage_update': task.get('date_last_stage_update') or '',
            'write_date': task.get('write_date') or '',
        }
        formatted_tasks.append(formatted_task)

    return {
        'vat': vat,
        'projects_searched': [25, 26],
        'total_tasks': len(formatted_tasks),
        'tasks': formatted_tasks,
    }
