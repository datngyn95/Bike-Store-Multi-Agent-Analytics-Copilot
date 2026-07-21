create or replace view staging.stg_brands as
select
    brand_id::integer as brand_id,
    nullif(trim(brand_name), '') as brand_name
from raw.brands;

create or replace view staging.stg_categories as
select
    category_id::integer as category_id,
    nullif(trim(category_name), '') as category_name
from raw.categories;

create or replace view staging.stg_customers as
select
    customer_id::integer as customer_id,
    nullif(trim(first_name), '') as first_name,
    nullif(trim(last_name), '') as last_name,
    nullif(trim(concat_ws(' ', nullif(trim(first_name), ''), nullif(trim(last_name), ''))), '') as customer_name,
    nullif(trim(phone), '') as phone,
    lower(nullif(trim(email), '')) as email,
    nullif(trim(street), '') as street,
    nullif(trim(city), '') as city,
    upper(nullif(trim(state), '')) as state,
    nullif(trim(zip_code), '') as zip_code
from raw.customers;

create or replace view staging.stg_orders as
select
    order_id::integer as order_id,
    customer_id::integer as customer_id,
    order_status::integer as order_status,
    case order_status::integer
        when 1 then 'pending'
        when 2 then 'processing'
        when 3 then 'rejected'
        when 4 then 'completed'
        else 'unknown'
    end as order_status_label,
    order_date::date as order_date,
    required_date::date as required_date,
    shipped_date::date as shipped_date,
    store_id::integer as store_id,
    staff_id::integer as staff_id,
    case
        when shipped_date is null then null
        else (shipped_date::date - order_date::date)
    end as days_to_ship,
    case
        when shipped_date is null then null
        else (shipped_date::date > required_date::date)
    end as is_late_shipment
from raw.orders;

create or replace view staging.stg_order_items as
select
    order_id::integer as order_id,
    item_id::integer as item_id,
    product_id::integer as product_id,
    quantity::integer as quantity,
    list_price::numeric(12, 2) as list_price,
    discount::numeric(8, 4) as discount,
    (quantity::numeric * list_price::numeric) as gross_sales,
    (quantity::numeric * list_price::numeric * discount::numeric) as discount_amount,
    (quantity::numeric * list_price::numeric * (1 - discount::numeric)) as revenue
from raw.order_items;

create or replace view staging.stg_products as
select
    product_id::integer as product_id,
    nullif(trim(product_name), '') as product_name,
    brand_id::integer as brand_id,
    category_id::integer as category_id,
    model_year::integer as model_year,
    list_price::numeric(12, 2) as list_price
from raw.products;

create or replace view staging.stg_staffs as
select
    staff_id::integer as staff_id,
    nullif(trim(first_name), '') as first_name,
    nullif(trim(last_name), '') as last_name,
    nullif(trim(concat_ws(' ', nullif(trim(first_name), ''), nullif(trim(last_name), ''))), '') as staff_name,
    lower(nullif(trim(email), '')) as email,
    nullif(trim(phone), '') as phone,
    active::integer as active,
    (active::integer = 1) as is_active,
    store_id::integer as store_id,
    manager_id::integer as manager_id
from raw.staffs;

create or replace view staging.stg_stocks as
select
    store_id::integer as store_id,
    product_id::integer as product_id,
    quantity::integer as quantity
from raw.stocks;

create or replace view staging.stg_stores as
select
    store_id::integer as store_id,
    nullif(trim(store_name), '') as store_name,
    nullif(trim(phone), '') as phone,
    lower(nullif(trim(email), '')) as email,
    nullif(trim(street), '') as street,
    nullif(trim(city), '') as city,
    upper(nullif(trim(state), '')) as state,
    nullif(trim(zip_code), '') as zip_code
from raw.stores;
