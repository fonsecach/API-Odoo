# README - API FastAPI com Integração ao Odoo

Este projeto é uma API desenvolvida em FastAPI para integração com o Odoo, permitindo operações como listagem e cadastro de empresas, gestão de oportunidades e mais.
>[!WARNING]
>Em desenvolvimento, os metodos e endpoints poderão ser atualizados.

![Screenshot 2024-11-01 at 11-48-08 FastAPI - ReDoc](https://github.com/user-attachments/assets/fba9ade1-f732-4ccb-9b19-de391a4d132d)

## Requisitos

Certifique-se de que você tenha os seguintes softwares instalados no seu sistema:
- Python 3.11.9
- Git
- Docker (opcional, para criar a imagem Docker)
- Criar um arquivo .ENV e inserir suas credenciais do Odoo (Dúvida consultar https://www.odoo.com/documentation/master/developer/reference/external_api.html)

## Instalação

### Passos para clonar o repositório:

1. **Clone o repositório do GitHub**:
    ```bash
    git clone https://github.com/Fonsecach/API-Odoo.git
    ```

2. **Navegue até o diretório do projeto**:
    ```bash
    cd API-Odoo
    ```

3. **Crie e ative um ambiente virtual** (opcional, mas recomendado):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Linux/MacOS
    venv\Scripts\activate     # Windows
    ```

4. **Instale as dependências**:
    ```bash
    pip install -r requirements.txt
    ```

## Como Executar

Para iniciar a API, execute o seguinte comando:

```bash
uvicorn main:app --reload
```

A aplicação estará disponível em http://127.0.0.1:8000.

## Documentação

A documentação interativa (Swagger) da API estará disponível em:

http://127.0.0.1:8000/docs

Para a documentação alternativa com Redoc:

http://127.0.0.1:8000/redoc

Docker
Para criar e executar uma imagem Docker da API, siga as instruções abaixo:

Crie a imagem Docker:


```bash
docker build -t api-odoo .
```
Execute o container Docker:


```bash
docker run -d --name api-odoo-container -p 8000:8000 api-odoo
```
Agora, a API estará disponível em http:/localhost:8000.
