-- Investigate simultaneous purchases before designing customer location history.
--
-- BUSINESS CONTEXT
-- We want to preserve the location recorded for each purchase. A person's
-- location may differ between purchases; this does not prove a residence change.
-- Before assigning time-based customer versions, check whether two different
-- locations can be observed for the same person at exactly the same timestamp.
--
-- BUSINESS QUESTIONS
-- 1. Does the same customer have more than one order at the same purchase timestamp?
--    Expected result: one row per customer_unique_id and purchase timestamp,
--    with the number of orders; show only groups with more than one order.
-- 2. Among those groups, are there different combinations of ZIP prefix, city,
--    and state? Repeated orders at the same location are not a location conflict.
-- 3. For conflicting groups, which order_id, customer_id, and location belong
--    to each purchase? These details will guide the dimension mapping decision.
--
-- EXAMPLE (illustrative, not an observed finding)
-- Person A | 2020-01-01 10:00:00 | order X | location 1
-- Person A | 2020-01-01 10:00:00 | order Y | location 1 -> simultaneous, no conflict
-- Person B | 2020-01-01 11:00:00 | order Z | location 1
-- Person B | 2020-01-01 11:00:00 | order W | location 2 -> location conflict
--
-- WHY THIS MATTERS
-- A location conflict means customer identity and time alone cannot determine
-- the correct version for an order. Location must also be considered in mapping.
-- No conflicts would support the simpler temporal mapping for the current data,
-- but would not guarantee that future inputs remain conflict-free.
--
-- IDENTIFIERS
-- customer_unique_id: groups purchases belonging to the same person.
-- customer_id: links an order to its recorded customer/location attributes.
-- order_id: uniquely identifies the order; grouping by it separates purchases
-- instead of bringing simultaneous purchases together.
--
-- NEXT QUESTIONS: CUSTOMER LOCATION HISTORY
-- 4. Which customers have purchases with different recorded locations over time?
--    Expected result: customer identity and number of distinct location combinations.
-- 5. In chronological order, when does each customer's recorded location differ
--    from the preceding purchase? Repeated purchases at the same location should
--    not create additional versions.
-- 6. Does a customer return to a previously observed location after purchasing
--    from another one? A -> B -> A represents three observed periods, not two.
-- 7. What purchase timestamp starts each observed period, and when does the next
--    period start? The agreed interval convention is [valid_from, valid_to),
--    with NULL valid_to and is_active = TRUE for the latest version.
-- 8. Can every order be associated with exactly one customer version whose
--    location matches the source purchase? Report missing and ambiguous matches.
-- 9. Are there overlapping periods or multiple active versions for a customer?
--    Any simultaneous-location conflict must be resolved before assuming that
--    timestamp alone is sufficient to assign versions.
-- Keep purchase-location observations distinct from actual residence history.
--
-- FOLLOWING BUSINESS ANALYSES (use separate files when implementing)
-- Monthly sales and order completion have initial queries in file 03.
-- The questions below extend that work; they are not implemented by this file.
--
-- SALES AND AVERAGE ORDER VALUE
-- 10. How do confirmed and delivered product values, freight, and combined order
--     values compare by purchase month?
-- 11. What is the average order value for each group: product value alone and
--     product value plus freight? How should eligible orders without items be
--     reported so that missing amounts are not silently treated as zero?
-- Agreed statuses: confirmed = approved, processing, invoiced, shipped, delivered;
-- completed = delivered. Both groups use purchase month, not delivery month.
--
-- PRODUCTS AND GEOGRAPHY
-- 12. Which categories contribute most to product sales, excluding freight?
-- 13. How do sales and order completion vary by the location recorded at purchase?
-- Pending definitions: which order group to use for each analysis and how to
-- report missing categories. Do not silently exclude unclassified products.
--
-- PAYMENTS
-- 14. How do payment amounts vary by payment method and installment count?
-- 15. How do payments reconcile with item prices plus freight at order level?
-- Pending definitions: eligible statuses and acceptable reconciliation differences.
-- An order can have multiple items and payments; joining their raw rows directly
-- can multiply amounts. Compare totals at a consistent order-level grain.
--
-- DELIVERY AND CUSTOMER BEHAVIOR
-- 16. Among delivered orders, how many arrived after the estimated delivery date,
--     and how does that rate vary by purchase month and purchase location?
--     Pending definitions: date versus timestamp comparison and missing dates.
-- 17. How many customers purchase again, and how long do they take to return?
--     Use customer_unique_id across purchases, not customer_id or dimension rows.
--     Pending definitions: eligible order statuses and the observation window.
-- 18. Which boundary months have insufficient coverage for fair comparisons?
--     An unfinished order in the recorded data is not proof of eventual failure.
--
-- Step 1: find customer_unique_id and order_purchase_timestamp combinations
-- with more than one order. Join orders and customers using customer_id.
-- Step 2: investigate whether those purchases have different locations.
-- Location attributes: ZIP code prefix, city, and state.
-- Multiple purchases at the same timestamp do not alone imply a location conflict.
-- This is an exploratory SELECT, not a dimension load or a schema change.

-- Relevant columns in staging.orders:
--   order_id TEXT
--   customer_id TEXT
--   order_purchase_timestamp TIMESTAMP
-- Relevant columns in staging.customers:
--   customer_id TEXT
--   customer_unique_id TEXT
--   customer_zip_code_prefix INTEGER
--   customer_city TEXT
--   customer_state CHAR(2)

WITH order_by_timestamp AS (
    SELECT
        order_id,
        customer_id,
        order_purchase_timestamp
    FROM staging.orders
    GROUP BY
        order_id,
        customer_id,
        order_purchase_timestamp
    ORDER BY
        order_purchase_timestamp DESC
)
SELECT
	*
FROM order_by_timestamp;
