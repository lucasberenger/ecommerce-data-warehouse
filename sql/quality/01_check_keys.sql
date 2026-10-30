-- check: customers_null_id
SELECT 
    *
FROM staging.customers AS c
WHERE c.customer_id IS NULL;

-- check: customers_duplicate_id
SELECT
    c.customer_id,
    COUNT(*) AS quantity
FROM staging.customers AS c 
GROUP BY 
    c.customer_id
HAVING COUNT(*) > 1;

-- check: orders_null_id
SELECT *
FROM staging.orders AS o
WHERE o.order_id IS NULL;

-- check: orders_duplicate_id
SELECT 
    o.order_id,
    COUNT(*) AS quantity
FROM staging.orders AS o 
GROUP BY o.order_id
HAVING COUNT(*) > 1;

-- check: products_null_id
SELECT *
FROM staging.products AS p
WHERE p.product_id IS NULL;

-- check: products_duplicate_id
SELECT 
    p.product_id,
    COUNT(*) AS quantity
FROM staging.products AS p
GROUP BY p.product_id
HAVING COUNT(*) > 1;

-- check: order_items_null_key
SELECT *
FROM staging.order_items AS o
WHERE o.order_id IS NULL OR o.order_item_id IS NULL; 

-- check: order_items_duplicate_key
SELECT 
    o.order_item_id AS item_id,
    o.order_id,
    COUNT(*) AS quantity
FROM staging.order_items AS o
GROUP BY 
    o.order_item_id,
    o.order_id
HAVING COUNT(*) > 1;

-- check: payments_null_key
SELECT *
FROM staging.payments AS p
WHERE p.order_id IS NULL OR p.payment_sequential IS NULL;

-- check: payments_duplicate_key
SELECT
    p.order_id,
    p.payment_sequential,
    COUNT(*) AS quantity
FROM staging.payments AS p 
GROUP BY 
    p.order_id,
    p.payment_sequential
HAVING COUNT(*) > 1;



