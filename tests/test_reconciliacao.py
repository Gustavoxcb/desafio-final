from etl.extracao import carregar_bruto
from etl.transformacao import transformar_pedidos
from etl.carga import reconciliar


def test_reconciliacao_contagem_e_soma_de_valor_itens():
    pedidos, contadores = transformar_pedidos(carregar_bruto("pedidos"))
    contagem_origem, contagem_destino, soma_origem, soma_destino = reconciliar(pedidos)
    assert contagem_origem == contagem_destino
    assert abs(soma_origem - soma_destino) <= 0.01