import logging
from typing import Any, Dict, List, Optional, Union

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.schemas.schemas import (
    TarefaCreate,
    TarefaUpdate,
    TaskSaleOrderUpdate,
    TaskStageUpdate,
)
from app.services.async_odoo_client import AsyncOdooClient

# Configurar logging
logger = logging.getLogger(__name__)

# Constantes
TASK_MODEL = 'project.task'
TASK_DEFAULT_FIELDS = ['id', 'name', 'project_id', 'stage_id', 'sale_order_id']


async def get_odoo_client() -> AsyncOdooClient:
    """
    Obtém uma instância do cliente Odoo assíncrono.
    Reutiliza conexões existentes quando possível.
    """
    return await AsyncOdooClient.get_instance(
        ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
    )


async def get_tasks_info(limit: int = 100, offset: int = 0,
                        fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Obtém informações de várias tarefas de forma assíncrona.
    
    Args:
        limit: Limite de registros a serem retornados
        offset: Deslocamento para paginação
        fields: Campos específicos a serem retornados (usa padrão se None)
        
    Returns:
        Lista de tarefas ou lista vazia em caso de erro
    """
    client = await get_odoo_client()

    if fields is None:
        fields = TASK_DEFAULT_FIELDS

    try:
        return await client.search_read(
            TASK_MODEL,
            [],
            fields=fields,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f'Erro ao buscar e ler informações das tarefas: {e}')
        return []


async def get_task_by_id(task_id: int, fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    Obtém uma tarefa pelo seu ID de forma assíncrona.
    
    Args:
        task_id: ID da tarefa
        fields: Campos específicos a serem retornados (usa padrão se None)
        
    Returns:
        Dados da tarefa ou None se não encontrada
    """
    client = await get_odoo_client()

    if fields is None:
        fields = TASK_DEFAULT_FIELDS

    try:
        tasks = await client.search_read(
            TASK_MODEL,
            [['id', '=', task_id]],
            fields=fields
        )
        return tasks[0] if tasks else None
    except Exception as e:
        logger.error(f'Erro ao recuperar tarefa por ID: {e}')
        return None


async def get_task_by_project_and_id(project_id: int, task_id: int,
                                   fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    Obtém uma tarefa específica de um projeto de forma assíncrona.
    
    Args:
        project_id: ID do projeto
        task_id: ID da tarefa
        fields: Campos específicos a serem retornados (usa padrão se None)
        
    Returns:
        Dados da tarefa ou None se não encontrada
    """
    client = await get_odoo_client()

    if fields is None:
        fields = TASK_DEFAULT_FIELDS

    try:
        tasks = await client.search_read(
            TASK_MODEL,
            [['id', '=', task_id], ['project_id', '=', project_id]],
            fields=fields
        )
        return tasks[0] if tasks else None
    except Exception as e:
        logger.error(f'Erro ao buscar informações da tarefa: {e}')
        return None


async def create_task(tarefa: Union[TarefaCreate, Dict[str, Any]]) -> Optional[int]:
    """
    Cria uma nova tarefa no Odoo de forma assíncrona.
    
    Args:
        tarefa: Dados da tarefa a ser criada (instância de TarefaCreate ou dict)
        
    Returns:
        ID da tarefa criada ou None em caso de erro
    """
    client = await get_odoo_client()

    try:
        # Converte para dicionário se for um modelo Pydantic
        if hasattr(tarefa, 'dict'):
            task_data = tarefa.dict(exclude_unset=True)
        else:
            task_data = dict(tarefa)

        return await client.create(TASK_MODEL, task_data)
    except Exception as e:
        logger.error(f'Erro ao criar tarefa: {e}')
        return None


async def update_task_fields(task_id: int, fields_data: Union[TarefaUpdate, Dict[str, Any]]) -> bool:
    """
    Atualiza campos específicos de uma tarefa de forma assíncrona.
    
    Args:
        task_id: ID da tarefa a ser atualizada
        fields_data: Dados a serem atualizados (instância de TarefaUpdate ou dict)
        
    Returns:
        True se bem-sucedido, False se falhar
    """
    client = await get_odoo_client()

    try:
        # Converte para dicionário se for um modelo Pydantic
        if hasattr(fields_data, 'dict'):
            data = fields_data.dict(exclude_unset=True, exclude_none=True)
        else:
            data = {k: v for k, v in fields_data.items() if v is not None}

        return await client.write(TASK_MODEL, task_id, data)
    except Exception as e:
        logger.error(f'Erro ao atualizar campos da tarefa: {e}')
        return False


async def update_task_sale_order(task_id: int, sale_order_id: int) -> bool:
    """
    Atualiza uma tarefa com o ID de um pedido de venda de forma assíncrona.
    
    Args:
        task_id: ID da tarefa a ser atualizada
        sale_order_id: ID do pedido de venda a ser vinculado
        
    Returns:
        True se bem-sucedido, False se falhar
    """
    client = await get_odoo_client()

    try:
        return await client.write(TASK_MODEL, task_id, {'sale_order_id': sale_order_id})
    except Exception as e:
        logger.error(f'Erro ao atualizar tarefa com ID do pedido de venda: {e}')
        return False


async def update_task_from_model(task_id: int, update_model: Union[TaskSaleOrderUpdate, TaskStageUpdate, TarefaUpdate]) -> bool:
    """
    Atualiza uma tarefa com base em um modelo de atualização.
    
    Args:
        task_id: ID da tarefa a ser atualizada
        update_model: Modelo Pydantic com os dados de atualização
        
    Returns:
        True se bem-sucedido, False se falhar
    """
    client = await get_odoo_client()

    try:
        data = update_model.dict(exclude_unset=True, exclude_none=True)
        return await client.write(TASK_MODEL, task_id, data)
    except Exception as e:
        logger.error(f'Erro ao atualizar tarefa com modelo: {e}')
        return False


async def create_task_attachment(task_id: int, file_name: str, file_content: str) -> Optional[int]:
    """
    Adiciona um anexo a uma tarefa de forma assíncrona.
    
    Args:
        task_id: ID da tarefa
        file_name: Nome do arquivo
        file_content: Conteúdo do arquivo codificado em base64
        
    Returns:
        ID do anexo criado ou None em caso de erro
    """
    client = await get_odoo_client()

    try:
        attachment_data = {
            "name": file_name,
            "datas": file_content,
            "res_model": TASK_MODEL,
            "res_id": task_id,
        }

        return await client.create("ir.attachment", attachment_data)
    except Exception as e:
        logger.error(f'Erro ao anexar arquivo à tarefa: {e}')
        return None

# app/services/tasks_project_service.py
# Adicione esta função ao seu arquivo

async def get_tasks_by_stage_name(project_id: int, stage_name: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Obtém tarefas de um projeto filtradas pelo nome do estágio de forma assíncrona.
    
    Args:
        project_id: ID do projeto
        stage_name: Nome do estágio para filtrar
        limit: Limite de registros a serem retornados
        offset: Deslocamento para paginação
        
    Returns:
        Lista de tarefas ou lista vazia em caso de erro
    """
    client = await get_odoo_client()
    
    try:
        # Primeiro, busca o ID do estágio pelo nome
        stage_ids = await client.search_read(
            'project.task.type',
            [['name', 'ilike', stage_name]],
            fields=['id']
        )
        
        if not stage_ids:
            logger.warning(f'Nenhum estágio encontrado com nome {stage_name}')
            return []
        
        # Extrai os IDs dos estágios encontrados
        stage_ids_list = [stage['id'] for stage in stage_ids]
        
        # Busca tarefas com o project_id e stage_id correspondentes
        tasks_info = await client.search_read(
            TASK_MODEL,
            [['project_id', '=', project_id], ['stage_id', 'in', stage_ids_list]],
            fields=['id', 'name', 'project_id', 'stage_id', 'sale_order_id',
                   'x_studio_tese_2', 'x_studio_segmento', 'partner_id'],
            limit=limit,
            offset=offset
        )
        
        return tasks_info
    except Exception as e:
        logger.error(f'Erro ao buscar tarefas por estágio: {e}')
        return []

async def transfer_task_messages(source_task_id: int, target_task_id: int) -> bool:
    """
    Transfere as mensagens (message_ids) de uma tarefa para outra de forma assíncrona.
    
    Args:
        source_task_id: ID da tarefa de origem das mensagens
        target_task_id: ID da tarefa de destino para onde as mensagens serão copiadas
        
    Returns:
        True se a operação for bem-sucedida, False em caso de erro
    """
    client = await get_odoo_client()
    
    try:
        # Obter as mensagens da tarefa de origem
        source_task = await client.search_read(
            TASK_MODEL,
            [['id', '=', source_task_id]],
            fields=['message_ids']
        )
        
        if not source_task or not source_task[0].get('message_ids'):
            logger.warning(f'A tarefa de origem {source_task_id} não possui mensagens para transferir')
            return True  # Retorna True pois não há erro, apenas não há mensagens
        
        source_messages = source_task[0]['message_ids']
        
        # Obter as mensagens da tarefa de destino para evitar duplicação
        target_task = await client.search_read(
            TASK_MODEL,
            [['id', '=', target_task_id]],
            fields=['message_ids']
        )
        
        if not target_task:
            logger.error(f'Tarefa de destino {target_task_id} não encontrada')
            return False
            
        target_messages = target_task[0].get('message_ids', [])
        
        # Para cada mensagem na tarefa de origem
        for message_id in source_messages:
            # Pular se a mensagem já existir na tarefa de destino
            if message_id in target_messages:
                continue
                
            # Obter detalhes da mensagem original
            message_data = await client.search_read(
                'mail.message',
                [['id', '=', message_id]],
                fields=['body', 'subject', 'message_type', 'subtype_id', 'author_id']
            )
            
            if not message_data:
                continue
                
            message_data = message_data[0]
            
            # Criar nova mensagem na tarefa de destino
            new_message = {
                'body': message_data.get('body', ''),
                'subject': message_data.get('subject', ''),
                'message_type': message_data.get('message_type', 'comment'),
                'subtype_id': message_data.get('subtype_id') and message_data['subtype_id'][0],
                'author_id': message_data.get('author_id') and message_data['author_id'][0],
                'model': TASK_MODEL,
                'res_id': target_task_id,
            }
            
            await client.create('mail.message', new_message)
        
        logger.info(f'Mensagens transferidas com sucesso da tarefa {source_task_id} para {target_task_id}')
        return True
        
    except Exception as e:
        logger.error(f'Erro ao transferir mensagens entre tarefas: {e}')
        return False

async def update_task_stage(task_id: int, stage_id: int) -> bool:
    """
    Atualiza o estágio de uma tarefa de forma assíncrona.
    
    Args:
        task_id: ID da tarefa a ser atualizada
        stage_id: ID do estágio para o qual a tarefa deve ser movida
        
    Returns:
        True se bem-sucedido, False se falhar
    """
    client = await get_odoo_client()
    
    try:
        return await client.write(TASK_MODEL, task_id, {'stage_id': stage_id})
    except Exception as e:
        logger.error(f'Erro ao atualizar estágio da tarefa: {e}')
        return False
