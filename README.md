# Desafio Final: ETL da Verdejar
 
ETL em Python que extrai clientes e pedidos de uma API paginada e produtos de um arquivo CSV, trata as seis armadilhas de qualidade dos dados (A1 a A6), carrega o resultado em um PostgreSQL e prova a carga com testes, reconciliação e consultas de validação.
 
---
 
## Ambiente
 
- Windows 11, PowerShell e VS Code
- Python 3.15
- PostgreSQL 16 em contêiner Docker (**caminho B** da seção 4 do desafio)
- Bibliotecas externas (em `requirements.txt`):
  - `psycopg[binary]`: biblioteca de conexão com o PostgreSQL
  - `python-dotenv`: lê a configuração do banco a partir do arquivo `.env`
  - `pytest`: testes automatizados

## Estrutura do projeto
 
```
desafio-final/
  etl/
    extracao.py        Parte 1: API paginada, CSV e dados brutos
    transformacao.py   Parte 2: funções das armadilhas A1 a A6 e contadores
    carga.py           Parte 3: conexão, carga no PostgreSQL e reconciliação
    main.py            executa o ETL completo
  tests/
    test_transformacao.py   testes das armadilhas A1 a A6
    test_reconciliacao.py   teste de reconciliação origem x destino
  insumos_verdejar/    insumos fornecidos (API, gerador, esquemas e dados)
  brutos/              dados extraídos (gerado pelo ETL; fora do Git)
  consultas_validacao.sql
  CONTRATO_DE_DADOS.md
  COMO_USEI_IA.md
  .env.example         modelo do .env (sem a senha)
```
 
Os insumos ficam na pasta `insumos_verdejar/`, e não em `insumos/` como na sugestão da seção 7.
 
## Como rodar
 
Todos os comandos são executados na raiz do projeto (`C:\desafio-final`), exceto onde indicado.
 
### 1. Instalar as dependências
 
```
python -m pip install -r requirements.txt
```
 
### 2. Configurar o acesso ao banco
 
Copie o `.env.example` para um arquivo `.env` e preencha a senha em `DB_SENHA`. O `.env` está no `.gitignore` e nunca é versionado.
 
### 3. Subir o banco (PostgreSQL no Docker) e aplicar o esquema
 
Com o Docker Desktop aberto:
 
```
docker run --name verdejar-pg -e POSTGRES_PASSWORD=SUA_SENHA -e POSTGRES_DB=verdejar -p 5433:5432 -d postgres:16
cd insumos_verdejar
docker cp schema.sql verdejar-pg:/schema.sql
docker exec verdejar-pg psql -U postgres -d verdejar -f /schema.sql
cd ..
```
 
**Porta 5433:** o contêiner usa a porta 5433 do computador, e não a 5432 do documento, porque já havia um PostgreSQL instalado no Windows ocupando a 5432. O `.env` aponta para a 5433.
 
**PowerShell:** o comando do documento usa `< schema.sql`, que não funciona no PowerShell. Por isso o arquivo é copiado para dentro do contêiner com `docker cp` e aplicado com `psql -f`.
 
Nas próximas vezes, basta `docker start verdejar-pg`.
 
### 4. Subir a API (em um terminal separado, que fica aberto)
 
```
cd insumos_verdejar
python api_verdejar.py
```
 
Para conferir, no Windows PowerShell use `curl.exe` (o `curl` do PowerShell é um apelido de outro comando):
 
```
curl.exe "http://127.0.0.1:8000/saude"
```
 
### 5. Rodar o ETL completo
 
```
python -m etl.main
```
 
### 6. Rodar os testes
 
Com o banco carregado (o teste de reconciliação consulta o PostgreSQL):
 
```
python -m pytest -v
```
 
### 7. Rodar as consultas de validação
 
```
docker cp consultas_validacao.sql verdejar-pg:/consultas.sql
docker exec verdejar-pg psql -U postgres -d verdejar -f /consultas.sql
```
 
## Estratégia de idempotência
 
Antes de carregar, o ETL esvazia as quatro tabelas com `TRUNCATE itens_pedido, pedidos, clientes, produtos` e carrega tudo de novo, dentro de uma única transação (se algo falhar no meio, nada é gravado e os dados anteriores continuam no banco).
 
