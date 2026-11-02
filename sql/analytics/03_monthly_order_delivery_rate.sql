-- Monthly order completion and sales value analyses.
-- Both queries return one row per purchase month, using the recorded order status.
-- Confirmed orders: approved, processing, invoiced, shipped, delivered.
-- Completed orders: delivered only; other confirmed statuses do not imply failure.
-- Query 1: confirmed and delivered order counts, plus the delivered percentage
-- of confirmed orders, rounded to a whole percentage point. No confirmed orders
-- means a NULL rate, while confirmed orders with no deliveries produce 0%.
-- Query 2: product value, freight, and their combined value for confirmed and
-- delivered orders. Items are aggregated by order before joining to avoid fanout.
-- Orders without items remain in the join with NULL item totals. SUM ignores
-- NULL values and returns NULL when there are no non-NULL values to aggregate.
-- These are order values, not recognized company revenue. Recent purchase months
-- may have incomplete coverage or less time for delivery; interpret comparisons
-- accordingly.

WITH monthly_orders AS (
    SELECT
        date_trunc('month', order_purchase_timestamp) AS purchase_month,
        COUNT(*) FILTER (
        WHERE order_status IN ('approved', 'processing', 'invoiced', 'shipped', 'delivered')
        ) AS confirmed_orders,
        COUNT (*) FILTER (
            WHERE order_status = 'delivered'
        ) AS delivered_orders
    FROM
        staging.orders
    GROUP BY
        purchase_month
)
SELECT
    purchase_month,
    confirmed_orders,
    delivered_orders,
    ROUND(delivered_orders::numeric / NULLIF(confirmed_orders::numeric, 0) * 100) AS delivered_rate_pct
FROM
    monthly_orders
ORDER BY purchase_month;

WITH items_by_order AS (
    SELECT
        oi.order_id,
        SUM(oi.price) AS total_price,
        SUM(oi.freight_value) AS total_freight
    FROM staging.order_items AS oi
    GROUP BY
        oi.order_id
), total_monthly AS (
    SELECT
        date_trunc('month', o.order_purchase_timestamp) AS purchase_month,
        SUM(i.total_price) FILTER(
            WHERE o.order_status IN ('approved', 'processing', 'invoiced', 'shipped', 'delivered')
        ) AS confirmed_orders_total_price,
        SUM(i.total_freight) FILTER(
            WHERE o.order_status IN ('approved', 'processing', 'invoiced', 'shipped', 'delivered')
        ) AS confirmed_orders_total_freight,
        SUM(i.total_price) FILTER(
            WHERE o.order_status = 'delivered'
        ) AS delivered_orders_total_price,
        SUM(i.total_freight) FILTER(
            WHERE o.order_status = 'delivered'
        ) AS delivered_orders_total_freight
    FROM staging.orders AS o
    LEFT JOIN items_by_order AS i
        ON o.order_id = i.order_id
    GROUP BY
        purchase_month
)
SELECT
    tm.purchase_month,
    tm.confirmed_orders_total_price,
    tm.confirmed_orders_total_freight,
    tm.confirmed_orders_total_price + tm.confirmed_orders_total_freight AS confirmed_orders_total,
    tm.delivered_orders_total_price,
    tm.delivered_orders_total_freight,
    tm.delivered_orders_total_price + tm.delivered_orders_total_freight AS delivered_orders_total
FROM total_monthly AS tm
ORDER BY tm.purchase_month DESC;

