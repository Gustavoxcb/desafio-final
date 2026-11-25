# Como usei a IA
 
**Ferramenta:** Claude (claude.ai), usado como par de programação e como tutor.
 
De forma geral, usei a IA para: explicar conceitos que eu não conhecia (API paginada, status HTTP, funções e parâmetros, try/except, testes com pytest, SQL); explicar a sintaxe de Python para eu escrever funções; revisar o meu código e o meu contrato de dados; e propor o código de partes mais técnicas (conexão com a API e com o banco, carga, reconciliação). Escrevi eu mesmo as funções das armadilhas A1, A2, A3 e A4, as funções transformar_clientes, transformar_produtos e montar_itens, o contrato de dados e os testes das armadilhas.
 
## Sugestões aceitas
 
### 1. Função `remover_repetidos` (Parte 2, armadilha A5)
 
- **O que pedi:** uma função que removesse os pedidos repetidos pelo id, mantendo a primeira ocorrência, e contasse os descartados.
- **O que a IA propôs:** percorrer os pedidos guardando os ids já vistos num `set`. Se o id já foi visto, o `continue` pula para o próximo; senão, o id é anotado e o pedido é guardado.
- **Por que aceitei:** é curta, eu entendi cada linha (funciona como uma lista de presença) e segue a regra do contrato de dados.
- **Como validei:** no terminal, ids `[1, 2, 1, 3]` resultaram em `[1, 2, 3]` com 1 descartado; com dois pedidos de mesmo id e conteúdo diferente, ficou o primeiro. Com os dados reais: 5000 únicos + 100 descartados = 5100, o que confere com o `gerar_dados.py` (5000 pedidos, 2% repetidos). Depois, transformei esses casos em testes no pytest.
### 2. Funções `calcular_valor_itens` e `eh_divergente` (Parte 2, armadilha A6)
 
- **O que pedi:** calcular `valor_itens` como a soma de quantidade × preço unitário e marcar `divergente` quando a diferença para `valor_total` fosse maior que um centavo.
- **O que a IA propôs:** somar os itens e arredondar para 2 casas; na divergência, usar `abs` na diferença e comparar `round(diferenca, 2) > 0.01`.
- **Por que aceitei:** o `abs` cobre a diferença "para mais ou para menos", um ponto que eu tinha encontrado na revisão do contrato usando o pedido 1 (total menor que a soma dos itens).
- **Como validei:** o pedido 1 deu `130.84`, igual à minha conta na calculadora. Fiz um experimento: `print(100.0 - 99.99)` mostra `0.010000000000005116`; tirei o `round` e o caso de exatamente 1 centavo passou a ser marcado como divergente (errado); com o `round`, voltou ao correto. No ETL, 238 divergentes (cerca de 4,8%, perto dos 5% do gerador). Esses casos viraram testes no pytest.
## Sugestões rejeitadas
 
### 1. Idempotência "ignorando o que já existe" (Parte 3)
 
- **O que pedi:** como garantir que rodar o ETL duas vezes não duplicasse os dados no banco.
- **O que a IA propôs:** duas estratégias: (A) limpar as tabelas com `TRUNCATE` e carregar tudo de novo; (B) inserir ignorando os ids que já existem.
- **Por que rejeitei a B:** num simulador, quando um dado mudava na fonte (a cidade de um cliente), a estratégia B mantinha o valor antigo no banco, porque o registro já existia e era pulado. Como o meu ETL sempre traz todos os dados de novo, o banco deve ficar igual à fonte.
- **O que fiz no lugar:** a estratégia A. Validei rodando `python -m etl.main` duas vezes seguidas: as contagens ficaram iguais (`clientes=1000 produtos=12 pedidos=5000 itens=12455`).
### 2. Converter os tipos já na leitura do CSV (Parte 1, item 3)
 
- **O que pedi:** ler o `produtos.csv` com o módulo `csv`.
- **O que a IA propôs:** duas opções: (A) manter os valores como texto e converter na transformação; (B) converter para número já na leitura.
- **Por que rejeitei a B:** o item 4 da Parte 1 pede guardar os dados brutos antes de qualquer transformação. Converter na leitura misturaria extração com transformação.
- **O que fiz no lugar:** os brutos ficam como texto (`'3.5'`) e a conversão acontece na função `transformar_produtos` (Parte 2). Validei vendo o `brutos/produtos.json` com texto e, depois da transformação, os valores como número (`3.5`).
### Outras decisões em que não segui a sugestão da IA
 
- **Caminho do banco:** a IA recomendou o caminho A (PostgreSQL instalado). Escolhi o caminho B (Docker), porque já tinha o Docker e o WSL e quis aprender a ferramenta.
- **Comando do Docker:** a IA sugeriu restringir a porta com `127.0.0.1:`. Preferi usar o comando oficial do documento.
- **Criação de arquivos:** a IA sugeriu criar o `COMO_USEI_IA.md` com um comando do PowerShell. Preferi criar pelo VS Code, porque eu não entendia o comando e o desafio não exige esse método.
## Falhas e retrabalho
 
### 1. Conflito de porta do banco (falha em sugestão da IA, Parte 3)
 
- **A falha:** a IA sugeriu subir o PostgreSQL do Docker na porta 5432 sem verificar se já existia um PostgreSQL instalado no meu Windows. Na hora de conectar pelo Python, deu erro de autenticação. As mensagens vinham em português, mas o PostgreSQL do Docker responde em inglês; e, usando a senha do pgAdmin, o erro mudava para "banco de dados verdejar não existe". Ou seja, o Python estava conectando no PostgreSQL do Windows, e não no do Docker.
- **O retrabalho:** recriei o contêiner na porta 5433 (`-p 5433:5432`), reapliquei o `schema.sql` e mudei `DB_PORTA` para 5433 no `.env` e no `.env.example`.
- **Como validei:** `SELECT COUNT(*) FROM clientes` respondeu `(0,)` e, depois, a carga completa funcionou.
### 2. Teste que falhou: data em formato inesperado (no meu código, Parte 4)
 
- **A falha:** o teste `test_data_invalida_gera_erro` falhou com `DID NOT RAISE ValueError`. A data `"31-12-2023"` (com hífen) passava pela minha função `converter_data` sem erro, porque ela só verificava datas com barra. O erro só apareceria no banco, na carga.
- **O retrabalho:** a IA apresentou duas opções (mudar o teste ou mudar a função). Escolhi mudar a função: agora toda data passa por `datetime.strptime(data, "%Y-%m-%d")`, que exige o formato AAAA-MM-DD. Atualizei o contrato ("Outros formatos geram erro").
- **Como validei:** o pytest passou e o ETL com os dados reais continuou com os mesmos números (`datas_convertidas=1037`).
### 3. Função de data devolvendo `None` (no meu código, Parte 2)
 
- **A falha:** na primeira versão da `converter_data`, uma data com barra mas incompleta (`"06/2026"`) fazia a função devolver `None` sem avisar, porque o `else` estava ligado ao `if` de fora. Depois, tentei corrigir com `return` de uma mensagem de erro, mas um teste mostrou que a mensagem virava a "data" que iria para o banco.
- **O retrabalho:** troquei por `raise ValueError(...)`, que interrompe e avisa. Aprendi a diferença entre devolver um resultado (`return`) e sinalizar um problema (`raise`).
 
