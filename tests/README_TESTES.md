# Testes de Criação de Oportunidades

Este diretório contém testes unitários abrangentes para a funcionalidade de criação de oportunidades unificadas.

## Arquivos de Teste

### 1. `test_opportunities.py`
Contém testes completos para:
- **`TestValidateCpfCnpj`**: Validação de CPF/CNPJ
- **`TestCreateOpportunityUnified`**: Criação de oportunidades com todos os cenários

### 2. `test_create_opportunity_examples.py`
Exemplos práticos demonstrando os casos de uso específicos solicitados:
- Criação apenas com nome
- Criação completa com empresa, CNPJ, tese INSS, team_id=6 e parceiro comercial='32'
- Criação com CPF (11 dígitos)

## Como Executar os Testes

### Executar todos os testes
```bash
uv run pytest tests/test_opportunities.py -v
```

### Executar apenas testes de validação CPF/CNPJ
```bash
uv run pytest tests/test_opportunities.py::TestValidateCpfCnpj -v
```

### Executar apenas testes de criação de oportunidades
```bash
uv run pytest tests/test_opportunities.py::TestCreateOpportunityUnified -v
```

### Executar exemplos práticos
```bash
uv run pytest tests/test_create_opportunity_examples.py -v -s
```

### Executar um teste específico
```bash
uv run pytest tests/test_opportunities.py::TestCreateOpportunityUnified::test_create_opportunity_apenas_nome -v
```

## Cenários Testados

### ✅ Validação de Documentos
- CPF válido (11 dígitos)
- CNPJ válido (14 dígitos)
- Documentos com formatação (máscaras)
- Documentos inválidos (tamanhos incorretos)
- Documentos vazios ou nulos

### ✅ Criação de Oportunidades
- **Apenas nome obrigatório**: Mínimo necessário para criar
- **Com empresa e CNPJ**: Criação automática de cliente
- **Com receita esperada**: Valores monetários
- **Com equipe específica**: team_id personalizado
- **Tratamento de erros**: CNPJ inválido, falhas no Odoo, etc.

### ✅ Casos Específicos Solicitados
1. **Apenas nome**: `{"name": "Minha Oportunidade"}`
2. **Completo**: `{"name": "...", "company_name": "...", "company_cnpj": "...", "x_studio_tese": "inss", "team_id": 6, "x_studio_selection_field_37f_1ibrq64l3": "32"}`
3. **Com CPF**: `{"name": "...", "company_cnpj": "12345678901"}`

## Estrutura dos Testes

### Mocking
- **AsyncOdooClient**: Simulado para não fazer chamadas reais ao Odoo
- **get_or_create_partner_by_vat**: Simulado para controlar criação de parceiros
- **Retornos**: Dados estruturados como o Odoo real retornaria

### Verificações
- **Dados de entrada**: Validação dos schemas Pydantic
- **Chamadas de método**: Verificação de parâmetros corretos
- **Dados de saída**: Estrutura e valores do resultado
- **Tratamento de erros**: HTTPExceptions apropriadas

## Cobertura de Testes

### Casos de Sucesso ✅
- Criação mínima (apenas nome)
- Criação com cliente (CNPJ/CPF)
- Criação com todos os campos opcionais
- Validação de documentos com formatação

### Casos de Erro ✅
- Documentos inválidos
- Falha na criação de parceiro
- Falha na criação da oportunidade no Odoo
- Falha na busca de detalhes após criação

### Campos Testados ✅
- `name` (obrigatório)
- `company_name` (opcional)
- `company_cnpj` (opcional, CPF/CNPJ)
- `team_id` (opcional)
- `expected_revenue` (opcional)
- `x_studio_tese` (opcional)
- `x_studio_selection_field_37f_1ibrq64l3` (opcional)
- `user_id` (default=3)

## Resultado dos Testes

```
========================= 22 passed, 4 warnings in 1.94s =========================
```

Todos os 22 testes passaram com sucesso, garantindo a robustez da funcionalidade de criação de oportunidades unificadas.