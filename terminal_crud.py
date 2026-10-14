"""
Nexus Peripherals - Terminal Database Interfacing & Multi-Role Control Suite
Course: BACSE202 Database Systems (VIT SCOPE) - Review 2 / Assessment 9

Features:
1. Three Distinct Role-Based Portals:
   - [1] Customer Portal (Dynamic Registration, SHA-256 Auth, Catalog, Proximity Routing, ACID Checkout, Order Tracking)
   - [2] Warehouse Manager Portal (Hub-scoped Stock Monitoring, Restock DML, Shipment Status Transitions)
   - [3] System Administrator Portal (Platform KPIs, SKU Insertion, Category Management, Constraint Tests)
2. Interactive input for all parameters with sensible default suggestions for quick evaluation.
3. Pure standard-library ASCII tables, clear SQL query displays, row counts, and error trapping.
"""

import sys
import os
import hashlib
import uuid
import datetime

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db_integration.db import get_db_connection, get_db_cursor, test_connection, DEFAULT_CONFIG
from db_integration.proximity import CITY_COORDINATES, calculate_haversine_distance, compute_warehouse_fulfillment


def print_banner(title: str, subtitle: str = ""):
    width = 80
    print("\n" + "=" * width)
    print(f"  {title.center(width - 4)}")
    if subtitle:
        print(f"  {subtitle.center(width - 4)}")
    print("=" * width)


def print_query(sql: str, params=None):
    print("\n\033[96m[EXECUTING SQL QUERY]:\033[0m")
    lines = sql.strip().split("\n")
    for line in lines:
        print(f"  \033[93m{line}\033[0m")
    if params:
        print(f"  \033[90mParameters: {params}\033[0m")
    print("-" * 80)


def print_table(rows, headers=None):
    """Prints a list of dictionaries or tuples as a clean ASCII table."""
    if not rows:
        print("\033[90m(0 rows returned)\033[0m")
        return

    if isinstance(rows[0], dict):
        if not headers:
            headers = list(rows[0].keys())
        data = [[str(r.get(h, '')) for h in headers] for r in rows]
    else:
        if not headers:
            headers = [f"Col {i+1}" for i in range(len(rows[0]))]
        data = [[str(c) if c is not None else 'NULL' for c in r] for r in rows]

    col_widths = [len(h) for h in headers]
    for row in data:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))

    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    hdr = "|" + "|".join(f" {headers[i].ljust(col_widths[i])} " for i in range(len(headers))) + "|"
    print(sep)
    print(hdr)
    print(sep)
    for row in data:
        line = "|" + "|".join(f" {row[i].ljust(col_widths[i])} " for i in range(len(row))) + "|"
        print(line)
    print(sep)
    print(f"\033[92mTotal Rows: {len(rows)}\033[0m\n")


def prompt_str(label: str, default: str = "") -> str:
    if default:
        res = input(f"{label} [{default}]: ").strip()
        return res if res else default
    while True:
        res = input(f"{label}: ").strip()
        if res:
            return res
        print("\033[91mInput cannot be empty. Please enter a value.\033[0m")


def prompt_int(label: str, default: int = 1) -> int:
    while True:
        res = input(f"{label} [{default}]: ").strip()
        if not res:
            return default
        try:
            return int(res)
        except ValueError:
            print("\033[91mPlease enter a valid integer.\033[0m")


def prompt_float(label: str, default: float = 0.0) -> float:
    while True:
        res = input(f"{label} [{default}]: ").strip()
        if not res:
            return default
        try:
            return float(res)
        except ValueError:
            print("\033[91mPlease enter a valid decimal number.\033[0m")


# ==============================================================================
# PORTAL 1: CUSTOMER PORTAL
# ==============================================================================

