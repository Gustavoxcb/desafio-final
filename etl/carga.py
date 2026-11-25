import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


def conectar():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORTA", "5432"),
        dbname=os.getenv("DB_NOME", "verdejar"),
        user=os.getenv("DB_USUARIO", "postgres"),
        password=os.getenv("DB_SENHA"),
    )

def limpar_tabelas(conexao):
    conexao.execute("TRUNCATE itens_pedido, pedidos, clientes, produtos")


def carregar_produtos(conexao, produtos):
    linhas = []
    for p in produtos:
        linhas.append((p["produto_id"], p["nome"], p["categoria"], p["preco_base"]))
    with conexao.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO produtos (produto_id, nome, categoria, preco_base) VALUES (%s, %s, %s, %s)",
            linhas,
        )


def carregar_clientes(conexao, clientes):
    linhas = []
    for c in clientes:
        linhas.append((c["id"], c["nome"], c["email"], c["cidade"], c["estado"], c["cadastro_em"]))
    with conexao.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO clientes (id, nome, email, cidade, estado, cadastro_em) VALUES (%s, %s, %s, %s, %s, %s)",
            linhas,
        )


def carregar_pedidos(conexao, pedidos):
    linhas = []
    for p in pedidos:
        linhas.append((p["id"], p["cliente_id"], p["data_pedido"], p["status"],
                       p["valor_total"], p["valor_itens"], p["divergente"]))
    with conexao.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO pedidos (id, cliente_id, data_pedido, status, valor_total, valor_itens, divergente) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            linhas,
        )


def carregar_itens(conexao, itens):
    linhas = []
    for i in itens:
        linhas.append((i["pedido_id"], i["linha"], i["produto_id"], i["quantidade"], i["preco_unitario"]))
    with conexao.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO itens_pedido (pedido_id, linha, produto_id, quantidade, preco_unitario) "
            "VALUES (%s, %s, %s, %s, %s)",
            linhas,
        )


def contar_registros(conexao):
    contagens = {}
    contagens["clientes"] = conexao.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    contagens["produtos"] = conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    contagens["pedidos"] = conexao.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    contagens["itens"] = conexao.execute("SELECT COUNT(*) FROM itens_pedido").fetchone()[0]
    return contagens


def executar_carga(produtos, clientes, pedidos, itens):
    with conectar() as conexao:
        limpar_tabelas(conexao)
        carregar_produtos(conexao, produtos)
        carregar_clientes(conexao, clientes)
        carregar_pedidos(conexao, pedidos)
        carregar_itens(conexao, itens)
        contagens = contar_registros(conexao)
    print(f"carga: clientes={contagens['clientes']} produtos={contagens['produtos']} "
          f"pedidos={contagens['pedidos']} itens={contagens['itens']}")
    return contagens

def reconciliar(pedidos):
    contagem_origem = len(pedidos)
    soma_origem = 0
    for p in pedidos:
        soma_origem += p["valor_itens"]
    soma_origem = round(soma_origem, 2)

    with conectar() as conexao:
        contagem_destino, soma_destino = conexao.execute(
            "SELECT COUNT(*), COALESCE(SUM(valor_itens), 0) FROM pedidos"
        ).fetchone()
    soma_destino = round(float(soma_destino), 2)

    diferenca = round(abs(soma_origem - soma_destino), 2)
    print(f"reconciliacao: soma_valor_itens_origem={soma_origem:.2f} "
          f"soma_valor_itens_destino={soma_destino:.2f} diferenca={diferenca:.2f}")
    return contagem_origem, contagem_destino, soma_origem, soma_destino