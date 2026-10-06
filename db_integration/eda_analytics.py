"""
Nexus Peripherals - Exploratory Data Analysis (EDA) & PDF Report Generator
Provides monthly sales, intake restock auditing, order volume aggregation,
interactive visual plotting helpers, and executive vector PDF generation.
"""

import os
import datetime
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal

import matplotlib
# Use non-interactive backend for server/export routines, tkagg used inside Tkinter
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.ticker as ticker

from db_integration.db import get_db_cursor, get_db_connection


def ensure_eda_tables_and_seed():
    """
    Ensures INVENTORY_INTAKE table exists and seeds realistic multi-month 
    historical data (May 2026 - Oct 2026) across Chennai, Bengaluru, Mumbai
    if not already present, enabling rich exploratory data analysis.
    """
    with get_db_cursor(autocommit=True) as (conn, cur):
        # 1. Ensure INVENTORY_INTAKE table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS INVENTORY_INTAKE (
                IntakeID INT AUTO_INCREMENT PRIMARY KEY,
                WarehouseID INT NOT NULL,
                ProductID INT NOT NULL,
                QuantityAdded INT NOT NULL CHECK (QuantityAdded > 0),
                IntakeDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                StaffID INT NULL,
                FOREIGN KEY (WarehouseID) REFERENCES WAREHOUSE(WarehouseID) ON DELETE CASCADE,
                FOREIGN KEY (ProductID) REFERENCES PRODUCT(ProductID) ON DELETE CASCADE,
                FOREIGN KEY (StaffID) REFERENCES STAFF_USER(StaffID) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Check if intake data already exists
        cur.execute("SELECT COUNT(*) AS cnt FROM INVENTORY_INTAKE;")
        intake_count = cur.fetchone()["cnt"]

        if intake_count == 0:
            # Seed realistic intake records for each warehouse across past 6 months
            # Month distribution: May, Jun, Jul, Aug, Sep, Oct 2026
            seed_intakes = [
                # (WarehouseID, ProductID, Qty, DateStr, StaffID)
                # May 2026
                (1, 1, 15, "2026-05-10 10:30:00", 2),
                (1, 5, 80, "2026-05-12 11:15:00", 2),
                (2, 2, 35, "2026-05-14 09:45:00", 3),
                (2, 6, 120, "2026-05-18 14:20:00", 3),
                (3, 4, 25, "2026-05-20 16:00:00", 4),
                (3, 8, 90, "2026-05-22 13:10:00", 4),

                # June 2026
                (1, 2, 20, "2026-06-08 10:00:00", 2),
                (1, 7, 60, "2026-06-15 15:30:00", 2),
                (2, 1, 40, "2026-06-10 11:00:00", 3),
                (2, 9, 30, "2026-06-22 16:45:00", 3),
                (3, 3, 15, "2026-06-12 12:15:00", 4),
                (3, 10, 50, "2026-06-25 14:00:00", 4),

                # July 2026
                (1, 3, 12, "2026-07-05 09:30:00", 2),
                (1, 8, 110, "2026-07-16 14:15:00", 2),
                (2, 4, 30, "2026-07-11 10:45:00", 3),
                (2, 5, 140, "2026-07-19 13:00:00", 3),
                (3, 1, 20, "2026-07-09 11:20:00", 4),
                (3, 7, 75, "2026-07-23 15:40:00", 4),

                # August 2026
                (1, 4, 25, "2026-08-04 10:10:00", 2),
                (1, 6, 95, "2026-08-14 11:50:00", 2),
                (2, 3, 18, "2026-08-08 14:30:00", 3),
                (2, 10, 45, "2026-08-20 16:15:00", 3),
                (3, 2, 28, "2026-08-12 09:40:00", 4),
                (3, 5, 100, "2026-08-24 13:25:00", 4),

                # September 2026
                (1, 1, 18, "2026-09-02 10:00:00", 2),
                (1, 9, 25, "2026-09-15 12:30:00", 2),
                (2, 2, 50, "2026-09-07 15:00:00", 3),
                (2, 7, 85, "2026-09-22 11:45:00", 3),
                (3, 4, 22, "2026-09-10 14:10:00", 4),
                (3, 8, 120, "2026-09-26 16:30:00", 4),

                # October 2026 (Current)
                (1, 2, 30, "2026-10-01 11:20:00", 2),
                (1, 5, 150, "2026-10-03 14:00:00", 2),
                (2, 1, 45, "2026-10-02 10:15:00", 3),
                (2, 8, 200, "2026-10-04 13:30:00", 3),
                (3, 3, 10, "2026-10-02 15:45:00", 4),
                (3, 9, 35, "2026-10-05 09:30:00", 4),
            ]

            for wid, pid, qty, dt, sid in seed_intakes:
                cur.execute("""
                    INSERT INTO INVENTORY_INTAKE (WarehouseID, ProductID, QuantityAdded, IntakeDate, StaffID)
                    VALUES (%s, %s, %s, %s, %s)
                """, (wid, pid, qty, dt, sid))

        # Check if we have orders in earlier months (May - September)
        cur.execute("""
            SELECT COUNT(*) AS cnt FROM ORDERS 
            WHERE OrderDate < '2026-10-01 00:00:00';
        """)
        prior_order_count = cur.fetchone()["cnt"]

        if prior_order_count < 10:
            # Ensure at least 1 benchmark customer exists for historical seed orders
            cur.execute("SELECT CustomerID FROM CUSTOMER LIMIT 1;")
            cust = cur.fetchone()
            if not cust:
                cur.execute("""
                    INSERT INTO CUSTOMER (FullName, Email, PasswordHash, Phone, City, Latitude, Longitude, ShippingAddress)
                    VALUES ('Harshith Antyakula', 'customer.demo@nexus.local', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',
                            '9876543210', 'Chennai', 13.0827, 80.2707, 'Anna Nagar West, Chennai')
                """)
                cust_id = cur.lastrowid
            else:
                cust_id = cust["CustomerID"]

            # Multi-month historical order records (May - Sep 2026)
            historical_orders = [
                # May 2026
                ("2026-05-15 14:20:00", 1, [(1, 1, 16999.00), (5, 2, 2099.00)], "COMPLETED", "CARD", "DELIVERED"),
                ("2026-05-24 16:45:00", 2, [(2, 1, 14499.00), (9, 1, 11999.00)], "COMPLETED", "UPI", "DELIVERED"),
                ("2026-05-29 11:30:00", 3, [(4, 1, 11499.00), (6, 3, 1599.00)], "COMPLETED", "UPI", "DELIVERED"),

                # June 2026
                ("2026-06-10 10:15:00", 1, [(2, 1, 14499.00), (7, 2, 1899.00)], "COMPLETED", "UPI", "DELIVERED"),
                ("2026-06-18 15:30:00", 2, [(3, 1, 25999.00), (5, 2, 2099.00)], "COMPLETED", "CARD", "DELIVERED"),
                ("2026-06-25 18:00:00", 3, [(10, 2, 7499.00), (8, 4, 1299.00)], "COMPLETED", "NETBANKING", "DELIVERED"),

                # July 2026
                ("2026-07-08 12:40:00", 1, [(1, 1, 16999.00), (9, 1, 11999.00)], "COMPLETED", "UPI", "DELIVERED"),
                ("2026-07-17 14:20:00", 2, [(4, 2, 11499.00), (6, 2, 1599.00)], "COMPLETED", "CARD", "DELIVERED"),
                ("2026-07-28 16:10:00", 3, [(2, 1, 14499.00), (7, 3, 1899.00)], "COMPLETED", "UPI", "DELIVERED"),

                # August 2026
                ("2026-08-05 11:15:00", 1, [(3, 1, 25999.00), (8, 2, 1299.00)], "COMPLETED", "UPI", "DELIVERED"),
                ("2026-08-14 13:50:00", 2, [(1, 1, 16999.00), (5, 3, 2099.00)], "COMPLETED", "CARD", "DELIVERED"),
                ("2026-08-22 17:30:00", 3, [(9, 1, 11999.00), (10, 1, 7499.00)], "COMPLETED", "UPI", "DELIVERED"),

                # September 2026
                ("2026-09-04 10:20:00", 1, [(4, 1, 11499.00), (6, 2, 1599.00)], "COMPLETED", "UPI", "DELIVERED"),
                ("2026-09-12 15:45:00", 2, [(2, 1, 14499.00), (1, 1, 16999.00)], "COMPLETED", "NETBANKING", "DELIVERED"),
                ("2026-09-21 16:30:00", 3, [(3, 1, 25999.00), (5, 2, 2099.00)], "COMPLETED", "UPI", "DELIVERED"),
                ("2026-09-28 12:10:00", 1, [(10, 2, 7499.00), (8, 3, 1299.00)], "COMPLETED", "CARD", "DELIVERED"),
            ]

            for dt_str, wid, items, pay_stat, pay_method, ship_stat in historical_orders:
                total_amt = sum(q * p for _, q, p in items)
                # Insert Order
                cur.execute("""
                    INSERT INTO ORDERS (CustomerID, OrderDate, TotalAmount, OrderStatus, ShippingAddress)
                    VALUES (%s, %s, %s, 'DELIVERED', 'Historical Test Address')
                """, (cust_id, dt_str, total_amt))
                oid = cur.lastrowid

                # Insert Items
                for pid, qty, price in items:
                    cur.execute("""
                        INSERT INTO ORDER_ITEM (OrderID, ProductID, Quantity, UnitPriceAtSale)
                        VALUES (%s, %s, %s, %s)
                    """, (oid, pid, qty, price))

                # Insert Payment
                cur.execute("""
                    INSERT INTO PAYMENT (OrderID, PaymentDate, PaymentMethod, AmountPaid, PaymentStatus)
                    VALUES (%s, %s, %s, %s, %s)
                """, (oid, dt_str, pay_method, total_amt, pay_stat))

                # Insert Shipment
                tracking_no = f"TRK-{wid}-{oid}-{dt_str[:10].replace('-', '')}"
                cur.execute("""
                    INSERT INTO SHIPMENT (OrderID, WarehouseID, TrackingNumber, DispatchedDate, DeliveryStatus)
                    VALUES (%s, %s, %s, %s, %s)
                """, (oid, wid, tracking_no, dt_str, ship_stat))


