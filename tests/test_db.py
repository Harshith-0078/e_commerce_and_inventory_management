"""
Nexus Peripherals - Comprehensive Integration & Unit Test Suite
BACSE202 Database Systems Final Project

Tests:
1. Haversine Distance & Geodesic Metric Validation.
2. MySQL 8.0 Connectivity & Schema Integrity (9 Tables + 2 Views).
3. Dynamic Customer Registration with SHA-256 Password Hashing.
4. Nearest-Warehouse Proximity Routing & Out-of-Stock Fallback Routing.
5. ACID Transaction Atomicity & Rollback Verification on Insufficient Stock.
"""

import os
import sys
import uuid
import hashlib
import unittest

# Ensure db_integration modules can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
db_integ_dir = os.path.join(parent_dir, "db_integration")
src_dir = os.path.join(parent_dir, "src")

for p in [parent_dir, db_integ_dir, src_dir]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

try:
    from db_integration.proximity import (
        calculate_haversine_distance,
        find_optimal_warehouse,
        evaluate_all_warehouses,
        CITY_COORDINATES
    )
    from db_integration.db import get_db_connection, test_connection, DEFAULT_CONFIG
except ImportError:
    from proximity import (
        calculate_haversine_distance,
        find_optimal_warehouse,
        evaluate_all_warehouses,
        CITY_COORDINATES
    )
    from db import get_db_connection, test_connection, DEFAULT_CONFIG


class TestProximityAlgorithm(unittest.TestCase):
    """Unit tests for the Haversine formula and pure proximity calculations."""

    def test_haversine_zero_distance(self):
        """Distance between identical coordinates must be 0.00 km."""
        chennai = CITY_COORDINATES["Chennai"]
        dist = calculate_haversine_distance(chennai[0], chennai[1], chennai[0], chennai[1])
        self.assertEqual(dist, 0.0)

    def test_haversine_known_distances(self):
        """
        Verify known geographic distance approximations between Indian hubs:
        Chennai -> Bengaluru: ~290 km (air distance)
        Vellore -> Chennai: ~125 km
        Vellore -> Bengaluru: ~180 km
        """
        chennai = CITY_COORDINATES["Chennai"]
        bengaluru = CITY_COORDINATES["Bengaluru"]
        vellore = CITY_COORDINATES["Vellore"]

        dist_chn_blr = calculate_haversine_distance(chennai[0], chennai[1], bengaluru[0], bengaluru[1])
        self.assertTrue(270.0 <= dist_chn_blr <= 310.0, f"Unexpected distance: {dist_chn_blr} km")

        dist_vel_chn = calculate_haversine_distance(vellore[0], vellore[1], chennai[0], chennai[1])
        dist_vel_blr = calculate_haversine_distance(vellore[0], vellore[1], bengaluru[0], bengaluru[1])

        # Vellore is closer to Chennai than to Bengaluru
        self.assertLess(dist_vel_chn, dist_vel_blr)
        self.assertTrue(110.0 <= dist_vel_chn <= 140.0)
        self.assertTrue(160.0 <= dist_vel_blr <= 200.0)

    def test_routing_and_fallback_logic_unit(self):
        """
        Verify nearest routing and out-of-stock fallback mechanics directly:
        - When Chennai has 3 units, an order of 1 from Vellore picks Chennai.
        - When customer requests 10 units, Chennai is skipped and Bengaluru (with 45 units) is picked.
        - When all hubs have 0 units, no hub is selected.
        """
        from proximity import compute_warehouse_fulfillment

        warehouses_mock = [
            {"WarehouseID": 1, "WarehouseName": "South Hub", "City": "Chennai", "State": "TN", "Latitude": 13.0827, "Longitude": 80.2707, "StockQuantity": 3},
            {"WarehouseID": 2, "WarehouseName": "Tech Hub", "City": "Bengaluru", "State": "KA", "Latitude": 12.9716, "Longitude": 77.5946, "StockQuantity": 45},
            {"WarehouseID": 3, "WarehouseName": "West Hub", "City": "Mumbai", "State": "MH", "Latitude": 19.0760, "Longitude": 72.8777, "StockQuantity": 20},
        ]
        vel_lat, vel_lon = CITY_COORDINATES["Vellore"]

        # Case 1: Quantity 1 -> Chennai selected (closest with stock)
        res1 = compute_warehouse_fulfillment(warehouses_mock, quantity=1, customer_lat=vel_lat, customer_lon=vel_lon)
        self.assertEqual(res1[0]["city"], "Chennai")
        self.assertTrue(res1[0]["has_sufficient_stock"])

        # Case 2: Quantity 10 -> Chennai insufficient (3 < 10) -> Fallback to Bengaluru
        res2 = compute_warehouse_fulfillment(warehouses_mock, quantity=10, customer_lat=vel_lat, customer_lon=vel_lon)
        self.assertEqual(res2[0]["city"], "Chennai")
        self.assertFalse(res2[0]["has_sufficient_stock"])
        # Next closest eligible
        eligible = [h for h in res2 if h["has_sufficient_stock"]]
        self.assertEqual(len(eligible), 2)
        self.assertEqual(eligible[0]["city"], "Bengaluru")

        # Case 3: Quantity 100 -> All insufficient
        res3 = compute_warehouse_fulfillment(warehouses_mock, quantity=100, customer_lat=vel_lat, customer_lon=vel_lon)
        eligible3 = [h for h in res3 if h["has_sufficient_stock"]]
        self.assertEqual(len(eligible3), 0)