def customer_register() -> dict:
    print_banner("CUSTOMER REGISTRATION", "Dynamic User Creation with SHA-256 Password Hashing")
    print("Please enter customer information:")
    name = prompt_str("  Full Name", "Harshith Antyakula")
    def_email = f"user_{uuid.uuid4().hex[:4]}@vitstudent.ac.in"
    email = prompt_str("  Email Address", def_email)
    password = prompt_str("  Password", "VITPassword2026!")
    phone = prompt_str("  Phone Number", "9876543210")
    city = prompt_str("  Delivery City", "Vellore")
    
    def_lat, def_lon = CITY_COORDINATES.get(city, (12.9165, 79.1325))
    lat = prompt_float(f"  Latitude for {city}", def_lat)
    lon = prompt_float(f"  Longitude for {city}", def_lon)
    address = prompt_str("  Shipping Address", f"VIT Main Campus, {city}, Tamil Nadu")

    pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    sql = """
    INSERT INTO CUSTOMER (FullName, Email, PasswordHash, Phone, City, Latitude, Longitude, ShippingAddress)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    params = (name, email, pw_hash, phone, city, lat, lon, address)
    print_query(sql, (name, email, f"{pw_hash[:16]}...", phone, city, lat, lon, address))

    try:
        with get_db_cursor(autocommit=True) as (conn, cur):
            cur.execute(sql, params)
            cid = cur.lastrowid
            print(f"\033[92m[SUCCESS]: Customer registered! Generated CustomerID = {cid}\033[0m")
            
            cur.execute("SELECT CustomerID, FullName, Email, City, Latitude, Longitude, AccountCreatedAt FROM CUSTOMER WHERE CustomerID = %s", (cid,))
            cust_row = cur.fetchone()
            print_table([cust_row])
            return cust_row
    except Exception as e:
        print(f"\033[91m[REGISTRATION FAILED]: {e}\033[0m")
        return None


def customer_login() -> dict:
    print_banner("CUSTOMER LOGIN", "Authentication via MySQL 8.0 & SHA-256")
    
    # Check if any customers exist
    with get_db_cursor() as (conn, cur):
        cur.execute("SELECT Email FROM CUSTOMER ORDER BY CustomerID DESC LIMIT 3;")
        recent = cur.fetchall()
    
    if not recent:
        print("\033[93mNo customers found in database yet. Let's register a new customer first!\033[0m")
        return customer_register()
    
    default_email = recent[0]["Email"]
    email = prompt_str("  Enter Customer Email", default_email)
    password = prompt_str("  Enter Password", "VITPassword2026!")
    pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    sql = "SELECT CustomerID, FullName, Email, City, Latitude, Longitude, ShippingAddress FROM CUSTOMER WHERE Email = %s AND PasswordHash = %s;"
    print_query(sql, (email, f"{pw_hash[:16]}..."))

    with get_db_cursor() as (conn, cur):
        cur.execute(sql, (email, pw_hash))
        cust = cur.fetchone()
        if cust:
            print(f"\033[92m[LOGIN SUCCESS]: Welcome back, {cust['FullName']} (CustomerID #{cust['CustomerID']})!\033[0m")
            return cust
        else:
            print("\033[91m[AUTHENTICATION FAILED]: Invalid email or password.\033[0m")
            retry = prompt_str("  Would you like to register as a new customer instead? (Y/N)", "Y").upper()
            if retry == "Y":
                return customer_register()
            return None


def customer_portal():
    print_banner("CUSTOMER PORTAL INTERFACE")
    print("  [1] Login with Existing Customer Account")
    print("  [2] Register New Customer Account")
    print("  [0] Back to Main Menu")
    c_choice = prompt_str("Choose Option [0-2]", "1")
    
    if c_choice == "1":
        cust = customer_login()
    elif c_choice == "2":
        cust = customer_register()
    else:
        return

    if not cust:
        return

    while True:
        print_banner(f"CUSTOMER DASHBOARD: {cust['FullName'].upper()}", f"Delivery City: {cust['City']} | CustomerID: #{cust['CustomerID']}")
        print("  [1] Browse Mechanical Keyboard Catalog (READ View)")
        print("  [2] Check Nearest-Warehouse Distance Matrix (Haversine Routing)")
        print("  [3] Place Multi-Item Order (ACID Multi-Table Checkout)")
        print("  [4] View My Order History & Tracking (READ Join)")
        print("  [5] Update My Shipping Address (UPDATE Customer)")
        print("  [6] Cancel an Order (DELETE with Cascading Integrity)")
        print("  [0] Logout")
        print("-" * 80)
        
        act = prompt_str("Select Action [0-6]", "1")
        if act == "1":
            with get_db_cursor() as (conn, cur):
                cur.execute("SELECT ProductID, SKU, ProductName, CategoryName, UnitPrice, TotalAvailableStock FROM vw_ProductCatalog;")
                print_table(cur.fetchall())
        elif act == "2":
            lat, lon = float(cust["Latitude"]), float(cust["Longitude"])
            print(f"\nEvaluating distance from {cust['City']} ({lat}, {lon}) to all warehouses:")
            with get_db_cursor() as (conn, cur):
                cur.execute("SELECT WarehouseID, WarehouseName, City, Latitude, Longitude FROM WAREHOUSE;")
                hubs = cur.fetchall()
            rows = []
            for h in hubs:
                dist = calculate_haversine_distance(lat, lon, float(h["Latitude"]), float(h["Longitude"]))
                rows.append({
                    "WarehouseID": h["WarehouseID"],
                    "Facility": h["WarehouseName"],
                    "Hub City": h["City"],
                    "Distance (km)": f"{dist:.2f} km"
                })
            rows.sort(key=lambda x: float(x["Distance (km)"].replace(" km", "")))
            print_table(rows)
            print(f"\033[92m[OPTIMAL ROUTING]: Nearest fulfillment hub is '{rows[0]['Facility']}' ({rows[0]['Hub City']}) at {rows[0]['Distance (km)']}.\033[0m")
        elif act == "3":
            # Place order
            with get_db_cursor() as (conn, cur):
                cur.execute("SELECT ProductID, ProductName, UnitPrice, TotalAvailableStock FROM vw_ProductCatalog WHERE TotalAvailableStock > 0 LIMIT 5;")
                avail = cur.fetchall()
                print("Available Products in Catalog:")
                print_table(avail)
                pid = prompt_int("  Select ProductID to order", avail[0]["ProductID"])
                qty = prompt_int("  Enter Quantity", 1)
                
                # Check closest warehouse with stock
                cur.execute("""
                    SELECT w.WarehouseID, w.WarehouseName, w.City, w.Latitude, w.Longitude, pi.StockQuantity 
                    FROM PRODUCT_INVENTORY pi
                    JOIN WAREHOUSE w ON pi.WarehouseID = w.WarehouseID
                    WHERE pi.ProductID = %s AND pi.StockQuantity >= %s;
                """, (pid, qty))
                eligible_hubs = cur.fetchall()
                if not eligible_hubs:
                    print(f"\033[91m[OUT OF STOCK]: No warehouse in the network has {qty} units in stock!\033[0m")
                    continue
                
                # Sort by distance
                for eh in eligible_hubs:
                    eh["dist"] = calculate_haversine_distance(float(cust["Latitude"]), float(cust["Longitude"]), float(eh["Latitude"]), float(eh["Longitude"]))
                eligible_hubs.sort(key=lambda x: x["dist"])
                best_hub = eligible_hubs[0]
                print(f"\033[92m[AUTOMATED ROUTING]: Selected closest hub '{best_hub['WarehouseName']}' ({best_hub['City']}) - Distance: {best_hub['dist']:.2f} km\033[0m")
                
                pay_method = prompt_str("  Payment Method [UPI / CARD / NETBANKING / COD]", "UPI").upper()

            # Execute ACID Order Transaction
            conn = get_db_connection(autocommit=False)
            cur = conn.cursor(dictionary=True)
            try:
                wid = best_hub["WarehouseID"]
                # 1. Lock stock row
                cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = %s AND WarehouseID = %s FOR UPDATE", (pid, wid))
                curr_stk = cur.fetchone()["StockQuantity"]
                if curr_stk < qty:
                    raise ValueError(f"Stock was depleted during transaction ({curr_stk} < {qty})!")
                
                # 2. Deduct inventory
                cur.execute("UPDATE PRODUCT_INVENTORY SET StockQuantity = StockQuantity - %s WHERE ProductID = %s AND WarehouseID = %s", (qty, pid, wid))
                
                # 3. Unit price
                cur.execute("SELECT UnitPrice FROM PRODUCT WHERE ProductID = %s", (pid,))
                price = float(cur.fetchone()["UnitPrice"])
                tot = price * qty
                
                # 4. Insert Order
                cur.execute("INSERT INTO ORDERS (CustomerID, TotalAmount, OrderStatus, ShippingAddress) VALUES (%s, %s, 'PROCESSING', %s)", (cust["CustomerID"], tot, cust["ShippingAddress"]))
                oid = cur.lastrowid
                
                # 5. Insert Item
                cur.execute("INSERT INTO ORDER_ITEM (OrderID, ProductID, Quantity, UnitPriceAtSale) VALUES (%s, %s, %s, %s)", (oid, pid, qty, price))
                
                # 6. Insert Payment
                cur.execute("INSERT INTO PAYMENT (OrderID, PaymentMethod, AmountPaid, PaymentStatus) VALUES (%s, %s, %s, 'COMPLETED')", (oid, pay_method, tot))
                
                # 7. Insert Shipment
                trk = f"TRK-NEXUS-{uuid.uuid4().hex[:8].upper()}"
                cur.execute("INSERT INTO SHIPMENT (OrderID, WarehouseID, TrackingNumber, DeliveryStatus) VALUES (%s, %s, %s, 'PREPARING')", (oid, wid, trk))
                
                conn.commit()
                print(f"\033[92m[ORDER PLACED]: Order #{oid} placed successfully across 5 tables! Tracking ID: {trk}\033[0m")
                cur.execute("SELECT OrderID, CustomerName, ProductName, Quantity, TotalAmount, PaymentMethod, TrackingNumber, DeliveryStatus, DispatchedFromHub FROM vw_OrderDetailsSummary WHERE OrderID = %s", (oid,))
                print_table(cur.fetchall())
            except Exception as e:
                conn.rollback()
                print(f"\033[91m[TRANSACTION ABORTED]: {e}\033[0m")
            finally:
                cur.close()
                conn.close()

        elif act == "4":
            # View customer's orders
            with get_db_cursor() as (conn, cur):
                cur.execute("""
                    SELECT o.OrderID, o.OrderDate, p.ProductName, oi.Quantity, o.TotalAmount, o.OrderStatus, s.TrackingNumber, s.DeliveryStatus, w.WarehouseName AS DispatchedHub
                    FROM ORDERS o
                    JOIN ORDER_ITEM oi ON o.OrderID = oi.OrderID
                    JOIN PRODUCT p ON oi.ProductID = p.ProductID
                    LEFT JOIN SHIPMENT s ON o.OrderID = s.OrderID
                    LEFT JOIN WAREHOUSE w ON s.WarehouseID = w.WarehouseID
                    WHERE o.CustomerID = %s
                    ORDER BY o.OrderID DESC;
                """, (cust["CustomerID"],))
                print_table(cur.fetchall())
        elif act == "5":
            new_addr = prompt_str("  Enter New Shipping Address", "Room 302, Mens Hostel Block L, VIT Vellore")
            with get_db_cursor(autocommit=True) as (conn, cur):
                cur.execute("UPDATE CUSTOMER SET ShippingAddress = %s WHERE CustomerID = %s", (new_addr, cust["CustomerID"]))
                cust["ShippingAddress"] = new_addr
                print(f"\033[92m[SUCCESS]: Shipping address updated!\033[0m")
        elif act == "6":
            # Cancel order
            with get_db_cursor() as (conn, cur):
                cur.execute("SELECT OrderID, TotalAmount, OrderStatus FROM ORDERS WHERE CustomerID = %s ORDER BY OrderID DESC LIMIT 5", (cust["CustomerID"],))
                my_orders = cur.fetchall()
            if not my_orders:
                print("\033[93mYou have no active orders to cancel.\033[0m")
                continue
            print("Your Recent Orders:")
            print_table(my_orders)
            oid = prompt_int("  Enter OrderID to cancel", my_orders[0]["OrderID"])
            with get_db_cursor(autocommit=True) as (conn, cur):
                cur.execute("DELETE FROM ORDERS WHERE OrderID = %s AND CustomerID = %s", (oid, cust["CustomerID"]))
                print(f"\033[92m[ORDER CANCELLED]: Order #{oid} removed. Cascading deletions triggered on Items, Payment, and Shipment!\033[0m")
        elif act == "0":
            print("\nLogged out of Customer Portal.\n")
            break


# ==============================================================================
# PORTAL 2: WAREHOUSE MANAGER PORTAL
# ==============================================================================

def warehouse_manager_portal():
    print_banner("WAREHOUSE MANAGER PORTAL", "Regional Hub Operations & Localized Inventory")
    print("Pre-seeded Test Manager Credentials:")
    print("  - Chennai Hub:   Username: 'manager_chennai'   | Password: 'chennai123'")
    print("  - Bengaluru Hub: Username: 'manager_bengaluru' | Password: 'bengaluru123'")
    print("  - Mumbai Hub:    Username: 'manager_mumbai'    | Password: 'mumbai123'")
    print("-" * 80)

    username = prompt_str("  Enter Manager Username", "manager_chennai")
    password = prompt_str("  Enter Password", "chennai123")
    pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    sql = """
    SELECT s.StaffID, s.Username, s.FullName, s.Role, s.AssignedWarehouseID, w.WarehouseName, w.City
    FROM STAFF_USER s
    JOIN WAREHOUSE w ON s.AssignedWarehouseID = w.WarehouseID
    WHERE s.Username = %s AND s.PasswordHash = %s AND s.Role = 'WAREHOUSE_MANAGER';
    """
    print_query(sql, (username, f"{pw_hash[:16]}..."))

    with get_db_cursor() as (conn, cur):
        cur.execute(sql, (username, pw_hash))
        mgr = cur.fetchone()

    if not mgr:
        print("\033[91m[AUTHENTICATION FAILED]: Invalid manager credentials or role mismatch.\033[0m")
        return

    wid = mgr["AssignedWarehouseID"]
    print(f"\033[92m[LOGIN SUCCESS]: Welcome {mgr['FullName']} - Supervisor of '{mgr['WarehouseName']}' ({mgr['City']})!\033[0m")

    while True:
        print_banner(f"HUB OPERATIONS: {mgr['WarehouseName'].upper()} ({mgr['City']})", f"WarehouseID: #{wid} | Supervisor: {mgr['FullName']}")
        print("  [1] View Localized Hub Stock & Health Badges (READ)")
        print("  [2] Restock Inventory for this Hub (UPDATE DML)")
        print("  [3] View Outbound Dispatches & Shipments (READ Join)")
        print("  [4] Advance Shipment Logistics Status (UPDATE Shipment)")
        print("  [5] Run Stored Procedure Diagnostic (sp_CheckWarehouseStock)")
        print("  [0] Logout")
        print("-" * 80)

        act = prompt_str("Select Action [0-5]", "1")
        if act == "1":
            with get_db_cursor() as (conn, cur):
                cur.execute("""
                    SELECT p.ProductID, p.SKU, p.ProductName, pi.StockQuantity, pi.ReorderLevel,
                           CASE 
                               WHEN pi.StockQuantity = 0 THEN 'OUT_OF_STOCK'
                               WHEN pi.StockQuantity <= pi.ReorderLevel THEN 'LOW_STOCK'
                               ELSE 'OPTIMAL'
                           END AS StockStatus,
                           pi.LastRestocked
                    FROM PRODUCT_INVENTORY pi
                    JOIN PRODUCT p ON pi.ProductID = p.ProductID
                    WHERE pi.WarehouseID = %s
                    ORDER BY pi.StockQuantity ASC;
                """, (wid,))
                print_table(cur.fetchall())
        elif act == "2":
            # Restock
            pid = prompt_int("  Enter ProductID to restock", 1)
            add_qty = prompt_int("  Enter Quantity of Units to Add", 25)
            with get_db_cursor(autocommit=True) as (conn, cur):
                cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = %s AND WarehouseID = %s", (pid, wid))
                row = cur.fetchone()
                if not row:
                    print("\033[91mProduct not found in inventory.\033[0m")
                    continue
                old_stk = row["StockQuantity"]
                cur.execute("UPDATE PRODUCT_INVENTORY SET StockQuantity = StockQuantity + %s WHERE ProductID = %s AND WarehouseID = %s", (add_qty, pid, wid))
                cur.execute("SELECT p.ProductName, pi.StockQuantity, pi.LastRestocked FROM PRODUCT_INVENTORY pi JOIN PRODUCT p ON pi.ProductID = p.ProductID WHERE pi.ProductID = %s AND pi.WarehouseID = %s", (pid, wid))
                new_row = cur.fetchone()
                print(f"\033[92m[RESTOCKED]: '{new_row['ProductName']}' updated from {old_stk} -> {new_row['StockQuantity']} units!\033[0m")
                print_table([new_row])
        elif act == "3":
            with get_db_cursor() as (conn, cur):
                cur.execute("""
                    SELECT s.ShipmentID, s.OrderID, c.FullName AS Customer, c.City AS Destination,
                           s.TrackingNumber, s.DeliveryStatus, s.DispatchedDate
                    FROM SHIPMENT s
                    JOIN ORDERS o ON s.OrderID = o.OrderID
                    JOIN CUSTOMER c ON o.CustomerID = c.CustomerID
                    WHERE s.WarehouseID = %s
                    ORDER BY s.ShipmentID DESC
                    LIMIT 10;
                """, (wid,))
                print_table(cur.fetchall())
        elif act == "4":
            with get_db_cursor() as (conn, cur):
                cur.execute("SELECT ShipmentID, OrderID, TrackingNumber, DeliveryStatus FROM SHIPMENT WHERE WarehouseID = %s ORDER BY ShipmentID DESC LIMIT 5", (wid,))
                shps = cur.fetchall()
            if not shps:
                print("\033[93mNo shipments routed to this hub yet.\033[0m")
                continue
            print("Active Shipments:")
            print_table(shps)
            oid = prompt_int("  Enter OrderID to transition status", shps[0]["OrderID"])
            print("Status Options: [1] PREPARING  [2] IN_TRANSIT  [3] OUT_FOR_DELIVERY  [4] DELIVERED")
            st = prompt_str("Select New Status [1-4]", "2")
            st_map = {"1": "PREPARING", "2": "IN_TRANSIT", "3": "OUT_FOR_DELIVERY", "4": "DELIVERED"}
            new_st = st_map.get(st, "IN_TRANSIT")
            
            with get_db_cursor(autocommit=True) as (conn, cur):
                cur.execute("UPDATE SHIPMENT SET DeliveryStatus = %s, DispatchedDate = CURRENT_TIMESTAMP WHERE OrderID = %s AND WarehouseID = %s", (new_st, oid, wid))
                cur.execute("SELECT ShipmentID, OrderID, TrackingNumber, DispatchedDate, DeliveryStatus FROM SHIPMENT WHERE OrderID = %s", (oid,))
                print(f"\033[92m[STATUS UPDATED]: Shipment status transitioned to '{new_st}'!\033[0m")
                print_table(cur.fetchall())
        elif act == "5":
            pid = prompt_int("  Enter ProductID for stored procedure check", 1)
            with get_db_cursor() as (conn, cur):
                cur.callproc("sp_CheckWarehouseStock", (pid,))
                for res in cur.stored_results():
                    print_table(res.fetchall())
        elif act == "0":
            print("\nLogged out of Warehouse Manager Portal.\n")
            break


# ==============================================================================
# PORTAL 3: SYSTEM ADMINISTRATOR PORTAL
# ==============================================================================

def system_admin_portal():
    print_banner("SYSTEM ADMINISTRATOR PORTAL", "Network-Wide Platform Oversight & Governance")
    print("Pre-seeded Admin Credentials:")
    print("  - Username: 'admin' | Password: 'admin123'")
    print("-" * 80)

    username = prompt_str("  Enter Administrator Username", "admin")
    password = prompt_str("  Enter Administrator Password", "admin123")
    pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    sql = "SELECT StaffID, Username, FullName, Role FROM STAFF_USER WHERE Username = %s AND PasswordHash = %s AND Role = 'ADMIN';"
    print_query(sql, (username, f"{pw_hash[:16]}..."))

    with get_db_cursor() as (conn, cur):
        cur.execute(sql, (username, pw_hash))
        adm = cur.fetchone()

    if not adm:
        print("\033[91m[AUTHENTICATION FAILED]: Invalid administrator credentials.\033[0m")
        return

    print(f"\033[92m[LOGIN SUCCESS]: Welcome, System Administrator {adm['FullName']}!\033[0m")

    while True:
        print_banner("SYSTEM ADMINISTRATOR CONTROL SUITE", "Enterprise Multi-Hub Governance")
        print("  [1] Platform Executive KPI Summary (READ Aggregations)")
        print("  [2] Add New Product Hardware SKU (CREATE Product + Multi-Hub Stock)")
        print("  [3] Add New Category (CREATE Category)")
        print("  [4] Network-Wide Global Orders & Tracking Audit (READ All Hubs)")
        print("  [5] Test Referential Integrity (DELETE Category RESTRICT Constraint)")
        print("  [6] Test Domain Integrity (CHECK UnitPrice > 0 Constraint Violation)")
        print("  [7] Test ACID Rollback on Inventory Depletion (Transaction Engine)")
        print("  [0] Logout")
        print("-" * 80)

        act = prompt_str("Select Action [0-7]", "1")
        if act == "1":
            # Platform KPIs
            with get_db_cursor() as (conn, cur):
                cur.execute("SELECT COALESCE(SUM(TotalAmount), 0) AS GrossRevenueINR, COUNT(OrderID) AS TotalOrdersPlaced FROM ORDERS;")
                rev = cur.fetchone()
                cur.execute("SELECT COUNT(*) AS ActiveSKUs FROM PRODUCT;")
                skus = cur.fetchone()["ActiveSKUs"]
                cur.execute("SELECT COUNT(*) AS RegisteredCustomers FROM CUSTOMER;")
                custs = cur.fetchone()["RegisteredCustomers"]
                cur.execute("SELECT COUNT(*) AS LowStockAlerts FROM PRODUCT_INVENTORY WHERE StockQuantity <= ReorderLevel;")
                low_stk = cur.fetchone()["LowStockAlerts"]

                kpi_data = [{
                    "Metric": "Total Platform Gross Revenue",
                    "Value": f"Rs. {float(rev['GrossRevenueINR']):,.2f}"
                }, {
                    "Metric": "Total Orders Fulfilled",
                    "Value": str(rev["TotalOrdersPlaced"])
                }, {
                    "Metric": "Active Hardware SKUs",
                    "Value": str(skus)
                }, {
                    "Metric": "Registered Customer Accounts",
                    "Value": str(custs)
                }, {
                    "Metric": "Hub Low Stock Alerts",
                    "Value": f"{low_stk} warning(s)"
                }]
                print_table(kpi_data, ["Metric", "Value"])
        elif act == "2":
            # Add Product
            with get_db_cursor() as (conn, cur):
                cur.execute("SELECT CategoryID, CategoryName FROM CATEGORY;")
                print_table(cur.fetchall())
            
            sku = prompt_str("  Enter Product SKU", f"KB-CUSTOM-{uuid.uuid4().hex[:4].upper()}")
            pname = prompt_str("  Enter Product Name", "Tokyo Sakura 80% Custom Aluminum Deck")
            price = prompt_float("  Enter Unit Price (INR)", 18999.00)
            cat_id = prompt_int("  Enter CategoryID", 1)

            sql = "INSERT INTO PRODUCT (SKU, ProductName, UnitPrice, CategoryID) VALUES (%s, %s, %s, %s);"
            print_query(sql, (sku, pname, price, cat_id))
            try:
                with get_db_cursor(autocommit=True) as (conn, cur):
                    cur.execute(sql, (sku, pname, price, cat_id))
                    pid = cur.lastrowid
                    
                    # Init stock
                    q_chn = prompt_int("  Initial Stock for Chennai Hub (Warehouse 1)", 15)
                    q_blr = prompt_int("  Initial Stock for Bengaluru Hub (Warehouse 2)", 40)
                    q_bom = prompt_int("  Initial Stock for Mumbai Hub (Warehouse 3)", 25)
                    cur.execute("""
                        INSERT INTO PRODUCT_INVENTORY (ProductID, WarehouseID, StockQuantity, ReorderLevel)
                        VALUES (%s, 1, %s, 5), (%s, 2, %s, 10), (%s, 3, %s, 8);
                    """, (pid, q_chn, pid, q_blr, pid, q_bom))
                    print(f"\033[92m[SUCCESS]: Product #{pid} added and inventory initialized across 3 hubs!\033[0m")
            except Exception as e:
                print(f"\033[91m[FAILED]: {e}\033[0m")
        elif act == "3":
            cname = prompt_str("  Enter New Category Name", "Desk Mats & Wrist Rests")
            cdesc = prompt_str("  Enter Description", "Ergonomic wrist pads and high-density stitched micro-woven desk mats")
            sql = "INSERT INTO CATEGORY (CategoryName, Description) VALUES (%s, %s);"
            print_query(sql, (cname, cdesc))
            try:
                with get_db_cursor(autocommit=True) as (conn, cur):
                    cur.execute(sql, (cname, cdesc))
                    print(f"\033[92m[SUCCESS]: Category '{cname}' created!\033[0m")
                    cur.execute("SELECT * FROM CATEGORY;")
                    print_table(cur.fetchall())
            except Exception as e:
                print(f"\033[91m[FAILED]: {e}\033[0m")
        elif act == "4":
            with get_db_cursor() as (conn, cur):
                cur.execute("""
                    SELECT o.OrderID, o.OrderDate, c.FullName AS Customer, c.City AS DeliveryCity,
                           p.ProductName, oi.Quantity, o.TotalAmount, o.OrderStatus,
                           s.TrackingNumber, s.DeliveryStatus, w.WarehouseName AS DispatchedHub
                    FROM ORDERS o
                    JOIN CUSTOMER c ON o.CustomerID = c.CustomerID
                    JOIN ORDER_ITEM oi ON o.OrderID = oi.OrderID
                    JOIN PRODUCT p ON oi.ProductID = p.ProductID
                    LEFT JOIN SHIPMENT s ON o.OrderID = s.OrderID
                    LEFT JOIN WAREHOUSE w ON s.WarehouseID = w.WarehouseID
                    ORDER BY o.OrderID DESC
                    LIMIT 15;
                """)
                print_table(cur.fetchall())
        elif act == "5":
            # Delete Category RESTRICT test
            print_header("REFERENTIAL INTEGRITY: DELETE with ON DELETE RESTRICT")
            print("Attempting to delete CategoryID = 1 ('Mechanical Keyboards') which has active products.")
            sql = "DELETE FROM CATEGORY WHERE CategoryID = 1;"
            print_query(sql)
            try:
                with get_db_cursor(autocommit=True) as (conn, cur):
                    cur.execute(sql)
                    print("\033[91mERROR: Deletion was permitted!\033[0m")
            except Exception as e:
                print(f"\033[92m[RESTRICT CONSTRAINT ENFORCED]: Database rejected deletion as expected!\033[0m")
                print(f"\033[93mMySQL Error: {e}\033[0m\n")
        elif act == "6":
            # Negative price test
            print_header("DOMAIN INTEGRITY: CHECK (UnitPrice > 0) Violation")
            neg_price = prompt_float("  Enter a negative price to test check constraint", -500.00)
            sql = f"INSERT INTO PRODUCT (SKU, ProductName, UnitPrice, CategoryID) VALUES ('TEST-NEG', 'Illegal Keyboard', {neg_price}, 1);"
            print_query(sql)
            try:
                with get_db_cursor(autocommit=True) as (conn, cur):
                    cur.execute(sql)
                    print("\033[91mERROR: Database accepted negative price!\033[0m")
            except Exception as e:
                print(f"\033[92m[CHECK CONSTRAINT ENFORCED]: Database rejected negative price as expected!\033[0m")
                print(f"\033[93mMySQL Error: {e}\033[0m\n")
        elif act == "7":
            # ACID Rollback test
            print_header("ACID CONCURRENCY: Atomic Rollback on Insufficient Inventory")
            with get_db_cursor() as (conn, cur):
                cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = 1 AND WarehouseID = 1;")
                stk = cur.fetchone()["StockQuantity"]
                print(f"Current Stock of Product #1 at Chennai Hub: {stk} units")
            
            excess = prompt_int(f"  Enter order quantity to exceed stock (e.g. {stk + 100})", stk + 100)
            conn = get_db_connection(autocommit=False)
            cur = conn.cursor(dictionary=True)
            try:
                cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = 1 AND WarehouseID = 1 FOR UPDATE;")
                avail = cur.fetchone()["StockQuantity"]
                if avail < excess:
                    print(f"\033[91m[INSUFFICIENT STOCK]: Requested {excess} > Available {avail}. Executing ROLLBACK.\033[0m")
                    conn.rollback()
                    print("\033[92m[ROLLBACK COMPLETED]: Transaction cleanly aborted. 0 records modified.\033[0m")
                cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = 1 AND WarehouseID = 1;")
                post_stk = cur.fetchone()["StockQuantity"]
                print(f"Verified Stock: {post_stk} units (Intact: {post_stk == stk})\n")
            finally:
                cur.close()
                conn.close()
        elif act == "0":
            print("\nLogged out of Administrator Portal.\n")
            break


# ==============================================================================
# MAIN APPLICATION DISPATCHER
# ==============================================================================

def main():
    while True:
        print_banner(
            "NEXUS PERIPHERALS: ROLE-BASED TERMINAL DATABASE SUITE",
            "BACSE202 DBMS Course Project • MySQL 8.0 Terminal Interfacing"
        )
        print("Select Portal Interface to Enter:")
        print("  [1] Customer Portal (Register, Auth, Catalog, Proximity Checkout, Orders)")
        print("  [2] Warehouse Manager Portal (Chennai, Bengaluru, Mumbai Hub Operations)")
        print("  [3] System Administrator Portal (KPIs, Products, Constraints, Rollbacks)")
        print("  [0] Exit")
        print("-" * 80)

        portal_choice = input("Enter choice [0-3]: ").strip()
        if portal_choice == "1":
            customer_portal()
        elif portal_choice == "2":
            warehouse_manager_portal()
        elif portal_choice == "3":
            system_admin_portal()
        elif portal_choice == "0":
            print("\nExiting Nexus Peripherals Terminal Suite. Goodbye!\n")
            break
        else:
            print("\nInvalid choice. Please select 0, 1, 2, or 3.")


if __name__ == "__main__":
    main()
