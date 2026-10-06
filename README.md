# Nexus Peripherals - Multi-Warehouse E-Commerce and Inventory Management System

**Course Specification:** BACSE202 Database Systems  
**Domain:** Enthusiast Mechanical Keyboard Components and Hardware Peripherals  
**Database:** MySQL 8.0 (InnoDB, Strict Foreign Key and Check Constraints, ACID Isolation)  
**Application Layer:** Python 3.x (mysql-connector-python, Tkinter / ttk)

---

## 1. Project Overview

Nexus Peripherals is an enterprise-grade e-commerce order management and multi-hub inventory routing platform engineered for mechanical keyboard components (custom aluminum keyboard kits, hot-swappable PCB decks, mechanical switches, keycap sets, and modding lubricants).

### Key Architectural Highlights:
1. **Three Distinct Role-Based Portals:**
   * **Customer Portal:**
     - Dynamic registration and authentication with SHA-256 password hashing.
     - Live catalog browser in Indian Rupees (INR / Rs).
     - Multi-item shopping cart with quantity adjustments.
     - Nearest-warehouse checkout with Haversine proximity routing preview.
     - Personal order history and tracking numbers.
   * **Warehouse Manager Portal:**
     - Stationed at a physical hub (Chennai, Bengaluru, Mumbai).
     - Monitors localized stock levels for their assigned WarehouseID in PRODUCT_INVENTORY.
     - One-click restock action for low inventory (UPDATE PRODUCT_INVENTORY.StockQuantity).
     - Views incoming hub dispatch orders and updates SHIPMENT status (PREPARING -> IN_TRANSIT -> OUT_FOR_DELIVERY -> DELIVERED).
   * **System Administrator (Admin) Portal:**
     - Full administrative access across all tables.
     - Live platform KPI metrics (Total Platform Revenue in INR, Total Orders, Active SKUs, Low Stock count).
     - Add new mechanical keyboard components to PRODUCT with SKU and INR pricing.
     - Add new product categories to CATEGORY.
     - Expand fulfillment network by adding new WAREHOUSE facilities with geodesic coordinates.
     - Global order ledger and shipment dispatch tracking across all customers.

2. **Dynamic Customer Authentication:**
   * The CUSTOMER table starts completely empty (no mock or pre-seeded customers).
   * Dynamic registration accepts user credentials, hashes passwords via SHA-256, maps delivery coordinates, and persists records directly to MySQL 8.0.

3. **Multi-Warehouse Segregated Inventory:**
   * Three strategic fulfillment hubs with exact geographical coordinates:
     - South Fulfillment Hub (Chennai): 13.0827 N, 80.2707 E
     - Tech Corridor Warehouse (Bengaluru): 12.9716 N, 77.5946 E
     - West Distribution Center (Mumbai): 19.0760 N, 72.8777 E
   * Real-time stock counts are isolated per product and per warehouse in PRODUCT_INVENTORY.

4. **Nearest-Warehouse Proximity Routing Engine:**
   * Evaluates geodesic distances using the Haversine formula between customer delivery coordinates and fulfillment hubs holding sufficient inventory.
   * Dispatches orders automatically from the closest hub holding 100% of all items in the cart.
   * If the closest hub has insufficient stock, the engine gracefully reroutes to the next closest eligible warehouse.

5. **Strict ACID Order Fulfillment Transactions:**
   * Executes multi-table atomic operations encompassing ORDERS, ORDER_ITEM, PAYMENT, SHIPMENT, and PRODUCT_INVENTORY.
   * Utilizes SELECT ... FOR UPDATE row-level locks on stock rows and executes clean rollbacks if stock falls below requested order quantities.

---

## 2. Directory Structure

```text
e_commerce_and_inventory_management/
├── frontend/
│   ├── app.py                  # Full-featured Tkinter/ttk desktop GUI application with 3 role portals
│   └── __init__.py             # Frontend package initializer
├── db/
│   ├── 01_schema.sql           # DDL schema (10 normalized tables, cascading constraints, CHECK clauses)
│   ├── 02_seed_data.sql        # Baseline categories, 10 keyboard components, 3 warehouse hubs, staff users
│   ├── 03_procedures_views.sql # Dynamic SQL views (vw_ProductCatalog, vw_WarehouseStockBreakdown, etc.)
│   └── __init__.py             # Database scripts package initializer
├── db_integration/
│   ├── db.py                   # Centralized connection pool, cursor context managers, config loader
│   ├── proximity.py            # Haversine distance calculator and multi-warehouse cart routing engine
│   └── __init__.py             # Database integration package initializer
├── tests/
│   ├── test_db.py              # Automated unit and integration test suite (10 comprehensive test cases)
│   └── __init__.py             # Tests package initializer
├── run.py                      # Root application entrypoint launcher
├── requirements.txt            # Dependency specification (mysql-connector-python>=8.0.30)
├── .gitignore                  # Git ignore rules for Python bytecode and environment files
└── README.md                   # Complete architectural documentation and execution guide
```

