# INVESTMENT BANK API

Projeto construído a partir do **Desafio-base**, preservando os nomes centrais da base (`app.py`, `authentication.py`, `database/database.sql`) e usando a organização em camadas da versão concluída:

```text
CLI -> FastAPI/resources -> schemas -> controllers -> repositories -> models -> PostgreSQL
                                      -> connectors -> Mock Market API
```

O projeto mantém apenas **um arquivo SQL**: `database/database.sql`.

## Escopo implementado

- cadastro PF e PJ, login e conta corrente criada automaticamente;
- conta de investimento solicitada pelo cliente e aprovada/rejeitada pelo gerente;
- depósito, transferência e PIX simulado;
- PostgreSQL + SQLAlchemy; dinheiro e taxas com `NUMERIC`/`Decimal`, sem `float` para cálculo bancário;
- investimento somente em **USD, EUR e JPY**;
- investimento mínimo: **PF R$ 2.000,00** e **PJ R$ 5.000,00**;
- spread fixo do banco: **2,5%**;
- uma única API mock (`mock_server`) fornece **câmbio, CDI, Selic, IR e IOF**;
- tela de métricas antes do investimento mostra câmbio, CDI, Selic, IR, IOF, spread, custos e valor líquido convertido;
- alerta de moeda quando a cotação atual fica **10% ou mais abaixo do custo médio de aquisição**. O alerta é informativo e a decisão de continuar investindo é do cliente;
- posições mostram ganho/perda em BRL e na moeda investida;
- extrato mostra métricas/custos separados e totais consolidados;
- simulação de meta calcula o tempo estimado por moeda e para a carteira combinada;
- **simulação não persiste meta, entrada ou resultado no banco**;
- UUIDs permanecem apenas como identificadores técnicos internos de banco quando já existiam no modelo, mas **não são retornados pelas rotas, não são usados na CLI e não aparecem para cliente ou gerente**.

## Simulação de meta

A simulação usa o valor atual das posições do cliente e uma taxa de referência líquida baseada na Selic mock, descontando a alíquota de IR usada no projeto. Ela calcula quantos meses seriam necessários para a posição atual atingir a meta, separadamente para USD, EUR e JPY, e também para o valor combinado da carteira. Se não existir posição naquela moeda, a CLI informa que não há valor atual suficiente para calcular. Nada dessa operação é gravado.

## Executar com Docker

```bash
docker compose up --build
```

Serviços:

- API: `http://localhost:8000/docs`
- Mock: `http://localhost:9000/docs`
- PostgreSQL: `localhost:5432`

Em outro terminal:

```bash
python cli.py
```

Se uma versão antiga do banco já tiver sido criada e o `database.sql` tiver mudado, recrie o banco de desenvolvimento:

```bash
docker compose down -v
docker compose up --build
```

> `down -v` apaga os dados locais do PostgreSQL. Use apenas quando puder recriar o banco.

## Testes

```bash
python -m pytest -q
```

Os testes automatizados usam SQLite isolado para testar as regras rapidamente; a aplicação Docker usa PostgreSQL. O mock externo é substituído por dados controlados durante os testes.

## Formatos mostrados na CLI

A própria CLI mostra exemplos junto aos campos, por exemplo:

- CPF: `123.123.123-12`
- CNPJ: `12.345.678/0001-90`
- data: `05/09/2005`
- conta: `123456`
- valor: `1000.00`
- moeda: `USD`, `EUR` ou `JPY`

## Gerente no ambiente de demonstração

A chave padrão de desenvolvimento é `manager123`. Ela pode ser alterada pela variável de ambiente `MANAGER_KEY`.


## Extrato da conta corrente

A API disponibiliza `GET /v1/accounts/{account_number}/statement` para consultar as movimentações da conta corrente autenticada. A CLI expõe a opção **Extrato da conta corrente**, mostrando depósitos, transferências, PIX e aplicações em investimentos, com valor, saldo após a movimentação e saldo atual.
