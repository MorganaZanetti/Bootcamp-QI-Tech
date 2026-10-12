# Bootcamp QI-Tech

Projeto de uma **API bancária com foco em investimentos**, desenvolvido
em Python utilizando **FastAPI, SQLAlchemy, PostgreSQL e Docker**.

O sistema permite cadastrar clientes PF e PJ, autenticar usuários,
movimentar uma conta corrente e solicitar uma conta de investimentos.
Após a aprovação da conta pelo gerente, o cliente pode consultar dados
de mercado e realizar investimentos em **USD, EUR e JPY**.

Além da API, o projeto possui uma **CLI (interface pelo terminal)** para
facilitar a utilização das funcionalidades e uma **API Mock**
responsável por fornecer dados simulados de câmbio, CDI, Selic, IR e
IOF.

------------------------------------------------------------------------

## Funcionalidades

### Cliente e conta corrente

-   Cadastro de Pessoa Física (PF) e Pessoa Jurídica (PJ);
-   login e autenticação;
-   criação automática da conta corrente no cadastro;
-   consulta das contas do cliente;
-   depósito;
-   transferência entre contas;
-   PIX simulado por CPF/CNPJ;
-   extrato da conta corrente.

### Investimentos

-   solicitação de abertura de conta de investimento;
-   aprovação ou rejeição da conta pelo gerente;
-   consulta de câmbio;
-   consulta das métricas antes da aplicação;
-   investimentos em USD, EUR e JPY;
-   investimento mínimo de **R\$ 2.000,00 para PF**;
-   investimento mínimo de **R\$ 5.000,00 para PJ**;
-   spread bancário de **2,5%**;
-   consulta das posições;
-   cálculo de ganho ou perda em BRL e na moeda estrangeira;
-   alerta quando a cotação fica 10% ou mais abaixo do custo médio de
    aquisição;
-   extrato de investimentos;
-   simulação de meta de investimento.

A simulação de meta é apenas uma consulta: **a meta, os cálculos e os
resultados da simulação não são armazenados no banco de dados**.

------------------------------------------------------------------------

## Como o projeto funciona

A aplicação foi organizada em camadas para separar as responsabilidades
do sistema:

``` text
CLI
 |
 v
FastAPI / Resources
 |
 v
Schemas
 |
 v
Controllers
 |
 v
Repositories
 |
 v
Models
 |
 v
PostgreSQL

Controllers
 |
 v
Connectors
 |
 v
Mock Market API
```

De forma simplificada:

-   **CLI (`cli.py`)**: interface utilizada pelo usuário no terminal;
-   **Resources**: recebem as requisições HTTP da API;
-   **Schemas**: validam os dados recebidos e enviados;
-   **Controllers**: executam as regras de negócio;
-   **Repositories**: realizam as operações de acesso ao banco;
-   **Models**: representam as tabelas do banco através do SQLAlchemy;
-   **PostgreSQL**: armazena clientes, contas, transações, investimentos
    e históricos;
-   **Connectors**: fazem a comunicação com serviços externos;
-   **Mock Market API**: simula uma API externa de dados financeiros.

O fluxo normal de uma operação é, portanto:

``` text
Usuário -> CLI -> API -> Controller -> Repository -> PostgreSQL
```

Quando são necessários dados financeiros:

``` text
Controller -> Connector -> Mock Market API
```

------------------------------------------------------------------------

## Tecnologias utilizadas

-   Python
-   FastAPI
-   SQLAlchemy
-   PostgreSQL
-   Docker
-   Docker Compose
-   Pydantic
-   HTTPX
-   Pytest

------------------------------------------------------------------------

## Estrutura principal

``` text
.
├── app.py
├── cli.py
├── authentication.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── database/
│   └── database.sql
├── mock_server/
├── src/
│   ├── connectors/
│   ├── controllers/
│   ├── models/
│   ├── repositories/
│   ├── resources/
│   └── schema/
└── tests/
```

------------------------------------------------------------------------

# Instruções para execução

## Pré-requisitos

Para executar o projeto utilizando Docker, é necessário ter:

-   Docker;
-   Docker Compose;
-   Python instalado para executar a CLI localmente.

Para verificar:

``` bash
docker --version
docker compose version
python --version
```

No Windows, caso o comando `python` não funcione, tente:

``` bash
py --version
```

------------------------------------------------------------------------

## 1. Abrir a pasta do projeto

No terminal, entre na pasta onde o projeto foi extraído:

``` bash
cd Desafio-Investment-Bank-API
```

------------------------------------------------------------------------

## 2. Iniciar os serviços

Execute:

``` bash
docker compose up --build
```

O Docker iniciará três serviços:

-   **PostgreSQL**: banco de dados;
-   **API**: aplicação principal;
-   **Mock API**: serviço que fornece os dados financeiros simulados.

Após a inicialização:

``` text
API principal: http://localhost:8000
Swagger:       http://localhost:8000/docs
Mock API:      http://localhost:9000
Mock Swagger:  http://localhost:9000/docs
PostgreSQL:    localhost:5432
```