Escolhi essa estratégia porque o ETL sempre traz todos os dados da fonte, e assim o banco fica sempre igual à fonte, inclusive se algum dado mudar. A alternativa de inserir ignorando os ids já existentes deixaria no banco valores desatualizados quando um registro mudasse na fonte.
 
Todas as inserções usam parâmetros (`%s`), sem montar SQL concatenando texto com os dados. A ordem de carga respeita as chaves estrangeiras: produtos, clientes, pedidos e itens_pedido.
 
## Decisões de transformação
 
- Os pedidos repetidos são removidos **antes** das conversões, mantendo a primeira ocorrência. Por isso, os contadores de datas e de valores convertidos se referem apenas aos 5000 pedidos únicos.
- `valores_convertidos` conta apenas os valores que vieram como texto com vírgula.
- Datas: `DD/MM/AAAA` é convertida para `AAAA-MM-DD`; `AAAA-MM-DD` é mantida; qualquer outro formato gera erro.
- A divergência considera a diferença entre `valor_total` e `valor_itens` para mais ou para menos, maior que um centavo.
- Na consulta de vendas por mês, os pedidos com status `cancelado` não são contados como venda.

As regras de cada campo estão no `CONTRATO_DE_DADOS.md`.
 
## Saída do ETL
 
Duas execuções seguidas de `python -m etl.main` (24/11/2026), com as mesmas contagens (idempotência):
 
```
extracao: clientes paginas=5 registros=1000
extracao: pedidos paginas=26 registros_brutos=5100
extracao: produtos registros=12
extracao: bruto salvo em brutos\clientes.json registros=1000
extracao: bruto salvo em brutos\pedidos.json registros=5100
extracao: bruto salvo em brutos\produtos.json registros=12
transformacao: pedidos_unicos=5000 repetidos_descartados=100
transformacao: emails_nulos=81 estados_padronizados=151 datas_convertidas=1037 valores_convertidos=1255
divergentes: 238 pedidos com valor_total diferente da soma dos itens
carga: clientes=1000 produtos=12 pedidos=5000 itens=12455
```
 
```
extracao: clientes paginas=5 registros=1000
extracao: pedidos paginas=26 registros_brutos=5100
extracao: produtos registros=12
extracao: bruto salvo em brutos\clientes.json registros=1000
extracao: bruto salvo em brutos\pedidos.json registros=5100
extracao: bruto salvo em brutos\produtos.json registros=12
transformacao: pedidos_unicos=5000 repetidos_descartados=100
transformacao: emails_nulos=81 estados_padronizados=151 datas_convertidas=1037 valores_convertidos=1255
divergentes: 238 pedidos com valor_total diferente da soma dos itens
carga: clientes=1000 produtos=12 pedidos=5000 itens=12455
```
 
Depois que a reconciliação foi incluída no ETL (25/11/2026), a execução passou a terminar com:
 
```
carga: clientes=1000 produtos=12 pedidos=5000 itens=12455
reconciliacao: soma_valor_itens_origem=311228.75 soma_valor_itens_destino=311228.75 diferenca=0.00
```
 
**Conferências:** os 81 e-mails nulos e os 151 estados em minúsculas batem com uma busca manual nos dados brutos; os 100 repetidos e os cerca de 5% de divergentes batem com o que o `gerar_dados.py` descreve.
 
---
 
## Consultas de validação
 
### (a) Total de vendas por mês (soma de valor_total, sem pedidos cancelados)
 
```
    mes     | valor_mensal
------------+--------------
 2026-01-01 |     24319.65
 2026-02-01 |     26861.74
 2026-03-01 |     23476.23
 2026-04-01 |     24747.39
 2026-05-01 |     24920.16
 2026-06-01 |     24946.33
 2026-07-01 |     26176.25
 2026-08-01 |     24331.32
 2026-09-01 |     24314.68
 2026-10-01 |     23990.57
(10 rows)
```
 
**Teste de consulta:** a soma dos meses é igual à soma geral da tabela, com o mesmo filtro.
 
```
 soma_dos_meses
----------------
      248084.32
(1 row)
 
 soma_geral
------------
  248084.32
(1 row)
```
 
### (b) Quantidade de pedidos por estado
 
```
 estado | quantidade_pedidos
--------+--------------------
 MG     |                476
 PR     |                974
 RS     |               1543
 SC     |               1127
 SP     |                880
(5 rows)
```
 
