# Contrato de dados

- Fontes: API Verdejar (rotas /clientes e /pedidos) e arquivo produtos.csv.
- Destino: PostgreSQL, conforme insumos_verdejar/schema.sql.

## Regras gerais

- Remover os repetidos de mesmo id antes das conversões. 
- Manter a primeira ocorrência dos repetidos.
- Quando um pedido é descartado os seus itens também são.
- Os contadores são calculados depois de remover os repetidos.
- Os produtos chegam como texto e são convertidos aqui.
- Todos os valores em dinheiro terão 2 casas decimais.

## Tabela clientes

| Campo | Tipo | Pode ser nulo? | Origem | Regra de transformação |
|---|---|---|---|---|
| id | Inteiro | Não | API /clientes, campo id | Mantém sem transformação |
| nome | Texto | Não | API /clientes, campo nome | Mantém sem transformação |
| email | Texto | Sim | API /clientes, campo email | Mantém cliente, grava os emails de valor nulo como nulo e conta. Armadilha A1. |
| cidade | Texto | Não | API /clientes, campo cidade | Mantém sem transformação |
| estado | Texto de 2 letras | Não | API /clientes, campo estado | Converte sempre para maiúsculas. Conta quantos foram alterados. Armadilha A2.|
| cadastro_em | Data | Não | API /clientes, campo cadastro_em | Está no formato adequado AAAA-MM-DD. Mantém sem transformação |

## Tabela produtos

| Campo | Tipo | Pode ser nulo? | Origem | Regra de transformação |
|---|---|---|---|---|
| produto_id | Inteiro | Não | produtos.csv, coluna produto_id (lida como texto) | Converte de texto para inteiro |
| nome | Texto | Não | produtos.csv, coluna nome | Mantém sem transformação |
| categoria | Texto | Não | produtos.csv, coluna categoria | Mantém sem transformação |
| preco_base | Decimal com duas casas (NUMERIC(10,2)) | Não | produtos.csv, coluna preco_base (lida como texto) | Converte de texto para decimal com duas casas |

## Tabela pedidos

| Campo | Tipo | Pode ser nulo? | Origem | Regra de transformação |
|---|---|---|---|---|
| id | Inteiro | Não | API /pedidos, campo id | Remove os pedidos de mesmo id, mantém a primeira ocorrência e conta os descartados. Armadilha A5 |
| cliente_id | Inteiro | Não | API /pedidos, campo cliente_id | Mantém sem transformação |
| data_pedido | Data | Não | API /pedidos, campo data_pedido | Recebe dois formatos: AAAA-MM-DD que será mantido e DD/MM/AAAA que será convertido para AAAA-MM-DD. Conta as datas convertidas. Dia e mês com um dígito recebem zero à esquerda. Outros formatos geram erro. Armadilha A3 |
| status | Texto | Não | API /pedidos, campo status | Mantém sem transformação |
| valor_total | Decimal com duas casas (NUMERIC(12,2)) | Não | API /pedidos, campo valor_total | Recebe dois formatos, um já é numero e outro que está em texto com virgula decimal. Mantém o caso onde é número e converte o caso onde é texto para número, ambos com duas casas decimais. Conta somente o formato que era texto. Armadilha A4 |
| valor_itens | Decimal com duas casas (NUMERIC(12,2)) | Não | Calculado a partir dos itens do pedido | Faz a soma de quantidade × preco_unitario de todos os itens do pedido, arredondando para 2 casas decimais. Armadilha A6. |
| divergente | Booleano | Não | Compara o valor_total com valor_itens | Vira verdadeiro quando tiver diferença de preço, para mais ou para menos, maior que um centavo, e é falso por padrão. Conta a quantidade de verdadeiros. Armadilha A6. |

## Tabela itens_pedido

| Campo | Tipo | Pode ser nulo? | Origem | Regra de transformação |
|---|---|---|---|---|
| pedido_id | Inteiro | Não | id do pedido ao qual o item pertence | Recebe o id do pedido ao qual o item pertence |
| linha | Inteiro | Não | Gerado: posição do item dentro do pedido (1, 2, 3...) | Numera os itens de cada pedido na ordem em que aparecem a partir do número 1 e a contagem recomeça a cada pedido |
| produto_id | Inteiro | Não | API /pedidos, dentro de itens | Mantém sem transformação |
| quantidade | Inteiro | Não | API /pedidos, dentro de itens | Mantém sem transformação |
| preco_unitario | Decimal com duas casas (NUMERIC(10,2)) | Não | API /pedidos, dentro de itens | Mantém sem transformação |