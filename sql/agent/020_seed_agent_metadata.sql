set search_path = public, extensions, agent, analytics, staging, raw, audit;

insert into agent.agent_registry (
    agent_name,
    domain,
    description,
    default_metrics,
    default_tables,
    owner_persona
)
values
    (
        'orchestrator_agent',
        'orchestration',
        'Routes Vietnamese analytics questions to the right Bike Store domain agents and merges evidence-backed answers.',
        array['revenue', 'orders', 'units_sold', 'average_order_value', 'stock_quantity'],
        array['analytics.*', 'agent.metric_catalog', 'agent.sql_templates', 'agent.question_examples'],
        'CEO/Founder, Data Analyst'
    ),
    (
        'sales_agent',
        'sales',
        'Analyzes revenue, orders, units sold, AOV, discounts and monthly sales trends.',
        array['revenue', 'orders', 'units_sold', 'average_order_value', 'discount_rate', 'sales_growth'],
        array['analytics.fact_sales', 'analytics.mart_sales_monthly', 'analytics.mart_executive_summary'],
        'CEO/Founder, Sales Manager'
    ),
    (
        'customer_agent',
        'customer',
        'Analyzes customers by state/city, top customers, lifetime revenue proxy and order frequency.',
        array['customer_count', 'orders_per_customer', 'revenue_per_customer', 'state_revenue', 'top_customers'],
        array['analytics.dim_customer', 'analytics.mart_customer_segments', 'analytics.fact_sales'],
        'Customer Analyst'
    ),
    (
        'product_agent',
        'product',
        'Analyzes product, category, brand, model year, selling price and discount performance.',
        array['product_revenue', 'units_sold', 'category_revenue', 'brand_revenue', 'avg_selling_price', 'discount_by_product'],
        array['analytics.dim_product', 'analytics.mart_product_performance', 'analytics.fact_sales'],
        'Product Manager'
    ),
    (
        'inventory_agent',
        'inventory',
        'Analyzes stock quantity, sales velocity, stockout risk, overstock risk and inventory value.',
        array['stock_quantity', 'sales_velocity', 'stockout_risk', 'overstock_risk', 'inventory_value'],
        array['analytics.fact_inventory', 'analytics.mart_inventory_risk'],
        'Inventory Manager'
    ),
    (
        'store_agent',
        'store',
        'Compares store revenue, orders, AOV, delivery delay and inventory health.',
        array['store_revenue', 'store_orders', 'store_aov', 'late_shipment_rate', 'store_inventory_health'],
        array['analytics.dim_store', 'analytics.mart_sales_by_store', 'analytics.mart_delivery_performance'],
        'CEO/Founder, Sales Manager'
    ),
    (
        'staff_agent',
        'staff',
        'Analyzes staff revenue, order count, AOV and manager/store performance.',
        array['orders_by_staff', 'revenue_by_staff', 'avg_order_value_by_staff', 'manager_performance'],
        array['analytics.dim_staff', 'analytics.mart_staff_performance', 'analytics.fact_sales'],
        'Sales Manager'
    ),
    (
        'data_quality_agent',
        'data_quality',
        'Explains data quality checks for nulls, duplicate keys, foreign keys, invalid dates and numeric anomalies.',
        array['dq_pass_rate', 'failed_checks', 'issue_count', 'missing_required_fields', 'invalid_numeric_rows', 'negative_revenue_rows'],
        array['audit.data_quality_check_results', 'reports.data_quality_report', 'analytics.fact_sales'],
        'Data Analyst'
    )
on conflict (agent_name) do update set
    domain = excluded.domain,
    description = excluded.description,
    default_metrics = excluded.default_metrics,
    default_tables = excluded.default_tables,
    owner_persona = excluded.owner_persona,
    is_active = true,
    updated_at = now();

