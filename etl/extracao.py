import csv
import json
import os
import urllib.error
import urllib.request

URL_BASE = "http://127.0.0.1:8000"
TAMANHO_PAGINA = 200
CAMINHO_PRODUTOS = "insumos_verdejar/dados/produtos.csv"
PASTA_BRUTOS = "brutos"


def buscar_pagina(rota, pagina, tamanho=TAMANHO_PAGINA):
    url = f"{URL_BASE}/{rota}?page={pagina}&page_size={tamanho}"
    with urllib.request.urlopen(url, timeout=10) as resposta:
        if resposta.status != 200:
            raise RuntimeError(f"status inesperado {resposta.status} em {url}")
        return json.loads(resposta.read().decode("utf-8"))


def extrair_rota(rota):
    try:
        primeira = buscar_pagina(rota, 1)
        total_paginas = primeira["total_pages"]
        itens = list(primeira["items"])
        for pagina in range(2, total_paginas + 1):
            resposta = buscar_pagina(rota, pagina)
            itens.extend(resposta["items"])
        return itens, total_paginas
    except urllib.error.HTTPError as erro:
        if erro.code == 404:
            print(f"erro: {rota}: rota ou pagina inexistente (HTTP 404)")
        else:
            print(f"erro: {rota}: a API respondeu com status HTTP {erro.code}")
    except urllib.error.URLError:
        print(f"erro: {rota}: nao foi possivel conectar a API em {URL_BASE}. Verifique se ela esta rodando.")
    except RuntimeError as erro:
        print(f"erro: {rota}: {erro}")
    return None, 0


def extrair_api():
    clientes, paginas_clientes = extrair_rota("clientes")
    pedidos, paginas_pedidos = extrair_rota("pedidos")
    if clientes is None or pedidos is None:
        print("extracao interrompida: corrija o problema acima e rode de novo")
        return None, None
    print(f"extracao: clientes paginas={paginas_clientes} registros={len(clientes)}")
    print(f"extracao: pedidos paginas={paginas_pedidos} registros_brutos={len(pedidos)}")
    return clientes, pedidos


def ler_produtos(caminho=CAMINHO_PRODUTOS):
    try:
        with open(caminho, encoding="utf-8", newline="") as arquivo:
            produtos = list(csv.DictReader(arquivo))
    except FileNotFoundError:
        print(f"erro: arquivo de produtos nao encontrado em {caminho}")
        return None
    print(f"extracao: produtos registros={len(produtos)}")
    return produtos


def salvar_bruto(nome, dados):
    os.makedirs(PASTA_BRUTOS, exist_ok=True)
    caminho = os.path.join(PASTA_BRUTOS, f"{nome}.json")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=1)
    print(f"extracao: bruto salvo em {caminho} registros={len(dados)}")


def carregar_bruto(nome):
    caminho = os.path.join(PASTA_BRUTOS, f"{nome}.json")
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        print(f"erro: arquivo bruto nao encontrado em {caminho}. Rode a extracao primeiro.")
        return None


def executar_extracao():
    clientes, pedidos = extrair_api()
    produtos = ler_produtos()
    if clientes is None or produtos is None:
        return False
    salvar_bruto("clientes", clientes)
    salvar_bruto("pedidos", pedidos)
    salvar_bruto("produtos", produtos)
    return True


if __name__ == "__main__":
    executar_extracao()