---

## 3. Database Architecture and Schema Specification

The schema complies with Third Normal Form (3NF) and enforces referential integrity via the MySQL InnoDB storage engine.

```text
                      +-------------------+
                      |     CATEGORY      |
                      +-------------------+
                                | 1
                                |
                                | M
                      +-------------------+           +-----------------------+
                      |      PRODUCT      |-----------|   PRODUCT_INVENTORY   |
                      +-------------------+ 1       M +-----------------------+
                                |                             | M
                                | 1                           |
                                |                             | 1
                                | M                   +-----------------------+
                      +-------------------+           |       WAREHOUSE       |
       +--------------|    ORDER_ITEM     |           +-----------------------+
       |              +-------------------+                       | 1
       |                        | M                               |
       |                        |                                 |
       |                        | 1                               |
+--------------+      +-------------------+                       |
|   CUSTOMER   |------|      ORDERS       |                       |
+--------------+ 1  M +-------------------+                       |
                                | 1                               |
               +----------------+----------------+                |
               | 1                               | 1              |
       +---------------+                 +---------------+        |
       |    PAYMENT    |                 |   SHIPMENT    |--------+
       +---------------+                 +---------------+ M
```

### Table Definitions:

1. **CATEGORY**: Product groupings (`CategoryID`, `CategoryName`, `Description`).
2. **CUSTOMER**: Dynamically registered end-users (`CustomerID`, `FullName`, `Email`, `PasswordHash`, `Phone`, `City`, `Latitude`, `Longitude`, `ShippingAddress`). Starts empty.
3. **PRODUCT**: Mechanical keyboard hardware SKUs (`ProductID`, `CategoryID`, `SKU`, `ProductName`, `UnitPrice`, `Description`). Unit prices denominated in INR (Rs).
4. **WAREHOUSE**: Regional distribution hubs (`WarehouseID`, `WarehouseName`, `City`, `State`, `Latitude`, `Longitude`, `Capacity`).
5. **STAFF_USER**: Hub managers and administrators (`StaffID`, `Username`, `FullName`, `Email`, `PasswordHash`, `Role`, `AssignedWarehouseID`).
6. **PRODUCT_INVENTORY**: Per-warehouse segregated stock levels (`InventoryID`, `ProductID`, `WarehouseID`, `StockQuantity`, `ReorderLevel`, `LastRestocked`).
7. **ORDERS**: Parent transaction headers (`OrderID`, `CustomerID`, `OrderDate`, `TotalAmount`, `OrderStatus`, `ShippingAddress`).
8. **ORDER_ITEM**: Individual product line items (`OrderItemID`, `OrderID`, `ProductID`, `Quantity`, `UnitPriceAtSale`).
9. **PAYMENT**: Financial settlement records (`PaymentID`, `OrderID`, `PaymentDate`, `PaymentMethod`, `AmountPaid`, `PaymentStatus`).
10. **SHIPMENT**: Logistics fulfillment and tracking (`ShipmentID`, `OrderID`, `WarehouseID`, `TrackingNumber`, `DispatchedDate`, `DeliveryStatus`).

---

## 4. Nearest-Warehouse Proximity Routing (Haversine Formula)

When a customer initiates order checkout, the distance to each candidate warehouse holding sufficient stock is computed via the spherical Haversine formula:

$$\Delta\sigma = 2 \arcsin \left( \sqrt{ \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right) } \right)$$

$$d = R \cdot \Delta\sigma$$

Where:
- $\phi_1, \phi_2$ = Latitudes of customer and warehouse in radians
- $\Delta\phi = \phi_2 - \phi_1$
- $\Delta\lambda = \lambda_2 - \lambda_1$ (difference in longitudes)
- $R = 6371.0 \text{ km}$ (mean Earth radius)