insert into agent.metric_catalog (
    metric_name,
    domain,
    description,
    formula,
    grain,
    primary_source,
    related_tables,
    owner_agent,
    display_format,
    caveats
)
values
    ('revenue', 'sales', 'Revenue after discount.', 'quantity * list_price * (1 - discount)', 'order_item', 'analytics.fact_sales', array['analytics.mart_sales_monthly', 'analytics.mart_sales_by_store', 'analytics.mart_product_performance'], 'sales_agent', 'currency', 'Uses line-item list price and discount from order_items.'),
    ('gross_sales', 'sales', 'Revenue before discount.', 'quantity * list_price', 'order_item', 'analytics.fact_sales', array['analytics.mart_sales_monthly', 'analytics.mart_product_performance'], 'sales_agent', 'currency', null),
    ('discount_amount', 'sales', 'Absolute discount amount.', 'quantity * list_price * discount', 'order_item', 'analytics.fact_sales', array['analytics.mart_sales_monthly', 'analytics.mart_product_performance'], 'sales_agent', 'currency', null),
    ('orders', 'sales', 'Distinct order count.', 'count(distinct order_id)', 'selected grain', 'analytics.fact_sales', array['analytics.mart_executive_summary', 'analytics.mart_sales_monthly'], 'sales_agent', 'number', null),
    ('order_items', 'sales', 'Line item count.', 'count(*)', 'order_item', 'analytics.fact_sales', array['analytics.mart_executive_summary'], 'sales_agent', 'number', null),
    ('units_sold', 'sales', 'Total product quantity sold.', 'sum(quantity)', 'selected grain', 'analytics.fact_sales', array['analytics.mart_sales_monthly', 'analytics.mart_product_performance'], 'sales_agent', 'number', null),
    ('average_order_value', 'sales', 'Average revenue per order.', 'sum(revenue) / nullif(count(distinct order_id), 0)', 'selected grain', 'analytics.fact_sales', array['analytics.mart_executive_summary', 'analytics.mart_sales_by_store'], 'sales_agent', 'currency', 'AOV is computed after discount.'),
    ('discount_rate', 'sales', 'Discount amount as a share of gross sales.', 'sum(discount_amount) / nullif(sum(gross_sales), 0)', 'selected grain', 'analytics.fact_sales', array['analytics.mart_sales_monthly', 'analytics.mart_product_performance'], 'sales_agent', 'percent', null),
    ('sales_growth', 'sales', 'Period-over-period revenue growth.', '(current_period_revenue - prior_period_revenue) / nullif(prior_period_revenue, 0)', 'month', 'analytics.mart_sales_monthly', array['analytics.mart_sales_monthly'], 'sales_agent', 'percent', 'Derived in query or dashboard layer when comparing adjacent periods.'),
    ('customers_with_orders', 'customer', 'Distinct customers with at least one order.', 'count(distinct customer_id)', 'selected grain', 'analytics.fact_sales', array['analytics.mart_executive_summary'], 'customer_agent', 'number', null),
    ('customer_count', 'customer', 'Customer count in a segment or geography.', 'count(distinct customer_id)', 'customer', 'analytics.mart_customer_segments', array['analytics.dim_customer'], 'customer_agent', 'number', null),
    ('orders_per_customer', 'customer', 'Average order frequency per customer.', 'sum(orders) / nullif(count(distinct customer_id), 0)', 'customer group', 'analytics.mart_customer_segments', array['analytics.fact_sales'], 'customer_agent', 'number', null),
    ('revenue_per_customer', 'customer', 'Average revenue per customer.', 'sum(revenue) / nullif(count(distinct customer_id), 0)', 'customer group', 'analytics.mart_customer_segments', array['analytics.fact_sales'], 'customer_agent', 'currency', null),
    ('state_revenue', 'customer', 'Revenue grouped by customer state.', 'sum(revenue) grouped by state', 'state', 'analytics.mart_customer_segments', array['analytics.dim_customer'], 'customer_agent', 'currency', null),
    ('top_customers', 'customer', 'Highest value customers by revenue and orders.', 'order customers by revenue desc, orders desc', 'customer', 'analytics.mart_customer_segments', array['analytics.dim_customer'], 'customer_agent', 'rank', null),
    ('product_revenue', 'product', 'Revenue by product.', 'sum(revenue) grouped by product_id', 'product', 'analytics.mart_product_performance', array['analytics.dim_product', 'analytics.fact_sales'], 'product_agent', 'currency', null),
    ('category_revenue', 'product', 'Revenue by product category.', 'sum(revenue) grouped by category_name', 'category', 'analytics.mart_product_performance', array['analytics.dim_category'], 'product_agent', 'currency', null),
    ('brand_revenue', 'product', 'Revenue by brand.', 'sum(revenue) grouped by brand_name', 'brand', 'analytics.mart_product_performance', array['analytics.dim_brand'], 'product_agent', 'currency', null),
    ('avg_selling_price', 'product', 'Average selling price after discount.', 'sum(revenue) / nullif(sum(quantity), 0)', 'product', 'analytics.mart_product_performance', array['analytics.fact_sales'], 'product_agent', 'currency', null),
    ('discount_by_product', 'product', 'Discount rate by product, brand or category.', 'sum(discount_amount) / nullif(sum(gross_sales), 0)', 'product', 'analytics.mart_product_performance', array['analytics.fact_sales'], 'product_agent', 'percent', null),
    ('stock_quantity', 'inventory', 'On-hand inventory quantity by store/product.', 'sum(stock_quantity)', 'store_product', 'analytics.fact_inventory', array['analytics.mart_inventory_risk'], 'inventory_agent', 'number', null),
    ('inventory_value', 'inventory', 'Inventory value proxy.', 'stock_quantity * list_price', 'store_product', 'analytics.fact_inventory', array['analytics.mart_inventory_risk'], 'inventory_agent', 'currency', 'Uses product list price as proxy value.'),
    ('sales_velocity', 'inventory', 'Recent daily units sold velocity.', 'units_sold_90d / 90', 'store_product', 'analytics.mart_inventory_risk', array['analytics.fact_sales'], 'inventory_agent', 'number', 'Uses the trailing 90 days from max order date in the dataset.'),
    ('stockout_risk', 'inventory', 'Products with low or zero stock relative to recent sales velocity.', 'inventory_status in (''stockout'', ''stockout_risk'')', 'store_product', 'analytics.mart_inventory_risk', array['analytics.fact_inventory'], 'inventory_agent', 'status', null),
    ('overstock_risk', 'inventory', 'Products with excess inventory or no recent sales.', 'inventory_status = ''overstock_risk''', 'store_product', 'analytics.mart_inventory_risk', array['analytics.fact_inventory'], 'inventory_agent', 'status', null),
    ('store_revenue', 'store', 'Revenue grouped by store.', 'sum(revenue) grouped by store_id', 'store', 'analytics.mart_sales_by_store', array['analytics.fact_sales', 'analytics.dim_store'], 'store_agent', 'currency', null),
    ('store_orders', 'store', 'Distinct orders grouped by store.', 'count(distinct order_id) grouped by store_id', 'store', 'analytics.mart_sales_by_store', array['analytics.fact_sales'], 'store_agent', 'number', null),
    ('store_aov', 'store', 'Average order value by store.', 'sum(revenue) / nullif(count(distinct order_id), 0)', 'store', 'analytics.mart_sales_by_store', array['analytics.fact_sales'], 'store_agent', 'currency', null),
    ('late_shipment_rate', 'store', 'Late shipped orders as a share of shipped orders.', 'avg(case when is_late_shipment then 1.0 else 0.0 end) filter (where shipped_date is not null)', 'store/month/staff', 'analytics.fact_sales', array['analytics.mart_sales_by_store', 'analytics.mart_delivery_performance', 'analytics.mart_staff_performance'], 'store_agent', 'percent', 'Canceled or unshipped orders are excluded from rate denominator.'),
    ('store_inventory_health', 'store', 'Store inventory health summary based on inventory risk statuses.', 'count by inventory_status grouped by store', 'store', 'analytics.mart_inventory_risk', array['analytics.fact_inventory'], 'store_agent', 'status', null),
    ('orders_by_staff', 'staff', 'Distinct orders handled by staff.', 'count(distinct order_id) grouped by staff_id', 'staff', 'analytics.mart_staff_performance', array['analytics.fact_sales', 'analytics.dim_staff'], 'staff_agent', 'number', null),
    ('revenue_by_staff', 'staff', 'Revenue handled by staff.', 'sum(revenue) grouped by staff_id', 'staff', 'analytics.mart_staff_performance', array['analytics.fact_sales', 'analytics.dim_staff'], 'staff_agent', 'currency', null),
    ('avg_order_value_by_staff', 'staff', 'Average order value by staff.', 'sum(revenue) / nullif(count(distinct order_id), 0)', 'staff', 'analytics.mart_staff_performance', array['analytics.fact_sales'], 'staff_agent', 'currency', null),
    ('manager_performance', 'staff', 'Staff performance grouped by manager.', 'aggregate staff orders and revenue by manager_id', 'manager', 'analytics.mart_staff_performance', array['analytics.dim_staff'], 'staff_agent', 'rank', 'Computed by grouping the staff mart at query time.'),
    ('dq_pass_rate', 'data_quality', 'Share of data quality checks passing.', 'passed_checks / total_checks', 'dq_run', 'audit.data_quality_check_results', array['reports.data_quality_report'], 'data_quality_agent', 'percent', 'Available after running scripts/check_data_quality.py.'),
    ('failed_checks', 'data_quality', 'Count of failed data quality checks.', 'count(*) where status = ''fail''', 'dq_run', 'audit.data_quality_check_results', array['reports.data_quality_report'], 'data_quality_agent', 'number', null),
    ('issue_count', 'data_quality', 'Total issue count from data quality checks.', 'sum(issue_count)', 'dq_run', 'audit.data_quality_check_results', array['reports.data_quality_report'], 'data_quality_agent', 'number', null),
    ('missing_required_fields', 'data_quality', 'Rows with required fact_sales fields missing.', 'count rows where required fields are null', 'order_item', 'analytics.fact_sales', array['reports.data_quality_report'], 'data_quality_agent', 'number', null),
    ('invalid_numeric_rows', 'data_quality', 'Rows with invalid quantity, price or discount values.', 'count rows where quantity/list_price/discount violate accepted ranges', 'order_item', 'analytics.fact_sales', array['reports.data_quality_report'], 'data_quality_agent', 'number', null),
    ('negative_revenue_rows', 'data_quality', 'Rows with negative revenue.', 'count rows where revenue < 0', 'order_item', 'analytics.fact_sales', array['reports.data_quality_report'], 'data_quality_agent', 'number', null)
