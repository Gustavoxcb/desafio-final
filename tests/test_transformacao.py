import pytest
from etl.transformacao import (
    email_ausente, padronizar_estado, converter_valor, converter_data,
    remover_repetidos, calcular_valor_itens, eh_divergente,
)

def test_email_ausente_retorna_true():
    cliente = {"id": 1, "nome": "Andre", "email": None}
    assert email_ausente(cliente) is True

def test_email_presente_retorna_false():
    cliente = {"id": 1, "nome": "Andre", "email": "andre@gmail.com"}
    assert email_ausente(cliente) is False


def test_estado_minusculo_vira_maiusculo():
    cliente = {"id": 1, "nome": "Andre", "estado": "sp"}
    cliente_padronizado = padronizar_estado(cliente)
    assert cliente_padronizado["estado"] == "SP"

def test_estado_maiusculo_permanece():
    cliente = {"id": 1, "nome": "Andre", "estado": "MS"}
    cliente_padronizado = padronizar_estado(cliente)
    assert cliente_padronizado["estado"] == "MS"


def test_valor_com_virgula_vira_numero():
    assert converter_valor("125,84") == 125.84

def test_valor_numerico_permanece():
    assert converter_valor(94.34) == 94.34


def test_data_dd_mm_aaaa_vira_aaaa_mm_dd():
    assert converter_data("15/08/2022") == "2022-08-15"

def test_data_nao_troca_dia_com_mes():
    assert converter_data("01/10/2026") == "2026-10-01"

def test_data_com_um_digito_recebe_zero():
    assert converter_data("6/6/2026") == "2026-06-06"

def test_data_formato_mes_dia_ano_gera_erro():
    with pytest.raises(ValueError):
        converter_data("12/31/2023")

def test_data_ano_mes_dia_permanece():
    assert converter_data("2023-12-31") == "2023-12-31"

def test_data_invalida_gera_erro():
    with pytest.raises(ValueError):
        converter_data("31-12-2023")
        

def test_id_repetido_sera_removido():
    pedidos = [
        {"id": 1, "cliente_id": 10},
        {"id": 2, "cliente_id": 11},
        {"id": 1, "cliente_id": 10},  
        {"id": 3, "cliente_id": 12},
    ]
    unicos, descartados = remover_repetidos(pedidos)
    assert len(unicos) == 3
    assert descartados == 1

def test_id_unico_permanece():
    pedidos = [
        {"id": 1, "cliente_id": 10},
        {"id": 2, "cliente_id": 11},
        {"id": 3, "cliente_id": 12},
    ]
    unicos, descartados = remover_repetidos(pedidos)
    assert len(unicos) == 3
    assert descartados == 0

def test_mantem_primeira_ocorrencia_em_id_repetido():
    pedidos = [
        {"id": 1, "cliente_id": 10},
        {"id": 2, "cliente_id": 11},
        {"id": 1, "cliente_id": 99},
        {"id": 3, "cliente_id": 12},
    ]
    unicos, descartados = remover_repetidos(pedidos)
    assert len(unicos) == 3
    assert descartados == 1
    assert unicos[0] == {"id": 1, "cliente_id": 10}
    assert {"id": 1, "cliente_id": 99} not in unicos


def test_valor_itens_calculado():
    itens = [
        {"quantidade": 4, "preco_unitario": 10.0},
        {"quantidade": 3, "preco_unitario": 6.0},
    ]
    assert calcular_valor_itens(itens) == 58.0

def test_valor_total_igual_valor_itens_divergente_retorna_false():
    assert eh_divergente(100.0, 100.0) is False

def test_valor_total_maior_que_valor_itens_divergente_retorna_true():
    assert eh_divergente(100.0, 99.98) is True

def test_valor_total_menor_que_valor_itens_divergente_retorna_true():
    assert eh_divergente(99.98, 100.0) is True

def test_diferenca_igual_um_centavo_divergente_retorna_false():
    assert eh_divergente(100.0, 99.99) is False