### Cart-Level Proximity Routing Logic:
1. Identify all warehouses in the network holding 100% of the requested items and quantities.
2. Calculate the Haversine distance from the customer's coordinates to each candidate warehouse.
3. Select the closest warehouse as the primary fulfillment hub.
4. If the closest hub has insufficient stock for even one cart item, the engine automatically falls back to the next closest eligible hub.

---

## 5. ACID Transaction Fulfillment Protocol

Order checkout is wrapped inside a single atomic database transaction:

```text
[START TRANSACTION]
   |
   +---> For each item in cart:
   |        SELECT StockQuantity FROM PRODUCT_INVENTORY
   |        WHERE ProductID = ? AND WarehouseID = ? FOR UPDATE;
   |        (Verify StockQuantity >= Quantity)
   |        IF insufficient -> [ROLLBACK & RETURN ERROR]
   |
   +---> For each item in cart:
   |        UPDATE PRODUCT_INVENTORY
   |        SET StockQuantity = StockQuantity - ?
   |        WHERE ProductID = ? AND WarehouseID = ?;
   |
   +---> INSERT INTO ORDERS (CustomerID, TotalAmount, OrderStatus, ShippingAddress);
   |     (Obtain OrderID)
   |
   +---> For each item in cart:
   |        INSERT INTO ORDER_ITEM (OrderID, ProductID, Quantity, UnitPriceAtSale);
   |
   +---> INSERT INTO PAYMENT (OrderID, PaymentMethod, AmountPaid, PaymentStatus);
   |
   +---> INSERT INTO SHIPMENT (OrderID, WarehouseID, TrackingNumber, DeliveryStatus);
   |
[COMMIT TRANSACTION]
```

If any failure, network error, or inventory depletion occurs during processing, the transaction executes a complete ROLLBACK, writing 0 records to the database.

---

## 6. Installation and Setup

### Prerequisites:
- Python 3.9+
- MySQL Server 8.0+
- MySQL Connector for Python

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Database Setup
1. Launch MySQL Command Line Client or MySQL Workbench.
2. Execute the scripts in order from the `db/` folder:
   ```sql
   SOURCE db/01_schema.sql;
   SOURCE db/02_seed_data.sql;
   SOURCE db/03_procedures_views.sql;
   ```
   *(Or use the in-app "DB Settings / Reset" tool to initialize the schema with one click).*

### Step 3: Run the Application
From the repository root:
```bash
python run.py
```
*(Or navigate to `frontend/` and run `python app.py`)*

---

## 7. Automated Test Suite

Run the automated integration and unit test suite verifying schema constraints, proximity math, ACID rollback, role-based access, and cart fulfillment:

```bash
python -m unittest tests/test_db.py
```

All 10 tests run in under 1 second against MySQL 8.0.

---

## 8. Default Staff Test Credentials

| Role | Username / Email | Password | Assigned Scope |
| :--- | :--- | :--- | :--- |
| System Administrator | admin | admin123 | Full Platform Oversight across all 10 tables |
| Warehouse Manager | manager_chennai | chennai123 | South Fulfillment Hub (Chennai) |
| Warehouse Manager | manager_bengaluru | bengaluru123 | Tech Corridor Warehouse (Bengaluru) |
| Warehouse Manager | manager_mumbai | mumbai123 | West Distribution Center (Mumbai) |
| Warehouse Manager | samarth@gmail.com | manager123 | Chennai Hub Manager Operations |

*(Customer accounts start empty and can be registered dynamically through the Customer Portal).*

---

## 9. Exploratory Data Analysis and Audit Reporting

The system features an integrated Exploratory Data Analysis (EDA) dashboard accessible by Warehouse Managers and System Administrators:

1. Visual Metrics:
   - Monthly Operations Trend: Dual-axis comparative analysis of Sales Revenue (INR in thousands), Restock Intake Volume (Units), and Order Frequency.
   - Category Revenue Distribution: Interactive pie chart displaying revenue share across Mechanical Keyboards, Switches, and Keycaps.
   - Top Performing Products: Ranking of top-selling SKUs by gross revenue and unit volume.

2. Scoped Role Access:
   - Warehouse Managers: Analytics are automatically isolated to their assigned fulfillment facility.
   - System Administrators: Network-wide global analytics with the option to filter by specific hubs.

3. Monthly Audit PDF Generation:
   - Hub Managers and Admins can export publication-grade, vector-sharp PDF reports for any specific month or full annual periods.
   - Each report contains formal metadata, executive financial KPI summaries, embedded high-resolution visual plots, itemized product sales tables, and an audit compliance sign-off.

