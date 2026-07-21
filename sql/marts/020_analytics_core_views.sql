create or replace view analytics.dim_brand as
select
    brand_id,
    brand_name
from staging.stg_brands;

create or replace view analytics.dim_category as
select
    category_id,
    category_name
from staging.stg_categories;

create or replace view analytics.dim_customer as
select
    customer_id,
    first_name,
    last_name,
    customer_name,
    phone,
    email,
    street,
    city,
    state,
    zip_code
from staging.stg_customers;

create or replace view analytics.dim_store as
select
    store_id,
    store_name,
    phone,
    email,
    street,
    city,
    state,
    zip_code
from staging.stg_stores;

create or replace view analytics.dim_product as
select
    p.product_id,
    p.product_name,
    p.brand_id,
    b.brand_name,
    p.category_id,
    c.category_name,
    p.model_year,
    p.list_price
from staging.stg_products p
left join staging.stg_brands b
    on p.brand_id = b.brand_id
left join staging.stg_categories c
    on p.category_id = c.category_id;

create or replace view analytics.dim_staff as
select
    s.staff_id,
    s.first_name,
    s.last_name,
    s.staff_name,
    s.email,
    s.phone,
    s.active,
    s.is_active,
    s.store_id,
    st.store_name,
    s.manager_id,
    m.staff_name as manager_name
from staging.stg_staffs s
left join staging.stg_stores st
    on s.store_id = st.store_id
left join staging.stg_staffs m
    on s.manager_id = m.staff_id;

create or replace view analytics.dim_date as
with bounds as (
    select
        min(order_date)::date as start_date,
        greatest(max(order_date), max(required_date), max(shipped_date))::date as end_date
    from staging.stg_orders
),
dates as (
    select generate_series(start_date, end_date, interval '1 day')::date as date_day
    from bounds
)
select
    date_day,
    extract(year from date_day)::integer as year,
    extract(quarter from date_day)::integer as quarter,
    extract(month from date_day)::integer as month,
    to_char(date_day, 'YYYY-MM') as year_month,
    extract(day from date_day)::integer as day_of_month,
    extract(isodow from date_day)::integer as day_of_week,
    to_char(date_day, 'Dy') as day_name,
    (extract(isodow from date_day) in (6, 7)) as is_weekend
from dates;

create or replace view analytics.fact_sales as
select
    concat(oi.order_id::text, '-', oi.item_id::text) as order_item_key,
    o.order_id,
    oi.item_id,
    o.customer_id,
    o.store_id,
    o.staff_id,
    oi.product_id,
    o.order_status,
    o.order_status_label,
    o.order_date,
    o.required_date,
    o.shipped_date,
    o.days_to_ship,
    o.is_late_shipment,
    oi.quantity,
    oi.list_price,
    oi.discount,
    oi.gross_sales,
    oi.discount_amount,
    oi.revenue
from staging.stg_orders o
inner join staging.stg_order_items oi
    on o.order_id = oi.order_id;

create or replace view analytics.fact_inventory as
select
    s.store_id,
    s.product_id,
    s.quantity as stock_quantity,
    p.list_price,
    (s.quantity::numeric * p.list_price) as inventory_value
from staging.stg_stocks s
left join staging.stg_products p
    on s.product_id = p.product_id;
