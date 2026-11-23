from etl.extracao import carregar_bruto

def padronizar_estado(cliente):
    novo_cliente = cliente.copy()  
    novo_cliente['estado'] = novo_cliente['estado'].upper()
    return novo_cliente

def converter_valor(valor):
    if isinstance(valor, str):
        valor = valor.replace(",", ".")
    valor = round(float(valor), 2)
    return valor

def converter_data(data):
    if isinstance(data, str) and "/" in data:
        partes = data.split("/")
        if len(partes) == 3:
            dia, mes, ano = partes
            return f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
        raise ValueError(f"data em formato inesperado: {data}")
    else:
        return data  

def remover_repetidos(pedidos):
    vistos = set()
    unicos = []
    for pedido in pedidos:
        if pedido["id"] in vistos:
            continue
        vistos.add(pedido["id"])
        unicos.append(pedido)
    descartados = len(pedidos) - len(unicos)
    return unicos, descartados

def calcular_valor_itens(itens):
    total = 0
    for item in itens:
        total += item["quantidade"] * item["preco_unitario"]
    return round(total, 2)
    
def eh_divergente(valor_total, valor_itens):
    diferenca = abs(valor_total - valor_itens)
    return round(diferenca, 2) > 0.01

def email_ausente(cliente):
    return cliente.get("email") is None

def transformar_clientes(clientes):
    lista_transformada = []
    emails_nulos = 0
    estados_padronizados = 0
    for cliente in clientes:
        if email_ausente(cliente):
            emails_nulos += 1
        novo_cliente = padronizar_estado(cliente)
        if novo_cliente["estado"] != cliente["estado"]:
            estados_padronizados += 1
        lista_transformada.append(novo_cliente)
    return lista_transformada, emails_nulos, estados_padronizados

def transformar_pedidos(pedidos):
    unicos, repetidos_descartados = remover_repetidos(pedidos)
    lista_transformada = []
    datas_convertidas = 0
    valores_convertidos = 0
    divergentes = 0
    for pedido in unicos:
        novo_pedido = pedido.copy()
        novo_pedido["data_pedido"] = converter_data(pedido["data_pedido"])
        if novo_pedido["data_pedido"] != pedido["data_pedido"]:
            datas_convertidas += 1
        if isinstance(pedido["valor_total"], str):
            valores_convertidos += 1
        novo_pedido["valor_total"] = converter_valor(pedido["valor_total"])
        novo_pedido["valor_itens"] = calcular_valor_itens(pedido["itens"])
        novo_pedido["divergente"] = eh_divergente(novo_pedido["valor_total"], novo_pedido["valor_itens"])
        if novo_pedido["divergente"]:
            divergentes += 1
        lista_transformada.append(novo_pedido)
    contadores = {
        "pedidos_unicos": len(lista_transformada),
        "repetidos_descartados": repetidos_descartados,
        "datas_convertidas": datas_convertidas,
        "valores_convertidos": valores_convertidos,
        "divergentes": divergentes,
    }
    return lista_transformada, contadores

def executar_transformacao():
    clientes = carregar_bruto("clientes")
    pedidos = carregar_bruto("pedidos")
    produtos = carregar_bruto("produtos")                                   
    clientes_transformados, emails_nulos, estados_padronizados = transformar_clientes(clientes)
    pedidos_transformados, contadores = transformar_pedidos(pedidos)
    produtos_transformados = transformar_produtos(produtos)                 
    itens = []                                                              
    for pedido in pedidos_transformados:                                    
        itens.extend(montar_itens(pedido["id"], pedido["itens"]))          
    print(f"transformacao: pedidos_unicos={contadores['pedidos_unicos']} repetidos_descartados={contadores['repetidos_descartados']}")
    print(f"transformacao: emails_nulos={emails_nulos} estados_padronizados={estados_padronizados} datas_convertidas={contadores['datas_convertidas']} valores_convertidos={contadores['valores_convertidos']}")
    print(f"divergentes: {contadores['divergentes']} pedidos com valor_total diferente da soma dos itens")
    return produtos_transformados, clientes_transformados, pedidos_transformados, itens   

def transformar_produtos(produtos):
    lista_transformada = []
    for produto in produtos:
        novo_produto = produto.copy()
        novo_produto["produto_id"] = int(novo_produto["produto_id"])
        novo_produto["preco_base"] = converter_valor(novo_produto["preco_base"])
        lista_transformada.append(novo_produto)
    return lista_transformada

def montar_itens(pedido_id, itens):
    lista_itens = []
    for i, item in enumerate(itens, start=1):
        novo_item = {
            "pedido_id": pedido_id,
            "linha": i,
            "produto_id": item["produto_id"],
            "quantidade": item["quantidade"],
            "preco_unitario": item["preco_unitario"]
        }
        lista_itens.append(novo_item)
    return lista_itens
