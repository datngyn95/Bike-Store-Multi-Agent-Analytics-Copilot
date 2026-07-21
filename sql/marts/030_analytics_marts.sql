create or replace view analytics.mart_executive_summary as
select
    count(distinct order_id) as orders,
    count(*) as order_items,
    count(distinct customer_id) as customers_with_orders,
    count(distinct product_id) as products_sold,
    count(distinct store_id) as stores_with_orders,
    min(order_date) as first_order_date,
    max(order_date) as last_order_date,
    round(sum(revenue), 2) as revenue,
    sum(quantity) as units_sold,
    round(sum(revenue) / nullif(count(distinct order_id), 0), 2) as average_order_value,
    round(sum(discount_amount) / nullif(sum(gross_sales), 0), 4) as discount_rate,
    round(avg(days_to_ship) filter (where shipped_date is not null), 2) as avg_days_to_ship,
    round(avg(case when is_late_shipment then 1.0 else 0.0 end) filter (where shipped_date is not null), 4) as late_shipment_rate
from analytics.fact_sales;

create or replace view analytics.mart_sales_monthly as
select
    date_trunc('month', fs.order_date)::date as month,
    extract(year from fs.order_date)::integer as year,
    extract(month from fs.order_date)::integer as month_number,
    count(distinct fs.order_id) as orders,
    count(*) as order_items,
    count(distinct fs.customer_id) as customers,
    sum(fs.quantity) as units_sold,
    round(sum(fs.gross_sales), 2) as gross_sales,
    round(sum(fs.discount_amount), 2) as discount_amount,
    round(sum(fs.revenue), 2) as revenue,
    round(sum(fs.revenue) / nullif(count(distinct fs.order_id), 0), 2) as average_order_value,
    round(sum(fs.discount_amount) / nullif(sum(fs.gross_sales), 0), 4) as discount_rate
from analytics.fact_sales fs
group by 1, 2, 3;

create or replace view analytics.mart_sales_by_store as
select
    fs.store_id,
    ds.store_name,
    ds.city,
    ds.state,
    count(distinct fs.order_id) as orders,
    count(distinct fs.customer_id) as customers,
    sum(fs.quantity) as units_sold,
    round(sum(fs.revenue), 2) as revenue,
    round(sum(fs.revenue) / nullif(count(distinct fs.order_id), 0), 2) as average_order_value,
    round(avg(case when fs.is_late_shipment then 1.0 else 0.0 end) filter (where fs.shipped_date is not null), 4) as late_shipment_rate
from analytics.fact_sales fs
left join analytics.dim_store ds
    on fs.store_id = ds.store_id
group by fs.store_id, ds.store_name, ds.city, ds.state;

create or replace view analytics.mart_product_performance as
select
    fs.product_id,
    dp.product_name,
    dp.brand_id,
    dp.brand_name,
    dp.category_id,
    dp.category_name,
    dp.model_year,
    count(distinct fs.order_id) as orders,
    sum(fs.quantity) as units_sold,
    round(sum(fs.gross_sales), 2) as gross_sales,
    round(sum(fs.discount_amount), 2) as discount_amount,
    round(sum(fs.revenue), 2) as revenue,
    round(sum(fs.revenue) / nullif(sum(fs.quantity), 0), 2) as avg_selling_price,
    round(sum(fs.discount_amount) / nullif(sum(fs.gross_sales), 0), 4) as discount_rate
from analytics.fact_sales fs
left join analytics.dim_product dp
    on fs.product_id = dp.product_id
group by
    fs.product_id,
    dp.product_name,
    dp.brand_id,
    dp.brand_name,
    dp.category_id,
    dp.category_name,
    dp.model_year;