### (c) Pedidos divergentes
 
```
 total_divergentes
-------------------
               238
(1 row)
```
 
Primeiras 10 linhas da consulta:
 
```
  id  | valor_total | valor_itens
------+-------------+-------------
    1 |      125.84 |      130.84
   51 |       26.58 |       23.58
   71 |      144.35 |      134.35
   81 |       -1.84 |        3.16
  106 |       47.78 |       44.78
  176 |      137.69 |      134.69
  186 |      143.51 |      133.51
  289 |       79.40 |       76.40
  303 |      120.25 |      110.25
  326 |       10.58 |        7.58
```
 
<details>
<summary>Clique para ver a lista completa dos 238 pedidos divergentes</summary>

```
  id  | valor_total | valor_itens
------+-------------+-------------
    1 |      125.84 |      130.84
   51 |       26.58 |       23.58
   71 |      144.35 |      134.35
   81 |       -1.84 |        3.16
  106 |       47.78 |       44.78
  176 |      137.69 |      134.69
  186 |      143.51 |      133.51
  289 |       79.40 |       76.40
  303 |      120.25 |      110.25
  326 |       10.58 |        7.58
  335 |       89.80 |       79.80
  381 |      135.93 |      140.93
  427 |       13.25 |        3.25
  433 |       63.49 |       60.49
  436 |       31.15 |       28.15
  475 |      213.04 |      210.04
  483 |       82.23 |       87.23
  498 |       50.19 |       47.19
  522 |       66.25 |       56.25
  523 |       78.38 |       75.38
  558 |       18.87 |       15.87
  565 |      151.23 |      141.23
  582 |      151.65 |      141.65
  586 |       26.53 |       31.53
  587 |       57.97 |       47.97
  630 |       69.20 |       74.20
  639 |       70.37 |       60.37
  742 |       90.50 |       95.50
  752 |      155.60 |      152.60
  759 |       24.01 |       14.01
  791 |       35.10 |       25.10
  803 |        7.17 |       12.17
  804 |      185.80 |      182.80
  841 |       57.07 |       62.07
  863 |       74.83 |       71.83
  896 |       11.05 |       16.05
  932 |        2.26 |        7.26
  940 |       50.26 |       47.26
  961 |       75.23 |       65.23
  989 |       30.65 |       20.65
 1021 |      126.11 |      131.11
 1034 |       34.45 |       31.45
 1042 |       36.15 |       41.15
 1059 |       68.41 |       58.41
 1084 |       72.37 |       62.37
 1087 |       47.11 |       52.11
 1091 |       50.30 |       40.30
 1094 |        5.89 |       10.89
 1132 |       45.94 |       50.94
 1142 |      142.90 |      132.90
 1158 |      163.00 |      168.00
 1162 |       77.55 |       67.55
 1172 |       56.56 |       46.56
 1202 |       78.33 |       75.33
 1212 |       53.21 |       43.21
 1244 |       36.72 |       33.72
 1260 |       79.84 |       69.84
 1263 |       17.22 |       14.22
 1278 |       18.25 |       23.25
 1288 |      181.79 |      171.79
 1296 |       55.98 |       45.98
 1310 |       87.34 |       77.34
 1344 |       75.88 |       72.88
 1384 |       46.50 |       36.50
 1388 |      132.51 |      137.51
 1429 |      111.89 |      108.89
 1451 |       24.50 |       14.50
 1453 |       25.20 |       22.20
 1471 |       15.46 |       20.46
 1494 |       52.99 |       49.99
 1497 |       55.32 |       52.32
 1527 |       98.82 |      103.82
 1538 |       88.16 |       78.16
 1556 |       22.16 |       12.16
 1569 |       28.06 |       25.06
 1615 |       33.77 |       38.77
 1635 |      107.72 |       97.72
 1637 |       62.34 |       67.34
 1640 |       55.42 |       52.42
 1668 |       39.47 |       36.47
 1673 |       74.32 |       71.32
 1678 |       31.05 |       21.05
 1703 |       43.50 |       33.50
 1710 |      131.78 |      121.78
 1719 |      141.18 |      146.18
 1733 |       41.03 |       46.03
 1756 |        8.78 |       13.78
 1776 |       49.51 |       54.51
 1781 |       68.30 |       65.30
 1946 |       57.90 |       54.90
 1976 |       60.45 |       50.45
 2024 |       44.41 |       41.41
 2103 |       37.27 |       34.27
 2141 |      186.68 |      183.68
 2151 |       74.51 |       64.51
 2161 |       62.76 |       67.76
 2173 |       61.03 |       51.03
 2182 |       40.38 |       30.38
 2214 |      110.16 |      107.16
 2261 |       59.55 |       56.55
 2278 |       69.09 |       66.09
 2287 |      148.68 |      138.68
 2288 |       39.42 |       44.42
 2312 |       53.00 |       58.00
 2331 |      100.14 |       90.14
 2336 |       44.20 |       41.20
 2337 |       39.64 |       29.64
 2348 |       75.12 |       72.12
 2389 |       71.92 |       61.92
 2393 |      193.72 |      190.72
 2402 |       33.99 |       30.99
 2424 |       44.67 |       41.67
 2428 |       45.92 |       50.92
 2430 |       95.02 |       92.02
 2459 |       44.98 |       34.98
 2500 |      116.85 |      121.85
 2521 |       55.05 |       60.05
 2536 |      113.58 |      103.58
 2542 |       73.94 |       70.94
 2559 |      114.95 |      119.95
 2560 |       26.68 |       31.68
 2563 |        9.70 |       14.70
 2595 |       47.12 |       44.12
 2599 |       47.83 |       52.83
 2606 |       66.03 |       63.03
 2617 |       59.45 |       64.45
 2620 |       30.72 |       27.72
 2621 |       45.40 |       42.40
 2657 |       81.52 |       78.52
 2695 |      106.00 |       96.00
 2700 |       21.29 |       26.29
 2731 |       98.51 |       88.51
 2732 |       20.67 |       10.67
 2745 |       92.73 |       89.73
 2751 |       65.05 |       62.05
 2780 |       53.04 |       58.04
 2822 |       68.77 |       65.77
 2844 |       42.65 |       47.65
 2846 |       64.14 |       61.14
 2848 |       13.38 |        3.38
 2879 |      109.97 |      106.97
 2885 |      101.15 |       91.15
 2928 |        6.79 |        3.79
 2946 |      154.05 |      151.05
 2950 |       50.67 |       47.67
 2970 |       68.38 |       73.38
 2993 |       55.96 |       60.96
 3111 |       37.74 |       42.74
 3119 |       31.36 |       36.36
 3185 |       90.65 |       87.65
 3218 |      139.80 |      129.80
 3223 |       50.81 |       55.81
 3246 |       66.16 |       56.16
 3248 |       13.66 |       10.66
 3258 |      104.83 |       94.83
 3317 |      118.39 |      123.39
 3321 |      118.34 |      108.34
 3333 |      124.55 |      121.55
 3365 |       38.85 |       35.85
 3428 |       55.27 |       45.27
 3429 |       63.54 |       68.54
 3439 |       36.68 |       26.68
 3455 |       99.37 |      104.37
 3472 |       37.96 |       42.96
 3483 |      127.05 |      124.05
 3492 |       47.66 |       37.66
 3493 |       99.22 |       89.22
 3497 |       63.52 |       53.52
 3521 |        9.88 |        6.88
 3537 |       58.94 |       48.94
 3538 |       62.76 |       59.76
 3545 |       92.42 |       89.42
 3559 |       43.21 |       33.21
 3579 |       52.00 |       42.00
 3586 |       95.54 |      100.54
 3592 |       47.80 |       44.80
 3594 |      106.07 |      103.07
 3624 |       48.18 |       45.18
 3630 |       15.48 |       20.48
 3650 |       16.36 |       13.36
 3701 |       40.48 |       30.48
 3734 |       60.31 |       50.31
 3760 |       97.93 |      102.93
 3783 |      122.52 |      119.52
 3816 |       52.30 |       42.30
 3905 |       56.62 |       46.62
 3913 |      123.85 |      113.85
 3916 |       58.53 |       48.53
 3919 |       17.38 |        7.38
 3930 |       52.52 |       49.52
 3969 |       91.46 |       88.46
 3988 |       38.01 |       35.01
 4003 |        6.52 |       11.52
 4027 |       71.11 |       68.11
 4093 |       27.14 |       32.14
 4111 |       40.80 |       37.80
 4112 |       37.56 |       27.56
 4207 |        7.19 |        4.19
 4238 |       53.98 |       58.98
 4242 |       44.85 |       34.85
 4273 |      116.23 |      106.23
 4287 |       67.46 |       57.46
 4313 |       43.97 |       40.97
 4327 |       14.63 |       11.63
 4345 |       61.22 |       58.22
 4354 |       34.44 |       31.44
 4358 |       63.36 |       60.36
 4365 |       76.79 |       81.79
 4371 |      102.73 |       92.73
 4397 |       85.84 |       75.84
 4405 |       51.67 |       41.67
 4476 |      159.88 |      164.88
 4520 |       87.28 |       77.28
 4557 |       33.68 |       30.68
 4560 |       36.30 |       26.30
 4566 |        9.89 |        6.89
 4567 |       48.96 |       38.96
 4570 |      104.31 |      101.31
 4602 |       15.64 |       12.64
 4620 |       60.68 |       57.68
 4632 |      142.24 |      132.24
 4640 |       61.03 |       51.03
 4682 |       35.92 |       25.92
 4686 |       14.59 |       11.59
 4713 |       14.80 |       19.80
 4742 |       76.05 |       66.05
 4820 |       59.36 |       64.36
 4825 |       57.62 |       47.62
 4849 |       60.69 |       50.69
 4868 |       79.95 |       69.95
 4883 |       12.40 |       17.40
 4917 |       91.77 |       81.77
 4918 |       10.24 |        7.24
 4921 |       40.10 |       37.10
 4922 |      120.25 |      125.25
 4980 |       52.50 |       57.50
 4983 |       71.18 |       61.18
 5000 |       18.88 |        8.88
(238 rows)
```
 