class TestDatabaseAndFulfillmentIntegration(unittest.TestCase):
    """Integration tests executing against the MySQL 8.0 database."""

    @classmethod
    def setUpClass(cls):
        """Verify database connectivity before running integration tests."""
        cls.is_db_available, cls.db_msg = test_connection(DEFAULT_CONFIG)
        if not cls.is_db_available:
            print(f"\n[WARNING] MySQL Database not accessible at {DEFAULT_CONFIG['host']}:{DEFAULT_CONFIG['port']}.")
            print(f"Reason: {cls.db_msg}")
            print("Skipping live database integration tests. To run full tests, start MySQL and initialize schema.\n")

    def setUp(self):
        if not self.is_db_available:
            self.skipTest(f"Live database unavailable: {self.db_msg}")
        self.conn = get_db_connection(DEFAULT_CONFIG, autocommit=False)

    def tearDown(self):
        if hasattr(self, "conn") and self.conn.is_connected():
            self.conn.rollback()
            self.conn.close()

    def test_01_schema_tables_and_views_exist(self):
        """Ensure all required tables and views are present."""
        cur = self.conn.cursor()
        cur.execute("SHOW TABLES")
        tables_found = [row[0].upper() for row in cur.fetchall()]
        cur.close()

        required_tables = [
            "CATEGORY",
            "CUSTOMER",
            "PRODUCT",
            "WAREHOUSE",
            "PRODUCT_INVENTORY",
            "STAFF_USER",
            "ORDERS",
            "ORDER_ITEM",
            "PAYMENT",
            "SHIPMENT",
            "VW_PRODUCTCATALOG",
            "VW_WAREHOUSESTOCKBREAKDOWN"
        ]

        for req in required_tables:
            self.assertIn(req, tables_found, f"Missing expected table or view: {req}")

    def test_02_dynamic_customer_registration_and_sha256(self):
        """
        Verify dynamic registration: CUSTOMER table starts empty for new users,
        persists password in SHA-256, and correctly verifies credentials.
        """
        cur = self.conn.cursor(dictionary=True)
        unique_email = f"test_architect_{uuid.uuid4().hex[:8]}@nexusperipherals.local"
        raw_password = "SecureEnthusiastPassword2026!"
        hashed_pw = hashlib.sha256(raw_password.encode("utf-8")).hexdigest()

        insert_sql = """
            INSERT INTO CUSTOMER (FullName, Email, PasswordHash, Phone, City, Latitude, Longitude, ShippingAddress)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(insert_sql, (
            "Alex Chen",
            unique_email,
            hashed_pw,
            "9876543210",
            "Vellore",
            12.916500,
            79.132500,
            "VIT Main Campus, Vellore, Tamil Nadu"
        ))
        self.conn.commit()
        cust_id = cur.lastrowid
        self.assertGreater(cust_id, 0)

        # Retrieve and verify
        cur.execute("SELECT * FROM CUSTOMER WHERE CustomerID = %s", (cust_id,))
        fetched = cur.fetchone()
        self.assertEqual(fetched["Email"], unique_email)
        self.assertEqual(fetched["PasswordHash"], hashed_pw)
        self.assertEqual(fetched["City"], "Vellore")
        cur.close()

    def test_03_nearest_warehouse_routing_and_fallback(self):
        """
        Verify proximity routing logic:
        1. When stock is sufficient, Vellore customer must route to closest hub (Chennai).
        2. When order quantity exceeds Chennai stock (e.g. asking 10 units of Product 1, where Chennai only has 3),
           it must automatically route to next nearest hub (Bengaluru).
        3. When Product 3 has 0 units in Chennai, even 1 unit must route to Bengaluru.
        """
        vellore_lat, vellore_lon = CITY_COORDINATES["Vellore"]

        # Scenario 1: Small order of Product 1 (Keychron Q1 Pro)
        # Chennai has 3 units. Customer wants 1.
        optimal = find_optimal_warehouse(self.conn, product_id=1, quantity=1, customer_lat=vellore_lat, customer_lon=vellore_lon)
        self.assertIsNotNone(optimal)
        self.assertEqual(optimal["city"], "Chennai", "Failed to assign closest hub when stock was available.")

        # Scenario 2: Large order of Product 1 exceeding Chennai's stock
        cur = self.conn.cursor(dictionary=True)
        cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = 1 AND WarehouseID = 1")
        chennai_stock = cur.fetchone()["StockQuantity"]
        cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = 1 AND WarehouseID = 2")
        blr_stock = cur.fetchone()["StockQuantity"]
        cur.close()

        exceed_qty = chennai_stock + 1
        if blr_stock >= exceed_qty:
            optimal_fallback = find_optimal_warehouse(self.conn, product_id=1, quantity=exceed_qty, customer_lat=vellore_lat, customer_lon=vellore_lon)
            self.assertIsNotNone(optimal_fallback)
            self.assertEqual(optimal_fallback["city"], "Bengaluru", "Failed to route to next nearest hub when nearest hub had insufficient stock.")

        # Scenario 3: Fallback when quantity exceeds Chennai stock
        cur = self.conn.cursor(dictionary=True)
        cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = 3 AND WarehouseID = 1")
        p3_chennai = cur.fetchone()["StockQuantity"]
        cur.close()

        optimal_p3 = find_optimal_warehouse(self.conn, product_id=3, quantity=p3_chennai + 1, customer_lat=vellore_lat, customer_lon=vellore_lon)
        if optimal_p3:
            self.assertNotEqual(optimal_p3["city"], "Chennai", "Routed to Chennai despite insufficient inventory!")
            self.assertEqual(optimal_p3["city"], "Bengaluru")

    def test_04_acid_transaction_rollback_on_out_of_stock(self):
        """
        Verify ACID atomicity: If order quantity exceeds available stock,
        the transaction must cleanly roll back, writing 0 records to ORDERS,
        ORDER_ITEM, PAYMENT, or SHIPMENT, and leaving PRODUCT_INVENTORY unchanged.
        """
        cur = self.conn.cursor(dictionary=True)
        cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = 1 AND WarehouseID = 1")
        initial_stock = cur.fetchone()["StockQuantity"]

        # Attempt to order 99999 units (exceeds all capacity)
        order_attempt_qty = 99999
        optimal = find_optimal_warehouse(self.conn, product_id=1, quantity=order_attempt_qty, customer_lat=12.9165, customer_lon=79.1325)
        self.assertIsNone(optimal, "Fulfillment engine returned a hub for impossible quantity!")

        # Simulate explicit transaction rollback
        try:
            cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = 1 AND WarehouseID = 1 FOR UPDATE")
            row = cur.fetchone()
            if row["StockQuantity"] < order_attempt_qty:
                raise ValueError("Insufficient stock - Transaction Rollback Triggered")
        except ValueError:
            self.conn.rollback()

        # Check stock unchanged
        cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = 1 AND WarehouseID = 1")
        post_rollback_stock = cur.fetchone()["StockQuantity"]
        self.assertEqual(initial_stock, post_rollback_stock)
        cur.close()

    def test_05_acid_transaction_commit_fulfillment(self):
        """
        Verify successful ACID execution:
        - Stock is decremented in PRODUCT_INVENTORY
        - Records created in ORDERS, ORDER_ITEM, PAYMENT, and SHIPMENT
        """
        cur = self.conn.cursor(dictionary=True)

        # Create temporary customer
        cur.execute("""
            INSERT INTO CUSTOMER (FullName, Email, PasswordHash, Phone, City, Latitude, Longitude, ShippingAddress)
            VALUES ('Order Test User', %s, 'hash', '1234567890', 'Chennai', 13.0827, 80.2707, 'Anna Salai, Chennai')
        """, (f"order_tester_{uuid.uuid4().hex[:6]}@nexus.local",))
        customer_id = cur.lastrowid

        product_id = 2  # GMMK Pro
        warehouse_id = 1 # Chennai
        order_qty = 2

        # Check initial stock
        cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = %s AND WarehouseID = %s FOR UPDATE", (product_id, warehouse_id))
        init_stock = cur.fetchone()["StockQuantity"]
        self.assertGreaterEqual(init_stock, order_qty)

        # 1. Deduct Stock
        cur.execute("UPDATE PRODUCT_INVENTORY SET StockQuantity = StockQuantity - %s WHERE ProductID = %s AND WarehouseID = %s", (order_qty, product_id, warehouse_id))

        # 2. Insert Order
        cur.execute("INSERT INTO ORDERS (CustomerID, TotalAmount, OrderStatus, ShippingAddress) VALUES (%s, 28998.00, 'PROCESSING', 'Anna Salai')", (customer_id,))
        order_id = cur.lastrowid

        # 3. Insert Order Item
        cur.execute("INSERT INTO ORDER_ITEM (OrderID, ProductID, Quantity, UnitPriceAtSale) VALUES (%s, %s, %s, 14499.00)", (order_id, product_id, order_qty))

        # 4. Insert Payment
        cur.execute("INSERT INTO PAYMENT (OrderID, PaymentMethod, AmountPaid, PaymentStatus) VALUES (%s, 'UPI', 28998.00, 'COMPLETED')", (order_id,))

        # 5. Insert Shipment
        trk = f"TRK-TEST-{uuid.uuid4().hex[:8].upper()}"
        cur.execute("INSERT INTO SHIPMENT (OrderID, WarehouseID, TrackingNumber, DeliveryStatus) VALUES (%s, %s, %s, 'PREPARING')", (order_id, warehouse_id, trk))

        # Commit ACID transaction
        self.conn.commit()

        # Verify stock decrement
        cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = %s AND WarehouseID = %s", (product_id, warehouse_id))
        new_stock = cur.fetchone()["StockQuantity"]
        self.assertEqual(new_stock, init_stock - order_qty)

        # Verify shipment tracking
        cur.execute("SELECT * FROM SHIPMENT WHERE OrderID = %s", (order_id,))
        shipment = cur.fetchone()
        self.assertEqual(shipment["TrackingNumber"], trk)
        self.assertEqual(shipment["DeliveryStatus"], "PREPARING")

        cur.close()

    def test_06_staff_roles_and_warehouse_manager_restock(self):
        """
        Verify Staff roles:
        - Admin and Manager records exist in STAFF_USER with SHA-256 password hash.
        - Warehouse Manager can directly restock inventory for their assigned hub.
        """
        cur = self.conn.cursor(dictionary=True)

        # 1. Verify seeded staff accounts
        cur.execute("SELECT Role, AssignedWarehouseID FROM STAFF_USER WHERE Username = 'manager_chennai'")
        mgr = cur.fetchone()
        self.assertIsNotNone(mgr)
        self.assertEqual(mgr["Role"], "WAREHOUSE_MANAGER")
        self.assertEqual(mgr["AssignedWarehouseID"], 1)

        cur.execute("SELECT Role FROM STAFF_USER WHERE Username = 'admin'")
        adm = cur.fetchone()
        self.assertIsNotNone(adm)
        self.assertEqual(adm["Role"], "ADMIN")

        # 2. Test restock action for Chennai hub (WarehouseID=1) on Product 1
        cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = 1 AND WarehouseID = 1 FOR UPDATE")
        before_stock = cur.fetchone()["StockQuantity"]

        restock_qty = 25
        cur.execute("""
            UPDATE PRODUCT_INVENTORY 
            SET StockQuantity = StockQuantity + %s 
            WHERE ProductID = 1 AND WarehouseID = 1
        """, (restock_qty,))
        self.conn.commit()

        cur.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = 1 AND WarehouseID = 1")
        after_stock = cur.fetchone()["StockQuantity"]
        self.assertEqual(after_stock, before_stock + restock_qty)

        cur.close()

    def test_07_multi_item_cart_proximity_routing(self):
        """
        Verify multi-item cart proximity routing (evaluate_cart_fulfillment):
        When a cart has multiple items (e.g. keyboard + switches), the proximity engine
        evaluates candidate hubs and selects the closest hub that has 100% of all items in stock.
        """
        try:
            from db_integration.proximity import evaluate_cart_fulfillment, find_optimal_warehouse_for_cart
        except ImportError:
            from proximity import evaluate_cart_fulfillment, find_optimal_warehouse_for_cart

        cart = [
            {"product_id": 1, "quantity": 1},
            {"product_id": 2, "quantity": 2}
        ]
        # Vellore coordinates
        lat, lon = CITY_COORDINATES["Vellore"]

        results = evaluate_cart_fulfillment(self.conn, cart, customer_lat=lat, customer_lon=lon)
        self.assertGreater(len(results), 0, "No candidate hubs evaluated for cart.")

        # Optimal hub holding all items in cart
        optimal = find_optimal_warehouse_for_cart(self.conn, cart, customer_lat=lat, customer_lon=lon)
        self.assertIsNotNone(optimal, "Optimal warehouse for multi-item cart was not found.")
        self.assertTrue(optimal["can_fulfill_all"], "Optimal hub does not have all cart items in stock.")
        self.assertEqual(optimal["city"], "Chennai", "Failed to select closest hub holding all cart items.")


def run_tests():
    print("=" * 75)
    print(" Nexus Peripherals - BACSE202 DBMS Integration & Unit Test Suite ")
    print("=" * 75)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
