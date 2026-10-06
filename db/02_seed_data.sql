-- ============================================================================
-- Project: Nexus Peripherals - Mechanical Keyboard E-Commerce & Inventory System
-- Course: BACSE202 Database Systems Project
-- Target Database: MySQL 8.0
-- File: 02_seed_data.sql
-- Description: Baseline seed data for Categories, Products, Warehouses, and
--              Cross-Warehouse Inventory allocations.
-- NOTE: In accordance with project requirements, CUSTOMER, ORDERS, ORDER_ITEM,
--       PAYMENT, and SHIPMENT tables are NOT seeded and start empty.
-- ============================================================================

USE nexus_peripherals;

-- ----------------------------------------------------------------------------
-- 1. CATEGORIES (3 core mechanical keyboard verticals)
-- ----------------------------------------------------------------------------
INSERT INTO CATEGORY (CategoryID, CategoryName, Description) VALUES
(1, 'Mechanical Keyboards', 'Custom barebone kits, pre-assembled keyboards, and hot-swappable gaming decks.'),
(2, 'Mechanical Switches', 'High-end linear, tactile, and clicky mechanical key switches for enthusiasts.'),
(3, 'Keycaps & Accessories', 'Double-shot PBT/ABS keycap sets, lubes, stabilizers, and customization tools.');

-- ----------------------------------------------------------------------------
-- 2. PRODUCTS (10 realistic mechanical keyboard components)
-- ----------------------------------------------------------------------------
INSERT INTO PRODUCT (ProductID, SKU, ProductName, UnitPrice, CategoryID) VALUES
-- Category 1: Mechanical Keyboards
(1, 'KB-KQ1P-WHT', 'Keychron Q1 Pro Wireless 75% Custom Keyboard (Barebone)', 16999.00, 1),
(2, 'KB-GMMK-BLK', 'Glorious GMMK Pro 75% Aluminum Gasket-Mounted Kit', 14499.00, 1),
(3, 'KB-MODE-SNT', 'Mode Sonnet 75% Premium Custom Keyboard (Navy/Copper)', 25999.00, 1),
(4, 'KB-TOFU-60R', 'KBDFans Tofu60 2.0 Aluminum Hot-Swap Deck', 11499.00, 1),

-- Category 2: Mechanical Switches
(5, 'SW-GAT-OK50', 'Gateron Oil King Linear Switches (Pack of 35)', 2099.00, 2),
(6, 'SW-KLH-BXW3', 'Kailh Box White V2 Clicky Switches (Pack of 35)', 1599.00, 2),
(7, 'SW-DRK-T135', 'Durock T1 Smokey Tactile Switches (Pack of 35)', 1899.00, 2),
(8, 'SW-ALZ-V3P3', 'Akko V3 Piano Pro Linear Switches (Pack of 45)', 1299.00, 2),

-- Category 3: Keycaps & Accessories
(9, 'KC-GMK-LASR', 'GMK Laser R2 Cherry Profile Double-Shot ABS Keycaps', 11999.00, 3),
(10, 'KC-PBT-RESN', 'PBTfans Resonance Dye-Sublimated PBT Keycap Set', 7499.00, 3);

-- ----------------------------------------------------------------------------
-- 3. WAREHOUSES (3 strategic fulfillment hubs with exact coordinates)
-- ----------------------------------------------------------------------------
INSERT INTO WAREHOUSE (WarehouseID, WarehouseName, City, State, Latitude, Longitude, Capacity) VALUES
(1, 'South Fulfillment Hub', 'Chennai', 'Tamil Nadu', 13.082700, 80.270700, 50000),
(2, 'Tech Corridor Warehouse', 'Bengaluru', 'Karnataka', 12.971600, 77.594600, 75000),
(3, 'West Distribution Center', 'Mumbai', 'Maharashtra', 19.076000, 72.877700, 60000);

-- ----------------------------------------------------------------------------
-- 4. PRODUCT_INVENTORY (Cross-warehouse distributed stock allocations)
-- Configured to test proximity routing, fallback scenarios, and low-stock alerts
-- ----------------------------------------------------------------------------
INSERT INTO PRODUCT_INVENTORY (ProductID, WarehouseID, StockQuantity, ReorderLevel) VALUES
-- Product 1: Keychron Q1 Pro (Low stock in Chennai, healthy in Bengaluru)
(1, 1, 3, 5),     -- Chennai: 3 units (triggers nearest fallback if customer wants >= 4)
(1, 2, 45, 10),   -- Bengaluru: 45 units
(1, 3, 20, 10),   -- Mumbai: 20 units

-- Product 2: Glorious GMMK Pro
(2, 1, 25, 10),   -- Chennai
(2, 2, 60, 15),   -- Bengaluru
(2, 3, 30, 10),   -- Mumbai

-- Product 3: Mode Sonnet Premium
(3, 1, 0, 5),     -- Chennai: 0 units (Tests immediate fallback routing to Bengaluru)
(3, 2, 12, 5),    -- Bengaluru
(3, 3, 8, 5),     -- Mumbai

-- Product 4: KBDFans Tofu60
(4, 1, 18, 5),
(4, 2, 22, 5),
(4, 3, 15, 5),

-- Product 5: Gateron Oil King Switches
(5, 1, 120, 25),
(5, 2, 250, 40),
(5, 3, 180, 30),

-- Product 6: Kailh Box White Switches
(6, 1, 80, 20),
(6, 2, 110, 25),
(6, 3, 95, 20),

-- Product 7: Durock T1 Tactile Switches
(7, 1, 90, 20),
(7, 2, 140, 25),
(7, 3, 75, 20),

-- Product 8: Akko V3 Piano Pro Switches
(8, 1, 200, 30),
(8, 2, 300, 50),
(8, 3, 150, 25),

-- Product 9: GMK Laser Keycaps
(9, 1, 14, 5),
(9, 2, 28, 5),
(9, 3, 10, 5),

-- Product 10: PBTfans Resonance Keycaps
(10, 1, 35, 8),
(10, 2, 50, 10),
(10, 3, 40, 8);

-- ----------------------------------------------------------------------------
-- 5. STAFF_USER (System Administrator & Warehouse Managers)
-- Passwords hashed via SHA-256:
-- admin -> 'admin123'
-- manager_chennai -> 'chennai123'
-- manager_bengaluru -> 'bengaluru123'
-- manager_mumbai -> 'mumbai123'
-- ----------------------------------------------------------------------------
INSERT INTO STAFF_USER (StaffID, Username, Email, PasswordHash, FullName, Role, AssignedWarehouseID) VALUES
(1, 'admin', 'admin@nexus.local', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'System Administrator', 'ADMIN', NULL),
(2, 'manager_chennai', 'manager.chennai@nexus.local', '9969d49c2dc32297c62b3227fe237486e2acfa54de24287af20b45e5523650e4', 'Chennai Hub Manager', 'WAREHOUSE_MANAGER', 1),
(3, 'manager_bengaluru', 'manager.bengaluru@nexus.local', '5b7f5b3ec26fe311d8ef21c6a22ae2ed31e2f2679745ca6dc532ea4d07ba7f5a', 'Bengaluru Hub Manager', 'WAREHOUSE_MANAGER', 2),
(4, 'manager_mumbai', 'manager.mumbai@nexus.local', '68dc2ec6f4e7d6b3639a995215b55bddebf5172a77e621a4465053a6867ffdc2', 'Mumbai Hub Manager', 'WAREHOUSE_MANAGER', 3);
