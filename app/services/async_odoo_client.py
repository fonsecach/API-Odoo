# app/services/async_odoo_client.py
import asyncio
import concurrent.futures
import functools
import logging
import xmlrpc.client
from typing import Any, Dict, List, Optional, Union

# Configurar logger
logger = logging.getLogger(__name__)


class AsyncOdooClient:
    """
    Cliente assíncrono para comunicação com o Odoo via XML-RPC.

    Permite executar chamadas XML-RPC ao Odoo de forma assíncrona,
    usando um ThreadPoolExecutor para evitar o bloqueio do loop de eventos.
    """

    _instances = {}  # Singleton pattern para reutilização de clientes

    @classmethod
    async def get_instance(
        cls, url: str, db: str, username: str, password: str
    ) -> 'AsyncOdooClient':
        """
        Obtém uma instância existente ou cria uma nova com as credenciais fornecidas.
        Implementa um padrão singleton baseado nas credenciais.
        """
        instance_key = f'{url}_{db}_{username}'
        if instance_key not in cls._instances:
            client = cls(url, db, username, password)
            await client.authenticate()  # Autenticar ao criar
            cls._instances[instance_key] = client

        return cls._instances[instance_key]

    def __init__(self, url: str, db: str, username: str, password: str):
        """
        Inicializa o cliente Odoo.

        Args:
            url: URL do servidor Odoo
            db: Nome do banco de dados
            username: Nome de usuário para autenticação
            password: Senha para autenticação
        """
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self._common_proxy = xmlrpc.client.ServerProxy(
            f'{url}/xmlrpc/2/common'
        )
        self._models_proxy = xmlrpc.client.ServerProxy(
            f'{url}/xmlrpc/2/object'
        )
        self._uid = None
        # Criar um executor com número limitado de workers para evitar sobrecarga
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)

    async def authenticate(self) -> Optional[int]:
        """
        Autentica o usuário no Odoo e armazena o UID.

        Returns:
            User ID (uid) se autenticado com sucesso, None caso contrário
        """
        if self._uid:
            return self._uid

        try:
            # Executa a chamada síncrona de autenticação em uma thread separada
            func = functools.partial(
                self._common_proxy.authenticate,
                self.db,
                self.username,
                self.password,
                {},
            )

            self._uid = await asyncio.get_event_loop().run_in_executor(
                self._executor, func
            )

            if self._uid:
                logger.info(f'Autenticação bem-sucedida. UID: {self._uid}')
            else:
                logger.error('Falha na autenticação.')

            return self._uid

        except Exception as e:
            logger.error(f'Erro ao autenticar: {e}')
            return None

    async def execute_kw(
        self,
        model: str,
        method: str,
        args: List[Any],
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Executa um método no Odoo de forma assíncrona.

        Args:
            model: Nome do modelo Odoo (ex: 'res.partner')
            method: Nome do método a ser executado (ex: 'search_read')
            args: Lista de argumentos posicionais
            kwargs: Dicionário de argumentos nomeados

        Returns:
            Resultado da chamada ao método

        Raises:
            Exception: Qualquer exceção ocorrida durante a chamada
        """
        if not self._uid:
            await self.authenticate()

            if not self._uid:
                raise Exception('Falha na autenticação no Odoo')

        kwargs = kwargs or {}

        func = functools.partial(
            self._models_proxy.execute_kw,
            self.db,
            self._uid,
            self.password,
            model,
            method,
            args,
            kwargs,
        )

        try:
            return await asyncio.get_event_loop().run_in_executor(
                self._executor, func
            )
        except Exception as e:
            logger.error(f'Erro ao executar {model}.{method}: {e}')
            raise

    # Métodos genéricos de CRUD

    async def search_read(
        self,
        model: str,
        domain: List,
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
        order: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca e lê registros no Odoo.

        Args:
            model: Nome do modelo
            domain: Filtro de domínio (ex: [['active', '=', True]])
            fields: Lista de campos a retornar
            limit: Número máximo de registros
            offset: Deslocamento para paginação
            order: Ordenação (ex: 'name ASC')

        Returns:
            Lista de registros encontrados
        """
        kwargs = {}
        if fields:
            kwargs['fields'] = fields
        if limit is not None:
            kwargs['limit'] = limit
        if offset:
            kwargs['offset'] = offset
        if order:
            kwargs['order'] = order

        try:
            return await self.execute_kw(
                model, 'search_read', [domain], kwargs
            )
        except Exception as e:
            logger.error(f'Erro em search_read de {model}: {e}')
            return []

    async def create(
        self, model: str, values: Dict[str, Any]
    ) -> Optional[int]:
        """
        Cria um novo registro no Odoo.

        Args:
            model: Nome do modelo
            values: Dicionário com valores dos campos

        Returns:
            ID do registro criado ou None em caso de erro
        """
        try:
            return await self.execute_kw(model, 'create', [values])
        except Exception as e:
            logger.error(f'Erro ao criar registro em {model}: {e}')
            return None

    async def write(
        self,
        model: str,
        record_ids: Union[int, List[int]],
        values: Dict[str, Any],
    ) -> bool:
        """
        Atualiza registros existentes no Odoo.

        Args:
            model: Nome do modelo
            record_ids: ID ou lista de IDs dos registros a atualizar
            values: Dicionário com valores dos campos a atualizar

        Returns:
            True se a atualização foi bem sucedida, False caso contrário
        """
        if isinstance(record_ids, int):
            record_ids = [record_ids]

        try:
            return await self.execute_kw(model, 'write', [record_ids, values])
        except Exception as e:
            logger.error(f'Erro ao atualizar registros em {model}: {e}')
            return False

    async def unlink(
        self, model: str, record_ids: Union[int, List[int]]
    ) -> bool:
        """
        Remove registros no Odoo.

        Args:
            model: Nome do modelo
            record_ids: ID ou lista de IDs dos registros a remover

        Returns:
            True se a remoção foi bem sucedida, False caso contrário
        """
        if isinstance(record_ids, int):
            record_ids = [record_ids]

        try:
            return await self.execute_kw(model, 'unlink', [record_ids])
        except Exception as e:
            logger.error(f'Erro ao remover registros em {model}: {e}')
            return False

    def close(self):
        """Fecha o executor de threads."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)
