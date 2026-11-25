-- (a) total de vendas por mes (soma de valor_total, sem pedidos cancelados)
SELECT DATE_TRUNC('month', data_pedido)::date AS mes, SUM(valor_total) AS valor_mensal
FROM pedidos
WHERE status <> 'cancelado'
GROUP BY mes
ORDER BY mes;

-- (a) teste de consulta: a soma dos meses deve ser igual a soma geral
SELECT SUM(valor_mensal) AS soma_dos_meses FROM (
    SELECT DATE_TRUNC('month', data_pedido)::date AS mes, SUM(valor_total) AS valor_mensal
    FROM pedidos
    WHERE status <> 'cancelado'
    GROUP BY mes
) AS por_mes;

SELECT SUM(valor_total) AS soma_geral FROM pedidos WHERE status <> 'cancelado';

-- (b) quantidade de pedidos por estado
SELECT clientes.estado, COUNT(*) AS quantidade_pedidos
FROM pedidos
JOIN clientes ON pedidos.cliente_id = clientes.id
GROUP BY clientes.estado
ORDER BY clientes.estado;

-- (c) pedidos divergentes
SELECT id, valor_total, valor_itens
FROM pedidos
WHERE divergente = true
ORDER BY id;

SELECT COUNT(*) AS total_divergentes FROM pedidos WHERE divergente = true;