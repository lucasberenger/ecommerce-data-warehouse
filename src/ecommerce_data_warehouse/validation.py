EXPECTED_COLUMNS = {
    "customers": {
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    },
    
     "orders": {
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    },

    "order_items": {
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    },

    "products": {
        "product_id",
        "product_category_name",
        "product_name_length",
        "product_description_length",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    },

    "payments": {
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    },
}


def validate_dataframe(df, table):
    expected = EXPECTED_COLUMNS[table]

    missing = expected - set(df.columns)

    if missing:
        raise ValueError(
            f"{table}: missing columns {missing}"
        )