on conflict (metric_name) do update set
    domain = excluded.domain,
    description = excluded.description,
    formula = excluded.formula,
    grain = excluded.grain,
    primary_source = excluded.primary_source,
    related_tables = excluded.related_tables,
    owner_agent = excluded.owner_agent,
    display_format = excluded.display_format,
    caveats = excluded.caveats,
    is_active = true,
    updated_at = now();

insert into agent.sql_templates (
    template_name,
    domain,
    agents,
    keywords,
    metrics,
    tables,
    description,
    sql_template,
    result_grain,
    chart_hint
)
values
    (
        'sales_monthly',
        'sales',
        array['sales_agent'],
        array['doanh thu', 'revenue', 'sales', 'thang', 'monthly', '2016', '2017', '2018'],
        array['revenue', 'orders', 'units_sold', 'average_order_value', 'discount_rate'],
        array['analytics.mart_sales_monthly'],
        'Monthly revenue, orders, units sold, AOV and discount rate.',
        $$select month, year, month_number, orders, units_sold, revenue, average_order_value, discount_rate
from analytics.mart_sales_monthly
order by month
limit {{limit}}$$,
        'month',
        'line'
    ),
    (
        'sales_summary',
        'sales',
        array['sales_agent'],
        array['tong quan', 'overview', 'kpi', 'summary', 'doanh so', 'tong doanh thu'],
        array['revenue', 'orders', 'units_sold', 'average_order_value', 'late_shipment_rate'],
        array['analytics.mart_executive_summary'],
        'Executive KPI summary.',
        $$select orders, order_items, customers_with_orders, products_sold, stores_with_orders,
       first_order_date, last_order_date, revenue, units_sold, average_order_value,
       discount_rate, avg_days_to_ship, late_shipment_rate
from analytics.mart_executive_summary
limit 1$$,
        'dataset',
        'metric_cards'
    ),
    (
        'top_store',
        'store',
        array['store_agent', 'sales_agent'],
        array['cua hang', 'store', 'cao nhat', 'top store', 'doanh thu', 'revenue'],
        array['store_revenue', 'orders', 'average_order_value', 'late_shipment_rate'],
        array['analytics.mart_sales_by_store'],
        'Rank stores by revenue.',
        $$select store_name, city, state, orders, customers, units_sold, revenue,
       average_order_value, late_shipment_rate
from analytics.mart_sales_by_store
order by revenue desc
limit {{limit}}$$,
        'store',
        'bar'
    ),
    (
        'delivery_late',
        'store',
        array['store_agent'],
        array['giao tre', 'late', 'delivery', 'shipment', 'ship', 'cham giao'],
        array['late_shipment_rate', 'avg_days_to_ship'],
        array['analytics.mart_delivery_performance'],
        'Late shipment rate by store.',
        $$select store_name, sum(orders) as orders, sum(shipped_orders) as shipped_orders,
       avg(avg_days_to_ship) as avg_days_to_ship,
       avg(late_shipment_rate) as late_shipment_rate
from analytics.mart_delivery_performance
group by store_name
order by late_shipment_rate desc
limit {{limit}}$$,
        'store',
        'bar'
    ),
    (
        'product_performance',
        'product',
        array['product_agent'],
        array['san pham', 'product', 'brand', 'thuong hieu', 'category', 'danh muc', 'model', 'doanh thu', 'revenue', 'dong gop'],
        array['product_revenue', 'brand_revenue', 'category_revenue', 'units_sold', 'avg_selling_price'],
        array['analytics.mart_product_performance'],
        'Product, brand and category performance.',
        $$select product_name, brand_name, category_name, model_year, orders, units_sold,
       revenue, avg_selling_price, discount_rate
from analytics.mart_product_performance
order by revenue desc
limit {{limit}}$$,
        'product',
        'bar'
    ),
    (
        'inventory_risk',
        'inventory',
        array['inventory_agent', 'product_agent'],
        array['ton kho', 'stock', 'inventory', 'stockout', 'overstock', 'ban chay', 'rui ro'],
        array['stock_quantity', 'sales_velocity', 'stockout_risk', 'overstock_risk', 'inventory_value'],
        array['analytics.mart_inventory_risk'],
        'Stockout and overstock risk by store/product.',
        $$select store_name, product_name, brand_name, category_name, stock_quantity,
       units_sold_90d, daily_sales_velocity, days_of_supply, inventory_value,
       inventory_status
from analytics.mart_inventory_risk
where inventory_status in ('stockout', 'stockout_risk', 'overstock_risk')
order by
    case inventory_status
        when 'stockout' then 1
        when 'stockout_risk' then 2
        when 'overstock_risk' then 3
        else 4
    end,
    units_sold_90d desc
limit {{limit}}$$,
        'store_product',
        'table'
    ),
    (
        'customer_state',
        'customer',
        array['customer_agent'],
        array['khach', 'customer', 'state', 'bang', 'city', 'vip', 'top khach'],
        array['customer_count', 'orders_per_customer', 'revenue_per_customer', 'state_revenue', 'top_customers'],
        array['analytics.mart_customer_segments'],
        'Customer revenue by state or top customers.',
        $$select state, count(*) as customers, sum(orders) as orders,
       sum(units_sold) as units_sold, sum(revenue) as revenue
from analytics.mart_customer_segments
group by state
order by revenue desc
limit {{limit}}$$,
        'state',
        'bar'
    ),
    (
        'staff_revenue',
        'staff',
        array['staff_agent'],
        array['nhan vien', 'staff', 'manager', 'xu ly', 'salesperson'],
        array['orders_by_staff', 'revenue_by_staff', 'avg_order_value_by_staff', 'manager_performance'],
        array['analytics.mart_staff_performance'],
        'Staff performance by revenue, orders and AOV.',
        $$select staff_name, store_name, manager_name, orders, customers, units_sold,
       revenue, average_order_value, late_shipment_rate
from analytics.mart_staff_performance
order by revenue desc
limit {{limit}}$$,
        'staff',
        'bar'
    ),
    (
        'data_quality_fact_sales',
        'data_quality',
        array['data_quality_agent'],
        array['loi du lieu', 'data quality', 'null', 'duplicate', 'foreign key', 'order_items', 'quality'],
        array['missing_required_fields', 'invalid_numeric_rows', 'negative_revenue_rows'],
        array['analytics.fact_sales'],
        'Read-only fact_sales quality checks.',
        $$select count(*) as rows_checked,
       count(*) filter (
           where order_id is null
              or item_id is null
              or product_id is null
              or quantity is null
              or list_price is null
              or discount is null
       ) as missing_required_fields,
       count(*) filter (
           where quantity <= 0
              or list_price <= 0
              or discount < 0
              or discount >= 1
       ) as invalid_numeric_rows,
       count(*) filter (where revenue < 0) as negative_revenue_rows
from analytics.fact_sales
limit 1$$,
        'dataset',
        'metric_cards'
    ),
    (
        'metric_catalog',
        'data_quality',
        array['data_quality_agent', 'orchestrator_agent'],
        array['metric', 'catalog', 'dinh nghia', 'formula', 'kpi la gi', 'revenue', 'orders', 'units_sold', 'average_order_value'],
        array['metric_catalog'],
        array['agent.metric_catalog'],
        'Read metric definitions and primary sources.',
        $$select metric_name, description, formula, primary_source
from agent.metric_catalog
where is_active
order by metric_name
limit {{limit}}$$,
        'metric',
        'table'
    )