</details>

---

## Testes
 
```
collected 21 items
 
tests/test_reconciliacao.py::test_reconciliacao_contagem_e_soma_de_valor_itens PASSED                         [  4%]
tests/test_transformacao.py::test_email_ausente_retorna_true PASSED                                           [  9%]
tests/test_transformacao.py::test_email_presente_retorna_false PASSED                                         [ 14%]
tests/test_transformacao.py::test_estado_minusculo_vira_maiusculo PASSED                                      [ 19%]
tests/test_transformacao.py::test_estado_maiusculo_permanece PASSED                                           [ 23%]
tests/test_transformacao.py::test_valor_com_virgula_vira_numero PASSED                                        [ 28%]
tests/test_transformacao.py::test_valor_numerico_permanece PASSED                                             [ 33%]
tests/test_transformacao.py::test_data_dd_mm_aaaa_vira_aaaa_mm_dd PASSED                                      [ 38%]
tests/test_transformacao.py::test_data_nao_troca_dia_com_mes PASSED                                           [ 42%]
tests/test_transformacao.py::test_data_com_um_digito_recebe_zero PASSED                                       [ 47%]
tests/test_transformacao.py::test_data_formato_mes_dia_ano_gera_erro PASSED                                   [ 52%]
tests/test_transformacao.py::test_data_ano_mes_dia_permanece PASSED                                           [ 57%]
tests/test_transformacao.py::test_data_invalida_gera_erro PASSED                                              [ 61%]
tests/test_transformacao.py::test_id_repetido_sera_removido PASSED                                            [ 66%]
tests/test_transformacao.py::test_id_unico_permanece PASSED                                                   [ 71%]
tests/test_transformacao.py::test_mantem_primeira_ocorrencia_em_id_repetido PASSED                            [ 76%]
tests/test_transformacao.py::test_valor_itens_calculado PASSED                                                [ 80%]
tests/test_transformacao.py::test_valor_total_igual_valor_itens_divergente_retorna_false PASSED               [ 85%]
tests/test_transformacao.py::test_valor_total_maior_que_valor_itens_divergente_retorna_true PASSED            [ 90%]
tests/test_transformacao.py::test_valor_total_menor_que_valor_itens_divergente_retorna_true PASSED            [ 95%]
tests/test_transformacao.py::test_diferenca_igual_um_centavo_divergente_retorna_false PASSED                  [100%]
 
================================================ 21 passed in 1.08s ================================================
```
 
