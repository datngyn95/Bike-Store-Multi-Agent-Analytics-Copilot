create or replace view agent.available_analytics_tables as
select
    schemaname as schema_name,
    viewname as table_name,
    definition
from pg_views
where schemaname in ('analytics', 'staging')
order by schemaname, viewname;

create or replace view agent.metric_catalog_seed as
select *
from (
    values
        ('revenue', 'Doanh thu sau discount', 'analytics.fact_sales.revenue = quantity * list_price * (1 - discount)', 'analytics.fact_sales'),
        ('orders', 'So don hang distinct', 'count(distinct order_id)', 'analytics.fact_sales'),
        ('units_sold', 'Tong so luong san pham ban ra', 'sum(quantity)', 'analytics.fact_sales'),
        ('average_order_value', 'Gia tri don hang trung binh', 'sum(revenue) / count(distinct order_id)', 'analytics.fact_sales'),
        ('discount_rate', 'Ty le discount theo doanh thu gross', 'sum(discount_amount) / sum(gross_sales)', 'analytics.fact_sales'),
        ('late_shipment_rate', 'Ty le giao tre tren don da ship', 'avg(is_late_shipment)', 'analytics.fact_sales'),
        ('stock_quantity', 'So luong ton kho', 'analytics.fact_inventory.stock_quantity', 'analytics.fact_inventory'),
        ('inventory_value', 'Gia tri ton kho proxy', 'stock_quantity * list_price', 'analytics.fact_inventory')
) as metrics(metric_name, description, formula, primary_source);