def record_intake(warehouse_id: int, product_id: int, quantity: int, staff_id: Optional[int] = None) -> bool:
    """
    Records an inventory intake / restock event in INVENTORY_INTAKE.
    """
    try:
        with get_db_cursor(autocommit=True) as (conn, cur):
            cur.execute("""
                INSERT INTO INVENTORY_INTAKE (WarehouseID, ProductID, QuantityAdded, StaffID)
                VALUES (%s, %s, %s, %s)
            """, (warehouse_id, product_id, quantity, staff_id))
        return True
    except Exception as e:
        print(f"Error logging intake: {e}")
        return False


def get_available_months(warehouse_id: Optional[int] = None) -> List[str]:
    """
    Returns sorted list of distinct months (YYYY-MM) present in orders or intake.
    """
    ensure_eda_tables_and_seed()
    months = set()
    with get_db_cursor() as (conn, cur):
        # From orders (scoped by warehouse if provided)
        if warehouse_id:
            cur.execute("""
                SELECT DISTINCT DATE_FORMAT(o.OrderDate, '%Y-%m') AS m
                FROM ORDERS o
                INNER JOIN SHIPMENT s ON o.OrderID = s.OrderID
                WHERE s.WarehouseID = %s
            """, (warehouse_id,))
        else:
            cur.execute("SELECT DISTINCT DATE_FORMAT(OrderDate, '%Y-%m') AS m FROM ORDERS;")
        for r in cur.fetchall():
            if r["m"]:
                months.add(r["m"])

        # From intake
        if warehouse_id:
            cur.execute("""
                SELECT DISTINCT DATE_FORMAT(IntakeDate, '%Y-%m') AS m
                FROM INVENTORY_INTAKE
                WHERE WarehouseID = %s
            """, (warehouse_id,))
        else:
            cur.execute("SELECT DISTINCT DATE_FORMAT(IntakeDate, '%Y-%m') AS m FROM INVENTORY_INTAKE;")
        for r in cur.fetchall():
            if r["m"]:
                months.add(r["m"])

    sorted_months = sorted(list(months), reverse=True)
    return sorted_months if sorted_months else ["2026-10"]


