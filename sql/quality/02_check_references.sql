-- check any orphan reference

SELECT 
    o.customer_id AS order_customer_id,
    c.customer_id AS customer_customer_id,
    o.order_id AS order_id
FROM staging.orders AS o
LEFT JOIN staging.customers AS c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
ORDER BY o.customer_id;

SELECT
    oi.order_id AS order_items_order_id,
    o.order_id AS orders_order_id,
    oi.order_item_id AS order_items_item_id
FROM staging.order_items AS oi
LEFT JOIN staging.orders AS o
    ON oi.order_id = o.order_id
WHERE o.order_id IS NULL
ORDER BY oi.order_id;

SELECT
    oi.product_id AS order_items_product_id,
    p.product_id AS products_product_id,
    oi.order_id AS order_order_id
FROM staging.order_items AS oi
LEFT JOIN staging.products AS p
    ON oi.product_id = p.product_id
WHERE p.product_id IS NULL
ORDER BY oi.order_id;

SELECT
    p.order_id AS payments_order_id,
    o.order_id AS order_id,
    p.payment_sequential AS payment_id
FROM staging.payments AS p 
LEFT JOIN staging.orders AS o
    ON p.order_id = o.order_id
WHERE o.order_id IS NULL
ORDER BY p.order_id;