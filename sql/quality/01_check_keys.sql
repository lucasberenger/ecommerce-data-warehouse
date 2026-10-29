-- customers: check for null customers ids
SELECT 
    *
FROM staging.customers AS c
WHERE c.customer_id IS NULL;

-- customers: check for duplicated customers ids
SELECT
    c.customer_id,
    COUNT(*) AS quantity
FROM staging.customers AS c 
GROUP BY 
    c.customer_id
HAVING COUNT(*) > 1;

-- orders: check for null orders ids
SELECT *
FROM staging.orders AS o
WHERE o.order_id IS NULL;

-- orders: check for duplicated orders ids
SELECT 
    o.order_id,
    COUNT(*) AS quantity
FROM staging.orders AS o 
GROUP BY o.order_id
HAVING COUNT(*) > 1;

-- products: check for null products ids
SELECT *
FROM staging.products AS p
WHERE p.product_id IS NULL;

-- products: check for duplicated products ids
SELECT 
    p.product_id,
    COUNT(*) AS quantity
FROM staging.products AS p
GROUP BY p.product_id
HAVING COUNT(*) > 1;

-- order items: check for null ids 
SELECT *
FROM staging.order_items AS o
WHERE o.order_id IS NULL OR o.order_item_id IS NULL; 

-- order items: check for duplicated ids
SELECT 
    o.order_item_id AS item_id,
    o.order_id,
    COUNT(*) AS quantity
FROM staging.order_items AS o
GROUP BY 
    o.order_item_id,
    o.order_id
HAVING COUNT(*) > 1;

-- payments: check for null ids
SELECT *
FROM staging.payments AS p
WHERE p.order_id IS NULL OR p.payment_sequential IS NULL;

-- payments: check for duplicated payment keys
SELECT
    p.order_id,
    p.payment_sequential,
    COUNT(*) AS quantity
FROM staging.payments AS p 
GROUP BY 
    p.order_id,
    p.payment_sequential
HAVING COUNT(*) > 1;