Mantenha esse terminal aberto enquanto estiver utilizando o sistema.

------------------------------------------------------------------------

## 3. Executar a CLI

Abra um **segundo terminal**, entre novamente na pasta do projeto e
execute:

``` bash
python cli.py
```

No Windows também pode ser utilizado:

``` bash
py cli.py
```

Caso apareça erro informando que o módulo `httpx` não está instalado:

``` bash
python -m pip install httpx
```

Depois execute novamente:

``` bash
python cli.py
```

A interface deverá apresentar o menu do **Investment Bank API**.

------------------------------------------------------------------------

## Utilização básica

O fluxo sugerido para testar o sistema é:

1.  cadastrar um cliente;
2.  realizar login;
3.  consultar a conta corrente criada automaticamente;
4.  realizar um depósito;
5.  testar transferência ou PIX;
6.  consultar o extrato da conta corrente;
7.  solicitar uma conta de investimento;
8.  acessar o menu do gerente e aprovar a solicitação;
9.  entrar novamente como cliente;
10. consultar câmbio e métricas;
11. realizar um investimento;
12. consultar posições e extrato de investimentos;
13. testar a simulação de meta.

A chave padrão do gerente no ambiente de desenvolvimento é:

``` text
manager123
```

------------------------------------------------------------------------

## Formato dos dados

A CLI apresenta exemplos dos formatos esperados. Alguns dos principais
são:

``` text
CPF:          123.123.123-12
CNPJ:         12.345.678/0001-90
Data:         05/09/2005
Conta:        123456
Valor:        1000.00
Moeda:        USD, EUR ou JPY
```

Para valores monetários, utilize ponto como separador decimal na
entrada:

``` text
2000.00
```

------------------------------------------------------------------------

# Banco de dados

O banco é criado automaticamente pelo Docker utilizando:

``` text
database/database.sql
```

Não é necessário executar o arquivo SQL manualmente.

Caso o `database.sql` seja alterado depois que o banco já tiver sido
criado, o volume antigo pode continuar utilizando a estrutura anterior.

Para recriar completamente o banco de desenvolvimento:

``` bash
docker compose down -v
docker compose up --build
```

**Atenção:** `docker compose down -v` remove o volume do PostgreSQL e
apaga os dados locais cadastrados anteriormente.

Para apenas parar os containers sem apagar os dados:

``` bash
docker compose down
```

------------------------------------------------------------------------

# Executando os testes

O projeto utiliza **Pytest**.

Com os containers em execução, a forma recomendada de executar todos os
testes é:

``` bash
docker compose exec api python -m pytest -v
```

Para uma saída mais resumida:

``` bash
docker compose exec api python -m pytest -q
```

Os testes automatizados utilizam um banco SQLite isolado para validar
rapidamente as regras da aplicação, enquanto a execução normal através
do Docker utiliza PostgreSQL. Os dados da API externa também são
substituídos por valores controlados durante os testes.

------------------------------------------------------------------------

## Executar apenas um arquivo de testes

Exemplo:

``` bash
docker compose exec api python -m pytest tests/test_auth_api.py -v
```

Outros arquivos disponíveis incluem:

``` text
tests/test_accounts_transactions.py
tests/test_auth_api.py
tests/test_calculations.py
tests/test_investments_scope.py
tests/test_pix.py
tests/test_validators.py
```

------------------------------------------------------------------------

## Executar um teste específico

Utilize:

``` bash
docker compose exec api python -m pytest caminho_do_arquivo.py::nome_do_teste -v
```

Exemplo de formato:

``` bash
docker compose exec api python -m pytest tests/test_auth_api.py::nome_do_teste -v
```

------------------------------------------------------------------------

## Testes fora do Docker

Também é possível executar os testes diretamente pelo Python, desde que
todas as dependências estejam instaladas:

``` bash
python -m pip install -r requirements.txt
python -m pytest -v
```

Para evitar diferenças de versão ou configuração entre computadores,
recomenda-se utilizar os testes através do container da API.

------------------------------------------------------------------------

# Reiniciando o projeto

Para parar:

``` bash
docker compose down
```

Para iniciar novamente:

``` bash
docker compose up
```

Se houver mudanças no código ou nas dependências e for necessário
reconstruir as imagens:

``` bash
docker compose up --build
```

Para reconstruir também o banco do zero:

``` bash
docker compose down -v
docker compose up --build
```

------------------------------------------------------------------------

# Observações

-   Os cálculos monetários utilizam `Decimal`/`NUMERIC`, evitando
    `float` para valores financeiros.
-   Os UUIDs existentes são utilizados apenas internamente e não são
    apresentados ao cliente ou gerente.
-   A API Mock é utilizada apenas para simular os dados externos
    necessários ao projeto.
-   O spread utilizado no projeto é de 2,5%.
-   O extrato da conta corrente registra as movimentações bancárias
    realizadas.
-   O extrato de investimentos apresenta as informações relacionadas às
    aplicações e seus custos.
-   Os valores de mercado, IR e IOF utilizados pela Mock API são valores
    de demonstração do projeto.