on conflict (template_name) do update set
    domain = excluded.domain,
    agents = excluded.agents,
    keywords = excluded.keywords,
    metrics = excluded.metrics,
    tables = excluded.tables,
    description = excluded.description,
    sql_template = excluded.sql_template,
    result_grain = excluded.result_grain,
    chart_hint = excluded.chart_hint,
    is_active = true,
    updated_at = now();

insert into agent.question_examples (
    question_id,
    domain,
    question_vi,
    expected_agents,
    expected_template,
    metrics,
    tables,
    tags,
    difficulty
)
values
    ('q_sales_monthly_2017', 'sales', 'Doanh thu theo thang nam 2017 nhu the nao?', array['sales_agent'], 'sales_monthly', array['revenue', 'orders'], array['analytics.mart_sales_monthly'], array['trend', 'time_filter'], 'basic'),
    ('q_sales_summary', 'sales', 'Tong revenue, orders va AOV cua Bike Store la bao nhieu?', array['sales_agent'], 'sales_summary', array['revenue', 'orders', 'average_order_value'], array['analytics.mart_executive_summary'], array['kpi'], 'basic'),
    ('q_sales_discount', 'sales', 'Ty le discount toan bo dataset la bao nhieu?', array['sales_agent'], 'sales_summary', array['discount_rate'], array['analytics.mart_executive_summary'], array['kpi', 'discount'], 'basic'),
    ('q_store_top_revenue', 'store', 'Cua hang nao co doanh thu cao nhat?', array['store_agent', 'sales_agent'], 'top_store', array['store_revenue'], array['analytics.mart_sales_by_store'], array['ranking'], 'basic'),
    ('q_store_aov', 'store', 'Cua hang nao co AOV cao nhat?', array['store_agent', 'sales_agent'], 'top_store', array['store_aov'], array['analytics.mart_sales_by_store'], array['ranking'], 'intermediate'),
    ('q_delivery_late_store', 'store', 'Cua hang nao co ty le giao tre cao nhat?', array['store_agent'], 'delivery_late', array['late_shipment_rate'], array['analytics.mart_delivery_performance'], array['delivery'], 'basic'),
    ('q_product_top_revenue', 'product', 'San pham nao co revenue cao nhat?', array['product_agent'], 'product_performance', array['product_revenue'], array['analytics.mart_product_performance'], array['ranking'], 'basic'),
    ('q_brand_revenue', 'product', 'Brand nao dong gop doanh thu lon nhat?', array['product_agent'], 'product_performance', array['brand_revenue'], array['analytics.mart_product_performance'], array['brand'], 'basic'),
    ('q_category_units', 'product', 'Category nao ban chay nhat theo units sold?', array['product_agent'], 'product_performance', array['category_revenue', 'units_sold'], array['analytics.mart_product_performance'], array['category'], 'intermediate'),
    ('q_product_discount', 'product', 'San pham nao co discount rate cao nhat?', array['product_agent'], 'product_performance', array['discount_by_product'], array['analytics.mart_product_performance'], array['discount'], 'intermediate'),
    ('q_inventory_stockout', 'inventory', 'San pham nao ban chay nhung ton kho thap?', array['inventory_agent', 'product_agent'], 'inventory_risk', array['stockout_risk', 'sales_velocity'], array['analytics.mart_inventory_risk'], array['risk'], 'basic'),
    ('q_inventory_overstock', 'inventory', 'Mat hang nao co rui ro overstock?', array['inventory_agent', 'product_agent'], 'inventory_risk', array['overstock_risk'], array['analytics.mart_inventory_risk'], array['risk'], 'basic'),
    ('q_inventory_value', 'inventory', 'Gia tri ton kho proxy duoc tinh tu bang nao?', array['inventory_agent'], 'metric_catalog', array['inventory_value'], array['agent.metric_catalog'], array['definition'], 'basic'),
    ('q_customer_state_revenue', 'customer', 'Bang nao co revenue khach hang cao nhat?', array['customer_agent'], 'customer_state', array['state_revenue'], array['analytics.mart_customer_segments'], array['geography'], 'basic'),
    ('q_customer_top', 'customer', 'Khach hang VIP hoac top customers la ai?', array['customer_agent'], 'customer_state', array['top_customers'], array['analytics.mart_customer_segments'], array['ranking'], 'basic'),
    ('q_customer_frequency', 'customer', 'Tan suat mua trung binh cua khach hang duoc tinh nhu the nao?', array['customer_agent'], 'metric_catalog', array['orders_per_customer'], array['agent.metric_catalog'], array['definition'], 'intermediate'),
    ('q_staff_revenue', 'staff', 'Nhan vien nao tao revenue cao nhat?', array['staff_agent'], 'staff_revenue', array['revenue_by_staff'], array['analytics.mart_staff_performance'], array['ranking'], 'basic'),
    ('q_staff_orders', 'staff', 'Nhan vien nao xu ly nhieu don nhat?', array['staff_agent'], 'staff_revenue', array['orders_by_staff'], array['analytics.mart_staff_performance'], array['ranking'], 'basic'),
    ('q_staff_manager', 'staff', 'Manager nao co team performance tot nhat?', array['staff_agent'], 'staff_revenue', array['manager_performance'], array['analytics.mart_staff_performance'], array['manager'], 'advanced'),
    ('q_dq_order_items', 'data_quality', 'Co loi du lieu nao trong order_items khong?', array['data_quality_agent'], 'data_quality_fact_sales', array['missing_required_fields', 'invalid_numeric_rows'], array['analytics.fact_sales'], array['quality'], 'basic'),
    ('q_metric_revenue', 'data_quality', 'Metric revenue duoc dinh nghia nhu the nao?', array['data_quality_agent', 'orchestrator_agent'], 'metric_catalog', array['revenue'], array['agent.metric_catalog'], array['definition'], 'basic'),
    ('q_metric_late_shipment', 'data_quality', 'Metric late_shipment_rate lay tu bang nao?', array['data_quality_agent', 'orchestrator_agent'], 'metric_catalog', array['late_shipment_rate'], array['agent.metric_catalog'], array['definition'], 'basic'),
    ('q_schema_monthly_sales', 'data_quality', 'Bang nao phu hop de ve monthly sales trend?', array['data_quality_agent', 'orchestrator_agent'], 'metric_catalog', array['revenue', 'orders'], array['agent.metric_catalog', 'analytics.mart_sales_monthly'], array['schema'], 'basic'),
    ('q_agent_scope', 'data_quality', 'Copilot ho tro nhung domain agent nao?', array['data_quality_agent', 'orchestrator_agent'], 'metric_catalog', array['metric_catalog'], array['agent.agent_registry'], array['agent_scope'], 'basic')
on conflict (question_id) do update set
    domain = excluded.domain,
    question_vi = excluded.question_vi,
    expected_agents = excluded.expected_agents,
    expected_template = excluded.expected_template,
    metrics = excluded.metrics,
    tables = excluded.tables,
    tags = excluded.tags,
    difficulty = excluded.difficulty,
    is_eval_question = true,
    expected_warning = excluded.expected_warning,
    updated_at = now();

create or replace view agent.metric_catalog_seed as
select
    metric_name,
    description,
    formula,
    primary_source
from agent.metric_catalog
where is_active;

create or replace view agent.active_sql_templates as
select
    template_name,
    domain,
    agents,
    keywords,
    metrics,
    tables,
    description,
    sql_template,
    result_grain,
    chart_hint
from agent.sql_templates
where is_active;

create or replace view agent.eval_question_examples as
select
    question_id,
    domain,
    question_vi,
    expected_agents,
    expected_template,
    metrics,
    tables,
    tags,
    difficulty
from agent.question_examples
where is_eval_question;