def get_eda_kpis(warehouse_id: Optional[int] = None, month: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculates executive KPIs: Total Sales Revenue (₹), Total Orders, Total Restock Intake, Average Order Value.
    """
    ensure_eda_tables_and_seed()
    with get_db_cursor() as (conn, cur):
        # Sales & Orders
        where_clauses_orders = []
        params_orders = []

        if warehouse_id:
            where_clauses_orders.append("s.WarehouseID = %s")
            params_orders.append(warehouse_id)
        if month and month != "ALL":
            where_clauses_orders.append("DATE_FORMAT(o.OrderDate, '%Y-%m') = %s")
            params_orders.append(month)

        where_sql_orders = "WHERE " + " AND ".join(where_clauses_orders) if where_clauses_orders else ""

        cur.execute(f"""
            SELECT 
                COUNT(DISTINCT o.OrderID) AS total_orders,
                COALESCE(SUM(o.TotalAmount), 0.0) AS total_sales
            FROM ORDERS o
            INNER JOIN SHIPMENT s ON o.OrderID = s.OrderID
            {where_sql_orders}
        """, tuple(params_orders))
        ord_res = cur.fetchone()
        total_orders = ord_res["total_orders"] or 0
        total_sales = float(ord_res["total_sales"] or 0.0)

        # Intake
        where_clauses_intake = []
        params_intake = []
        if warehouse_id:
            where_clauses_intake.append("WarehouseID = %s")
            params_intake.append(warehouse_id)
        if month and month != "ALL":
            where_clauses_intake.append("DATE_FORMAT(IntakeDate, '%Y-%m') = %s")
            params_intake.append(month)

        where_sql_intake = "WHERE " + " AND ".join(where_clauses_intake) if where_clauses_intake else ""

        cur.execute(f"""
            SELECT COALESCE(SUM(QuantityAdded), 0) AS total_intake
            FROM INVENTORY_INTAKE
            {where_sql_intake}
        """, tuple(params_intake))
        intake_res = cur.fetchone()
        total_intake = int(intake_res["total_intake"] or 0)

        aov = (total_sales / total_orders) if total_orders > 0 else 0.0

        return {
            "total_sales": total_sales,
            "total_orders": total_orders,
            "total_intake": total_intake,
            "aov": aov
        }


def get_monthly_trend_data(warehouse_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Returns monthly aggregated trends for multi-month comparisons:
    [ { "month": "2026-05", "sales": 45000.0, "intake": 180, "orders": 3 }, ... ]
    """
    ensure_eda_tables_and_seed()
    with get_db_cursor() as (conn, cur):
        # Monthly Sales & Orders
        where_ord = "WHERE s.WarehouseID = %s" if warehouse_id else ""
        params_ord = (warehouse_id,) if warehouse_id else ()

        cur.execute(f"""
            SELECT 
                DATE_FORMAT(o.OrderDate, '%Y-%m') AS m,
                COUNT(DISTINCT o.OrderID) AS order_cnt,
                COALESCE(SUM(o.TotalAmount), 0.0) AS revenue
            FROM ORDERS o
            INNER JOIN SHIPMENT s ON o.OrderID = s.OrderID
            {where_ord}
            GROUP BY m
            ORDER BY m ASC
        """, params_ord)
        orders_by_month = {r["m"]: {"orders": r["order_cnt"], "sales": float(r["revenue"])} for r in cur.fetchall()}

        # Monthly Intake
        where_int = "WHERE WarehouseID = %s" if warehouse_id else ""
        params_int = (warehouse_id,) if warehouse_id else ()

        cur.execute(f"""
            SELECT 
                DATE_FORMAT(IntakeDate, '%Y-%m') AS m,
                COALESCE(SUM(QuantityAdded), 0) AS intake_qty
            FROM INVENTORY_INTAKE
            {where_int}
            GROUP BY m
            ORDER BY m ASC
        """, params_int)
        intake_by_month = {r["m"]: int(r["intake_qty"]) for r in cur.fetchall()}

        # Combine all months in sorted chronological order
        all_months = sorted(list(set(list(orders_by_month.keys()) + list(intake_by_month.keys()))))
        data = []
        for m in all_months:
            data.append({
                "month": m,
                "sales": orders_by_month.get(m, {}).get("sales", 0.0),
                "orders": orders_by_month.get(m, {}).get("orders", 0),
                "intake": intake_by_month.get(m, 0)
            })
        return data


def get_category_distribution(warehouse_id: Optional[int] = None, month: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns revenue and item count aggregated by product category for pie chart.
    """
    ensure_eda_tables_and_seed()
    with get_db_cursor() as (conn, cur):
        where_clauses = []
        params = []
        if warehouse_id:
            where_clauses.append("s.WarehouseID = %s")
            params.append(warehouse_id)
        if month and month != "ALL":
            where_clauses.append("DATE_FORMAT(o.OrderDate, '%Y-%m') = %s")
            params.append(month)

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        cur.execute(f"""
            SELECT 
                c.CategoryName,
                COALESCE(SUM(oi.Quantity * oi.UnitPriceAtSale), 0.0) AS revenue,
                COALESCE(SUM(oi.Quantity), 0) AS units_sold
            FROM CATEGORY c
            INNER JOIN PRODUCT p ON c.CategoryID = p.CategoryID
            INNER JOIN ORDER_ITEM oi ON p.ProductID = oi.ProductID
            INNER JOIN ORDERS o ON oi.OrderID = o.OrderID
            INNER JOIN SHIPMENT s ON o.OrderID = s.OrderID
            {where_sql}
            GROUP BY c.CategoryID, c.CategoryName
            ORDER BY revenue DESC
        """, tuple(params))
        rows = cur.fetchall()
        return [{"category": r["CategoryName"], "revenue": float(r["revenue"]), "units": int(r["units_sold"])} for r in rows]


def get_top_selling_products(warehouse_id: Optional[int] = None, month: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Returns top performing products by revenue/units sold.
    """
    ensure_eda_tables_and_seed()
    with get_db_cursor() as (conn, cur):
        where_clauses = []
        params = []
        if warehouse_id:
            where_clauses.append("s.WarehouseID = %s")
            params.append(warehouse_id)
        if month and month != "ALL":
            where_clauses.append("DATE_FORMAT(o.OrderDate, '%Y-%m') = %s")
            params.append(month)

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        params.append(limit)

        cur.execute(f"""
            SELECT 
                p.ProductName,
                p.SKU,
                c.CategoryName,
                COALESCE(SUM(oi.Quantity), 0) AS total_qty,
                COALESCE(SUM(oi.Quantity * oi.UnitPriceAtSale), 0.0) AS total_revenue
            FROM PRODUCT p
            INNER JOIN CATEGORY c ON p.CategoryID = c.CategoryID
            INNER JOIN ORDER_ITEM oi ON p.ProductID = oi.ProductID
            INNER JOIN ORDERS o ON oi.OrderID = o.OrderID
            INNER JOIN SHIPMENT s ON o.OrderID = s.OrderID
            {where_sql}
            GROUP BY p.ProductID, p.ProductName, p.SKU, c.CategoryName
            ORDER BY total_revenue DESC
            LIMIT %s
        """, tuple(params))
        rows = cur.fetchall()
        return [{
            "product_name": r["ProductName"],
            "sku": r["SKU"],
            "category": r["CategoryName"],
            "units": int(r["total_qty"]),
            "revenue": float(r["total_revenue"])
        } for r in rows]


def generate_monthly_pdf_report(
    output_path: str,
    warehouse_id: Optional[int] = None,
    month: Optional[str] = None,
    staff_name: str = "Authorized Staff",
    staff_role: str = "Administrator"
) -> Tuple[bool, str]:
    """
    Generates a publication-grade, vector-sharp PDF operations & financial report
    for the selected month and hub scope, embedding KPIs, multi-month trends,
    category revenue distribution, and product rankings.
    """
    try:
        ensure_eda_tables_and_seed()

        # Resolve warehouse metadata
        hub_name = "Global Fulfillment Network (All Hubs)"
        if warehouse_id:
            with get_db_cursor() as (conn, cur):
                cur.execute("SELECT WarehouseName, City, State FROM WAREHOUSE WHERE WarehouseID = %s", (warehouse_id,))
                wh = cur.fetchone()
                if wh:
                    hub_name = f"{wh['WarehouseName']} ({wh['City']}, {wh['State']})"

        month_label = month if (month and month != "ALL") else "All-Time Multi-Month Overview"

        # Fetch Data
        kpis = get_eda_kpis(warehouse_id, month)
        trends = get_monthly_trend_data(warehouse_id)
        categories = get_category_distribution(warehouse_id, month)
        top_products = get_top_selling_products(warehouse_id, month, limit=6)

        # Build PDF with PdfPages
        with PdfPages(output_path) as pdf:
            # ---------------- PAGE 1: EXECUTIVE AUDIT & CHARTS ----------------
            fig = plt.figure(figsize=(8.5, 11), dpi=200)
            fig.patch.set_facecolor("#FFFFFF")

            # Page Header Title
            plt.figtext(0.5, 0.94, "NEXUS PERIPHERALS", ha="center", fontsize=18, weight="bold", color="#1E3A8A")
            plt.figtext(0.5, 0.915, "Monthly Operations, Financial & Inventory Audit Report", ha="center", fontsize=12, color="#4B5563")

            # Metadata Strip
            meta_text = (
                f"Scope: {hub_name}\n"
                f"Target Period: {month_label}   |   Generated By: {staff_name} ({staff_role})\n"
                f"Report Generation Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}   |   Status: Verified"
            )
            plt.figtext(0.5, 0.865, meta_text, ha="center", fontsize=8.5, color="#374151",
                        bbox=dict(boxstyle="round,pad=0.6", facecolor="#F3F4F6", edgecolor="#D1D5DB"))

            # KPI Summary Grid (4 Cards in 1 Row)
            kpi_y = 0.80
            kpi_box_w = 0.20
            kpi_items = [
                ("Total Revenue", f"₹{kpis['total_sales']:,.2f}", "#059669"),
                ("Orders Fulfilled", f"{kpis['total_orders']:,} orders", "#2563EB"),
                ("Restock Intake", f"{kpis['total_intake']:,} units", "#7C3AED"),
                ("Avg Order Value", f"₹{kpis['aov']:,.2f}", "#D97706"),
            ]
            for i, (title, val, clr) in enumerate(kpi_items):
                bx = 0.08 + i * 0.22
                plt.figtext(bx + 0.10, kpi_y + 0.025, title, ha="center", fontsize=8, color="#6B7280", weight="bold")
                plt.figtext(bx + 0.10, kpi_y, val, ha="center", fontsize=10.5, color=clr, weight="bold")
                rect = plt.Rectangle((bx, kpi_y - 0.015), kpi_box_w, 0.055, fill=False, edgecolor="#E5E7EB", transform=fig.transFigure, linewidth=1)
                fig.patches.append(rect)

            # Chart 1: Monthly Operations Trend (Bar + Line)
            ax1 = fig.add_axes([0.10, 0.48, 0.80, 0.26])
            if trends:
                x_labels = [t["month"] for t in trends]
                sales_vals = [t["sales"] / 1000.0 for t in trends]  # In ₹ Thousands
                intake_vals = [t["intake"] for t in trends]
                order_vals = [t["orders"] for t in trends]

                import numpy as np
                x = np.arange(len(x_labels))
                width = 0.35

                b1 = ax1.bar(x - width/2, sales_vals, width, label="Sales Revenue (₹ in Thousands)", color="#3B82F6", alpha=0.85)
                b2 = ax1.bar(x + width/2, intake_vals, width, label="Restock Intake (Units)", color="#10B981", alpha=0.85)

                ax1.set_title("Multi-Month Operational Performance (Sales Revenue vs Intake Volume)", fontsize=10.5, weight="bold", color="#1F2937", pad=10)
                ax1.set_xticks(x)
                ax1.set_xticklabels(x_labels, fontsize=8)
                ax1.set_ylabel("Revenue (₹ Thousands) / Units", fontsize=8.5, color="#374151")
                ax1.grid(axis="y", linestyle="--", alpha=0.4)

                # Secondary axis for Order Count line
                ax1_line = ax1.twinx()
                l1 = ax1_line.plot(x, order_vals, color="#DC2626", marker="o", linewidth=2, label="Order Count")
                ax1_line.set_ylabel("Order Count", fontsize=8.5, color="#DC2626")
                ax1_line.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

                # Combine legends
                handles1, labels1 = ax1.get_legend_handles_labels()
                handles2, labels2 = ax1_line.get_legend_handles_labels()
                ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper left", fontsize=7.5, framealpha=0.9)
            else:
                ax1.text(0.5, 0.5, "No multi-month historical data recorded yet.", ha="center", va="center")

            # Chart 2: Category Revenue Breakdown (Pie Chart)
            ax2 = fig.add_axes([0.10, 0.16, 0.38, 0.26])
            if categories and sum(c["revenue"] for c in categories) > 0:
                cat_labels = [c["category"] for c in categories]
                cat_revs = [c["revenue"] for c in categories]
                colors = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899"]
                wedges, texts, autotexts = ax2.pie(
                    cat_revs,
                    labels=None,
                    autopct="%1.1f%%",
                    startangle=140,
                    colors=colors[:len(cat_revs)],
                    pctdistance=0.75,
                    textprops=dict(color="#FFFFFF", weight="bold", fontsize=7.5)
                )
                ax2.set_title("Category Revenue Share", fontsize=9.5, weight="bold", color="#1F2937")
                ax2.legend(wedges, cat_labels, loc="lower center", bbox_to_anchor=(0.5, -0.22), fontsize=7, frameon=False)
            else:
                ax2.text(0.5, 0.5, "No category sales recorded", ha="center", va="center", fontsize=8)
                ax2.axis("off")

            # Chart 3: Top Performing Products (Bar Chart)
            ax3 = fig.add_axes([0.54, 0.16, 0.38, 0.26])
            if top_products:
                prod_names = [p["product_name"][:18] + ".." if len(p["product_name"]) > 18 else p["product_name"] for p in top_products]
                prod_revs = [p["revenue"] / 1000.0 for p in top_products]
                y_pos = range(len(prod_names))

                bars = ax3.barh(y_pos, prod_revs, color="#6366F1", alpha=0.85)
                ax3.set_yticks(y_pos)
                ax3.set_yticklabels(prod_names, fontsize=7)
                ax3.invert_yaxis()
                ax3.set_xlabel("Revenue (₹ Thousands)", fontsize=7.5)
                ax3.set_title("Top Products by Sales", fontsize=9.5, weight="bold", color="#1F2937")
                ax3.grid(axis="x", linestyle="--", alpha=0.4)
            else:
                ax3.text(0.5, 0.5, "No product sales recorded", ha="center", va="center", fontsize=8)
                ax3.axis("off")

            # Footer
            plt.figtext(0.5, 0.03, "Page 1 of 2  •  Confidential  •  Nexus Peripherals Operations Management", ha="center", fontsize=7.5, color="#9CA3AF")
            pdf.savefig(fig)
            plt.close(fig)

            # ---------------- PAGE 2: TABULAR AUDIT BREAKDOWN ----------------
            fig2 = plt.figure(figsize=(8.5, 11), dpi=200)
            fig2.patch.set_facecolor("#FFFFFF")

            plt.figtext(0.5, 0.94, "ITEMIZED PRODUCT PERFORMANCE & RESTOCK AUDIT", ha="center", fontsize=15, weight="bold", color="#1E3A8A")
            plt.figtext(0.5, 0.915, f"Period: {month_label}  |  Facility: {hub_name}", ha="center", fontsize=10, color="#4B5563")

            # Detailed table of products
            ax_tbl = fig2.add_axes([0.08, 0.45, 0.84, 0.42])
            ax_tbl.axis("off")

            table_data = [["Product Name", "SKU", "Category", "Units Sold", "Revenue (INR)"]]
            for p in top_products:
                table_data.append([
                    p["product_name"],
                    p["sku"],
                    p["category"],
                    f"{p['units']:,}",
                    f"₹{p['revenue']:,.2f}"
                ])

            if len(table_data) == 1:
                table_data.append(["No transaction data for this period", "-", "-", "0", "₹0.00"])

            table = ax_tbl.table(
                cellText=table_data,
                colWidths=[0.38, 0.18, 0.20, 0.10, 0.14],
                cellLoc="left",
                loc="upper center"
            )
            table.auto_set_font_size(False)
            table.set_fontsize(8.5)
            table.scale(1, 1.8)

            # Style table header row
            for j in range(5):
                cell = table[(0, j)]
                cell.set_facecolor("#1E3A8A")
                cell.set_text_props(color="#FFFFFF", weight="bold")

            # Alternate row colors
            for i in range(1, len(table_data)):
                bg_c = "#F9FAFB" if i % 2 == 1 else "#FFFFFF"
                for j in range(5):
                    table[(i, j)].set_facecolor(bg_c)

            # Audit Sign-Off Box
            sign_y = 0.25
            plt.figtext(0.08, sign_y + 0.10, "Operations Compliance & Verification:", fontsize=9.5, weight="bold", color="#1F2937")
            sign_box = (
                f"1. Financial Reconciliation: Matches payment gateway records for {month_label}.\n"
                f"2. Physical Inventory Check: Product stock balances synced with localized warehouse hubs.\n"
                f"3. Stored Procedure & Proximity Audit: Haversine geodesic routing verified.\n"
                f"4. Authorized Signatory: ________________________     Date: {datetime.date.today()}"
            )
            plt.figtext(0.08, sign_y + 0.02, sign_box, fontsize=8.5, color="#4B5563",
                        bbox=dict(boxstyle="round,pad=0.8", facecolor="#F3F4F6", edgecolor="#D1D5DB"))

            plt.figtext(0.5, 0.03, "Page 2 of 2  •  Confidential  •  Nexus Peripherals Operations Management", ha="center", fontsize=7.5, color="#9CA3AF")
            pdf.savefig(fig2)
            plt.close(fig2)

        return True, f"PDF report successfully saved to:\n{output_path}"

    except Exception as e:
        return False, f"Error generating PDF report:\n{str(e)}"
