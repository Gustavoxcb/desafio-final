from etl.extracao import executar_extracao
from etl.transformacao import executar_transformacao
from etl.carga import executar_carga


def main():
    if not executar_extracao():
        print("etl interrompido: a extracao falhou")
        return
    produtos, clientes, pedidos, itens = executar_transformacao()
    executar_carga(produtos, clientes, pedidos, itens)


if __name__ == "__main__":
    main()