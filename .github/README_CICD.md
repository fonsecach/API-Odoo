# CI/CD Pipeline - GitHub Actions + Fly.io

Este repositório possui um pipeline CI/CD automatizado que executa testes e faz deploy para o Fly.io.

## 🔧 Configuração Inicial

### 1. Secrets do GitHub

Configure os seguintes secrets no GitHub (Settings → Secrets and variables → Actions):

```bash
FLY_API_TOKEN=your_fly_api_token_here
```

### 2. Como obter o FLY_API_TOKEN

```bash
# Instalar Fly CLI
curl -L https://fly.io/install.sh | sh

# Fazer login
flyctl auth login

# Obter token
flyctl auth token
```

### 3. Configurar aplicação no Fly.io

```bash
# Na raiz do projeto
flyctl launch

# Ou se já tem fly.toml
flyctl deploy
```

## 🚀 Workflows Configurados

### 1. `deploy.yml` - Pipeline Principal

**Triggers:**
- `push` na branch `release-flyio` → Executa testes + deploy
- `pull_request` nas branches `main`, `master`, `develop` → Executa apenas testes

**Jobs:**
1. **test**: Executa todos os testes com uv
2. **deploy**: Deploy no Fly.io (apenas branch `release-flyio`)
3. **notify**: Notifica resultados

### 2. `dependabot.yml` - Atualizações Automáticas

**Funcionalidades:**
- **Auto-merge**: Patches e minor updates automáticos
- **Review manual**: Major updates precisam de aprovação
- **Testes**: Executa testes antes do merge
- **Agrupamento**: Agrupa updates relacionados

## 📋 Fluxo de Trabalho

### Desenvolvimento Normal
```bash
# 1. Desenvolver na branch de feature
git checkout -b feature/nova-funcionalidade

# 2. Fazer commits
git add .
git commit -m "feat: adiciona nova funcionalidade"

# 3. Abrir PR para main/develop
# → Executa apenas testes
```

### Deploy para Produção
```bash
# 1. Mergear para release-flyio
git checkout release-flyio
git merge main

# 2. Push para GitHub
git push origin release-flyio
# → Executa testes + deploy automático
```

### Atualizações de Dependências
```bash
# Dependabot cria PRs automaticamente:
# - Minor/Patch: Auto-merge se testes passarem
# - Major: Comentário solicitando review manual
```

## 🧪 Comandos de Teste Locais

```bash
# Instalar dependências
uv sync

# Executar todos os testes
uv run pytest tests/ -v

# Testes específicos
uv run pytest tests/test_opportunities.py::TestValidateCpfCnpj -v
uv run pytest tests/test_opportunities.py::TestCreateOpportunityUnified -v
uv run pytest tests/test_create_opportunity_examples.py -v

# Com cobertura
uv run pytest tests/ --cov=app --cov-report=term-missing
```

## 📊 Status dos Testes

### Testes Incluídos
- ✅ **Validação CPF/CNPJ**: 8 testes
- ✅ **Criação de Oportunidades**: 7 testes  
- ✅ **Exemplos Práticos**: 3 testes
- ✅ **Testes Legados**: 7 testes

**Total: 25 testes automatizados**

### Cobertura
- Validação de entrada
- Lógica de negócio
- Tratamento de erros
- Integração com Odoo (mockada)

## 🔒 Segurança

### Dependabot Configuration
- **Frequência**: Semanal
- **Timezone**: America/Sao_Paulo
- **Auto-merge**: Apenas minor/patch
- **Labels**: Automáticas por categoria

### Verificações de Segurança
- `safety check` para vulnerabilidades
- Testes automatizados antes do merge
- Review manual para major updates

## 🚨 Troubleshooting

### Testes Falhando
```bash
# Ver logs detalhados
uv run pytest tests/ -v --tb=long

# Executar teste específico
uv run pytest tests/test_opportunities.py::test_nome_especifico -v -s
```

### Deploy Falhando
```bash
# Verificar configuração do Fly.io
flyctl status

# Ver logs da aplicação
flyctl logs

# Verificar fly.toml
cat fly.toml
```

### Dependabot Não Funcionando
1. Verificar se `.github/dependabot.yml` está correto
2. Verificar permissões do repositório
3. Verificar se o username nos reviewers existe

## 📝 Arquivos Importantes

```
.github/
├── workflows/
│   ├── deploy.yml          # Pipeline principal
│   └── dependabot.yml      # Auto-merge do Dependabot
├── dependabot.yml          # Configuração do Dependabot
└── README_CICD.md          # Esta documentação

tests/
├── test_opportunities.py           # Testes principais
├── test_create_opportunity_examples.py  # Exemplos
└── README_TESTES.md               # Documentação dos testes
```

## 🎯 Próximos Passos

1. **Criar branch release-flyio**:
   ```bash
   git checkout -b release-flyio
   git push origin release-flyio
   ```

2. **Configurar secrets no GitHub**
3. **Testar pipeline com um commit**
4. **Monitorar Dependabot**

## 📞 Suporte

Se você encontrar problemas:
1. Verifique os logs do GitHub Actions
2. Verifique se todos os secrets estão configurados
3. Teste localmente com `uv run pytest`
4. Verifique se o Fly.io está configurado corretamente