# Bike Store Data Quality Report

- Run ID: `8177dbaa-db71-4811-9d49-e3451930461d`
- Checked at UTC: `2026-07-18T16:33:26.296382+00:00`
- Overall status: **PASS**
- Checks passed: `34/34`
- Checks failed: `0`

## Category Summary

| Category | Checks | Failed | Status |
| --- | ---: | ---: | --- |
| analytics_regression | 3 | 0 | PASS |
| date_check | 1 | 0 | PASS |
| domain_rule | 1 | 0 | PASS |
| duplicate_check | 1 | 0 | PASS |
| foreign_key | 4 | 0 | PASS |
| null_check | 3 | 0 | PASS |
| numeric_check | 1 | 0 | PASS |
| row_count | 20 | 0 | PASS |

## Check Results

| Status | Check | Category | Issues | Max Allowed | Description |
| --- | --- | --- | ---: | ---: | --- |
| PASS | `raw_brands_expected_count` | row_count | 0 | 0 | raw.brands must contain 9 rows from source CSV. |
| PASS | `raw_categories_expected_count` | row_count | 0 | 0 | raw.categories must contain 7 rows from source CSV. |
| PASS | `raw_customers_expected_count` | row_count | 0 | 0 | raw.customers must contain 1445 rows from source CSV. |
| PASS | `raw_orders_expected_count` | row_count | 0 | 0 | raw.orders must contain 1615 rows from source CSV. |
| PASS | `raw_order_items_expected_count` | row_count | 0 | 0 | raw.order_items must contain 4722 rows from source CSV. |
| PASS | `raw_products_expected_count` | row_count | 0 | 0 | raw.products must contain 321 rows from source CSV. |
| PASS | `raw_staffs_expected_count` | row_count | 0 | 0 | raw.staffs must contain 10 rows from source CSV. |
| PASS | `raw_stocks_expected_count` | row_count | 0 | 0 | raw.stocks must contain 939 rows from source CSV. |
| PASS | `raw_stores_expected_count` | row_count | 0 | 0 | raw.stores must contain 3 rows from source CSV. |
| PASS | `stg_brands_matches_raw_brands_count` | row_count | 0 | 0 | staging.stg_brands row count must match raw.brands. |
| PASS | `stg_categories_matches_raw_categories_count` | row_count | 0 | 0 | staging.stg_categories row count must match raw.categories. |
| PASS | `stg_customers_matches_raw_customers_count` | row_count | 0 | 0 | staging.stg_customers row count must match raw.customers. |
| PASS | `stg_orders_matches_raw_orders_count` | row_count | 0 | 0 | staging.stg_orders row count must match raw.orders. |
| PASS | `stg_order_items_matches_raw_order_items_count` | row_count | 0 | 0 | staging.stg_order_items row count must match raw.order_items. |
| PASS | `stg_products_matches_raw_products_count` | row_count | 0 | 0 | staging.stg_products row count must match raw.products. |
| PASS | `stg_staffs_matches_raw_staffs_count` | row_count | 0 | 0 | staging.stg_staffs row count must match raw.staffs. |
| PASS | `stg_stocks_matches_raw_stocks_count` | row_count | 0 | 0 | staging.stg_stocks row count must match raw.stocks. |
| PASS | `stg_stores_matches_raw_stores_count` | row_count | 0 | 0 | staging.stg_stores row count must match raw.stores. |
| PASS | `analytics_fact_sales_matches_stg_order_items_count` | row_count | 0 | 0 | analytics.fact_sales must preserve every staging order item row. |
| PASS | `analytics_fact_inventory_matches_stg_stocks_count` | row_count | 0 | 0 | analytics.fact_inventory must preserve every staging stock row. |
| PASS | `required_primary_keys_not_null` | null_check | 0 | 0 | All primary key fields must be non-null after staging. |
| PASS | `required_business_names_not_null` | null_check | 0 | 0 | Core human-readable names must be present for dimensions. |
| PASS | `order_required_fields_not_null` | null_check | 0 | 0 | Orders and order items must keep required analytic fields. |
| PASS | `duplicate_primary_keys` | duplicate_check | 0 | 0 | Primary and composite keys must be unique in staging. |
| PASS | `product_foreign_keys_valid` | foreign_key | 0 | 0 | Products must reference existing brands and categories. |
| PASS | `order_foreign_keys_valid` | foreign_key | 0 | 0 | Orders must reference existing customers, stores and staffs. |
| PASS | `order_item_foreign_keys_valid` | foreign_key | 0 | 0 | Order items must reference existing orders and products. |
| PASS | `staff_and_stock_foreign_keys_valid` | foreign_key | 0 | 0 | Staffs and stocks must reference existing stores/products/managers. |
| PASS | `order_status_values_valid` | domain_rule | 0 | 0 | Order status must be one of the source system values 1, 2, 3, 4. |
| PASS | `date_values_valid` | date_check | 0 | 0 | Order dates must be parseable and follow business date order. |
| PASS | `numeric_values_valid` | numeric_check | 0 | 0 | Quantities, prices and discounts must be in valid ranges. |
| PASS | `analytics_revenue_non_negative` | analytics_regression | 0 | 0 | Fact sales revenue must not contain negative values. |
| PASS | `analytics_core_kpis_match_prd_baseline` | analytics_regression | 0 | 0 | Core KPI totals must match the validated PRD baseline. |
| PASS | `analytics_marts_not_empty` | analytics_regression | 0 | 0 | Dashboard/API marts must contain rows. |
