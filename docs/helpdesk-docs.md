# Helpdesk - Documentação Técnica

## Visão Geral

O sistema de Helpdesk é uma API REST desenvolvida com FastAPI que se integra com o sistema Odoo para gerenciamento de tickets de suporte. O sistema permite listar, filtrar e gerenciar chamados de suporte através de endpoints HTTP, utilizando autenticação via XML-RPC para comunicação segura com o Odoo.

## Arquitetura

### Diagrama de Sequência

![mermaid-diagram-2024-12-01-200004](https://github.com/user-attachments/assets/0cc86300-2d0e-40dc-9eed-8cf853ef1721)

## Endpoints

### GET /routers/tickets

Lista todos os tickets de suporte disponíveis.

**Parâmetros de Query:**

- `limit` (opcional): Número máximo de tickets a retornar (default: 100)
- `offset` (opcional): Número de tickets a pular (default: 0)

**Resposta de Sucesso:**

```json
{
    "chamados": [
        {
            "id": 1,
            "name": "Título do Chamado",
            "description": "Descrição do problema",
            "state": "novo",
            "create_date": "2024-01-01 10:00:00"
        }
    ]
}
```

### GET /routers/tickets/{team_id}

Lista todos os tickets de um time específico.

**Parâmetros de Path:**

- `team_id`: ID do time de suporte

**Parâmetros de Query:**

- `limit` (opcional): Número máximo de tickets a retornar (default: 100)
- `offset` (opcional): Número de tickets a pular (default: 0)

### GET /routers/tickets/{team_id}/{ticket_id}

Retorna informações detalhadas de um ticket específico.

**Parâmetros de Path:**

- `team_id`: ID do time de suporte
- `ticket_id`: ID do ticket

## Autenticação

O sistema utiliza autenticação XML-RPC com o servidor Odoo. As credenciais são configuradas através das seguintes variáveis de ambiente:

- `ODOO_URL`: URL do servidor Odoo
- `ODOO_DB`: Nome do banco de dados
- `ODOO_USERNAME`: Usuário do Odoo
- `ODOO_PASSWORD`: Senha do usuário

## Códigos de Erro

- `401 Unauthorized`: Falha na autenticação com o Odoo
- `400 Bad Request`: Nenhum chamado encontrado para os parâmetros fornecidos

## Desenvolvimento e Testes

### Executando Testes

```bash
uv pytest tests/test_helpdesk.py -v
```

### Executando a Aplicação Localmente em modo de desenvolvimento

```bash
uv run fastapi dev main.py
```

## Dependências Principais

- FastAPI
- xmlrpc.client
- pytest (para testes)

## Estrutura do Projeto

```
├── app/
│   ├── routers/
│   │   └── helpdesk_endpoints.py
│   │   └── ...
│   ├── Services/
│   │   ├── authentication.py
│   │   └── helpdesk_service.py
│   │   └── ...
│   └── config/
│       └── settings.py
├── tests/
│   ├── conftest.py
│       └── test_helpdesk.py
│       └── ...
└── main.py
```

## Próximos Passos

- [ ] Implementar criação de tickets via API
- [ ] Implementar alteração de tickets via API
- [ ] Adicionar mais filtros de busca