create or replace view analytics.mart_inventory_risk as
with max_order_date as (
    select max(order_date) as max_date
    from analytics.fact_sales
),
recent_sales as (
    select
        store_id,
        product_id,
        sum(quantity) as units_sold_90d
    from analytics.fact_sales fs
    cross join max_order_date m
    where fs.order_date >= (m.max_date - interval '90 days')
    group by store_id, product_id
)
select
    fi.store_id,
    ds.store_name,
    fi.product_id,
    dp.product_name,
    dp.brand_name,
    dp.category_name,
    fi.stock_quantity,
    coalesce(rs.units_sold_90d, 0) as units_sold_90d,
    round((coalesce(rs.units_sold_90d, 0)::numeric / 90), 4) as daily_sales_velocity,
    case
        when coalesce(rs.units_sold_90d, 0) = 0 then null
        else round(fi.stock_quantity::numeric / nullif((rs.units_sold_90d::numeric / 90), 0), 1)
    end as days_of_supply,
    round(fi.inventory_value, 2) as inventory_value,
    case
        when fi.stock_quantity = 0 and coalesce(rs.units_sold_90d, 0) > 0 then 'stockout'
        when coalesce(rs.units_sold_90d, 0) > 0 and fi.stock_quantity <= (rs.units_sold_90d::numeric / 90 * 14) then 'stockout_risk'
        when coalesce(rs.units_sold_90d, 0) = 0 and fi.stock_quantity > 0 then 'overstock_risk'
        when fi.stock_quantity > (rs.units_sold_90d::numeric / 90 * 120) then 'overstock_risk'
        else 'healthy'
    end as inventory_status
from analytics.fact_inventory fi
left join recent_sales rs
    on fi.store_id = rs.store_id
    and fi.product_id = rs.product_id
left join analytics.dim_store ds
    on fi.store_id = ds.store_id
left join analytics.dim_product dp
    on fi.product_id = dp.product_id;

create or replace view analytics.mart_customer_segments as
with customer_sales as (
    select
        customer_id,
        count(distinct order_id) as orders,
        sum(quantity) as units_sold,
        round(sum(revenue), 2) as revenue,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date
    from analytics.fact_sales
    group by customer_id
),
ranked as (
    select
        dc.customer_id,
        dc.customer_name,
        dc.city,
        dc.state,
        coalesce(cs.orders, 0) as orders,
        coalesce(cs.units_sold, 0) as units_sold,
        coalesce(cs.revenue, 0) as revenue,
        cs.first_order_date,
        cs.last_order_date,
        percent_rank() over (order by coalesce(cs.revenue, 0)) as revenue_percent_rank
    from analytics.dim_customer dc
    left join customer_sales cs
        on dc.customer_id = cs.customer_id
)
select
    customer_id,
    customer_name,
    city,
    state,
    orders,
    units_sold,
    revenue,
    first_order_date,
    last_order_date,
    case
        when orders = 0 then 'no_orders'
        when revenue_percent_rank >= 0.95 then 'vip'
        when revenue_percent_rank >= 0.80 then 'high_value'
        when orders >= 2 then 'repeat'
        else 'one_time'
    end as customer_segment
from ranked;

create or replace view analytics.mart_staff_performance as
select
    fs.staff_id,
    dsf.staff_name,
    dsf.store_id,
    dsf.store_name,
    dsf.manager_id,
    dsf.manager_name,
    count(distinct fs.order_id) as orders,
    count(distinct fs.customer_id) as customers,
    sum(fs.quantity) as units_sold,
    round(sum(fs.revenue), 2) as revenue,
    round(sum(fs.revenue) / nullif(count(distinct fs.order_id), 0), 2) as average_order_value,
    round(avg(case when fs.is_late_shipment then 1.0 else 0.0 end) filter (where fs.shipped_date is not null), 4) as late_shipment_rate
from analytics.fact_sales fs
left join analytics.dim_staff dsf
    on fs.staff_id = dsf.staff_id
group by
    fs.staff_id,
    dsf.staff_name,
    dsf.store_id,
    dsf.store_name,
    dsf.manager_id,
    dsf.manager_name;

create or replace view analytics.mart_delivery_performance as
select
    date_trunc('month', fs.order_date)::date as month,
    fs.store_id,
    ds.store_name,
    count(distinct fs.order_id) as orders,
    count(distinct fs.order_id) filter (where fs.shipped_date is not null) as shipped_orders,
    round(avg(fs.days_to_ship) filter (where fs.shipped_date is not null), 2) as avg_days_to_ship,
    round(avg(case when fs.is_late_shipment then 1.0 else 0.0 end) filter (where fs.shipped_date is not null), 4) as late_shipment_rate
from analytics.fact_sales fs
left join analytics.dim_store ds
    on fs.store_id = ds.store_id
group by 1, fs.store_id, ds.store_name;
