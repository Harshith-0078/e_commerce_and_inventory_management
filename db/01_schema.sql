-- ============================================================================
-- Project: Nexus Peripherals - Mechanical Keyboard E-Commerce & Inventory System
-- Course: BACSE202 Database Systems Project
-- Target Database: MySQL 8.0
-- File: 01_schema.sql
-- Description: DDL schema definition with strict foreign key constraints & checks.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS nexus_peripherals;
USE nexus_peripherals;

-- Disable foreign key checks momentarily for clean teardown
SET FOREIGN_KEY_CHECKS = 0;

-- Drop existing tables in reverse dependency order
DROP TABLE IF EXISTS SHIPMENT;
DROP TABLE IF EXISTS PAYMENT;
DROP TABLE IF EXISTS ORDER_ITEM;
DROP TABLE IF EXISTS ORDERS;
DROP TABLE IF EXISTS PRODUCT_INVENTORY;
DROP TABLE IF EXISTS STAFF_USER;
DROP TABLE IF EXISTS WAREHOUSE;
DROP TABLE IF EXISTS PRODUCT;
DROP TABLE IF EXISTS CUSTOMER;
DROP TABLE IF EXISTS CATEGORY;

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------------------------------------------------------
-- Table: CATEGORY
-- Stores high-level product groupings (Keyboards, Switches, Keycaps)
-- ----------------------------------------------------------------------------
CREATE TABLE CATEGORY (
    CategoryID INT AUTO_INCREMENT PRIMARY KEY,
    CategoryName VARCHAR(50) NOT NULL UNIQUE,
    Description TEXT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- Table: CUSTOMER
-- Tracks registered users with geo-coordinates for proximity routing
-- Starts empty per BACSE202 project specification (dynamic auth registration)
-- ----------------------------------------------------------------------------
CREATE TABLE CUSTOMER (
    CustomerID INT AUTO_INCREMENT PRIMARY KEY,
    FullName VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    Phone VARCHAR(15),
    City VARCHAR(50) NOT NULL,
    Latitude DECIMAL(9,6),
    Longitude DECIMAL(9,6),
    ShippingAddress TEXT NOT NULL,
    AccountCreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- Table: PRODUCT
-- Catalog of individual keyboard components and accessories
-- ----------------------------------------------------------------------------
CREATE TABLE PRODUCT (
    ProductID INT AUTO_INCREMENT PRIMARY KEY,
    SKU VARCHAR(50) NOT NULL UNIQUE,
    ProductName VARCHAR(120) NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL CHECK (UnitPrice > 0),
    CategoryID INT NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (CategoryID) REFERENCES CATEGORY(CategoryID) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- Table: WAREHOUSE
-- Fulfillment facilities with precise geographical coordinates
-- ----------------------------------------------------------------------------
CREATE TABLE WAREHOUSE (
    WarehouseID INT AUTO_INCREMENT PRIMARY KEY,
    WarehouseName VARCHAR(100) NOT NULL,
    City VARCHAR(50) NOT NULL,
    State VARCHAR(50) NOT NULL,
    Latitude DECIMAL(9,6) NOT NULL,
    Longitude DECIMAL(9,6) NOT NULL,
    Capacity INT NOT NULL CHECK (Capacity > 0),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- Table: STAFF_USER
-- Internal operations staff: System Administrators and assigned Warehouse Managers
-- ----------------------------------------------------------------------------
CREATE TABLE STAFF_USER (
    StaffID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) NOT NULL UNIQUE,
    Email VARCHAR(100) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    FullName VARCHAR(100) NOT NULL,
    Role ENUM('ADMIN', 'WAREHOUSE_MANAGER') NOT NULL,
    AssignedWarehouseID INT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (AssignedWarehouseID) REFERENCES WAREHOUSE(WarehouseID) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- Table: PRODUCT_INVENTORY
-- Composite entity tracking segregated stock quantities per warehouse hub
-- ----------------------------------------------------------------------------
CREATE TABLE PRODUCT_INVENTORY (
    ProductID INT NOT NULL,
    WarehouseID INT NOT NULL,
    StockQuantity INT NOT NULL DEFAULT 0 CHECK (StockQuantity >= 0),
    ReorderLevel INT NOT NULL DEFAULT 10,
    LastRestocked TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (ProductID, WarehouseID),
    FOREIGN KEY (ProductID) REFERENCES PRODUCT(ProductID) ON DELETE CASCADE,
    FOREIGN KEY (WarehouseID) REFERENCES WAREHOUSE(WarehouseID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- Table: ORDERS
-- Purchase orders recorded for customer checkout
-- ----------------------------------------------------------------------------
CREATE TABLE ORDERS (
    OrderID INT AUTO_INCREMENT PRIMARY KEY,
    CustomerID INT NOT NULL,
    OrderDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    TotalAmount DECIMAL(10,2) NOT NULL DEFAULT 0.00 CHECK (TotalAmount >= 0),
    OrderStatus ENUM('PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED') DEFAULT 'PENDING',
    ShippingAddress TEXT NOT NULL,
    FOREIGN KEY (CustomerID) REFERENCES CUSTOMER(CustomerID) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- Table: ORDER_ITEM
-- Individual line items in an order with captured sale prices
-- ----------------------------------------------------------------------------
CREATE TABLE ORDER_ITEM (
    OrderItemID INT AUTO_INCREMENT PRIMARY KEY,
    OrderID INT NOT NULL,
    ProductID INT NOT NULL,
    Quantity INT NOT NULL CHECK (Quantity > 0),
    UnitPriceAtSale DECIMAL(10,2) NOT NULL CHECK (UnitPriceAtSale > 0),
    FOREIGN KEY (OrderID) REFERENCES ORDERS(OrderID) ON DELETE CASCADE,
    FOREIGN KEY (ProductID) REFERENCES PRODUCT(ProductID) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- Table: PAYMENT
-- Financial transaction records linked 1:1 to an order
-- ----------------------------------------------------------------------------
CREATE TABLE PAYMENT (
    PaymentID INT AUTO_INCREMENT PRIMARY KEY,
    OrderID INT NOT NULL UNIQUE,
    PaymentDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PaymentMethod ENUM('UPI', 'CARD', 'NETBANKING', 'COD') NOT NULL,
    AmountPaid DECIMAL(10,2) NOT NULL CHECK (AmountPaid >= 0),
    PaymentStatus ENUM('PENDING', 'COMPLETED', 'FAILED') DEFAULT 'PENDING',
    FOREIGN KEY (OrderID) REFERENCES ORDERS(OrderID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------------
-- Table: SHIPMENT
-- Warehouse dispatch details and unique tracking identification
-- ----------------------------------------------------------------------------
CREATE TABLE SHIPMENT (
    ShipmentID INT AUTO_INCREMENT PRIMARY KEY,
    OrderID INT NOT NULL,
    WarehouseID INT NOT NULL,
    TrackingNumber VARCHAR(60) NOT NULL UNIQUE,
    DispatchedDate TIMESTAMP NULL,
    DeliveryStatus ENUM('PREPARING', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED') DEFAULT 'PREPARING',
    FOREIGN KEY (OrderID) REFERENCES ORDERS(OrderID) ON DELETE CASCADE,
    FOREIGN KEY (WarehouseID) REFERENCES WAREHOUSE(WarehouseID) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
