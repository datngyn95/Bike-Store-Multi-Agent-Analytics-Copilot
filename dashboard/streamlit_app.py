from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from components import db, ui
from components.auth import render_account_controls, require_authentication
from pages import copilot, customers, data_quality, delivery, executive, inventory, products, sales, staff, stores


PAGES = {
    "Executive": executive.render,
    "Sales": sales.render,
    "Customers": customers.render,
    "Products": products.render,
    "Inventory": inventory.render,
    "Stores": stores.render,
    "Staff": staff.render,
    "Delivery": delivery.render,
    "Data Quality": data_quality.render,
    "Copilot": copilot.render,
}


def main() -> None:
    ui.configure_page()
    require_authentication()

    with st.sidebar:
        st.title("Bike Store")
        page_name = st.radio("Trang", list(PAGES.keys()), label_visibility="collapsed")
        st.divider()
        if db.has_configured_database_url():
            st.caption("Database: configured")
        else:
            st.caption("Database: missing DATABASE_URL")
        if st.button("Lam moi cache", width="stretch"):
            db.clear_query_cache()
            st.rerun()
        st.divider()
        render_account_controls()

    PAGES[page_name]()


if __name__ == "__main__":
    main()
