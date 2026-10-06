-- ============================================================================
-- Project: Nexus Peripherals - Mechanical Keyboard E-Commerce & Inventory System
-- Course: BACSE202 Database Systems Project
-- Target Database: MySQL 8.0
-- File: 03_procedures_views.sql
-- Description: Database views and diagnostic routines for aggregated catalog,
--              multi-warehouse stock tracking, and order fulfillment.
-- ============================================================================

USE nexus_peripherals;

-- ----------------------------------------------------------------------------
-- View 1: vw_ProductCatalog
-- Aggregates total stock available across all warehouse hubs per product
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_ProductCatalog AS
SELECT 
    p.ProductID,
    p.SKU,
    p.ProductName,
    c.CategoryName,
    p.UnitPrice,
    COALESCE(SUM(pi.StockQuantity), 0) AS TotalAvailableStock
FROM PRODUCT p
INNER JOIN CATEGORY c ON p.CategoryID = c.CategoryID
LEFT JOIN PRODUCT_INVENTORY pi ON p.ProductID = pi.ProductID
GROUP BY p.ProductID, p.SKU, p.ProductName, c.CategoryName, p.UnitPrice;

-- ----------------------------------------------------------------------------
-- View 2: vw_WarehouseStockBreakdown
-- Detailed multi-warehouse hub breakdown for real-time stock decrement tracking
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_WarehouseStockBreakdown AS
SELECT 
    p.ProductID,
    p.ProductName,
    w.WarehouseName,
    w.City,
    pi.StockQuantity,
    pi.ReorderLevel,
    CASE 
        WHEN pi.StockQuantity = 0 THEN 'OUT_OF_STOCK'
        WHEN pi.StockQuantity <= pi.ReorderLevel THEN 'LOW_STOCK'
        ELSE 'OPTIMAL'
    END AS StockStatus
FROM PRODUCT_INVENTORY pi
INNER JOIN PRODUCT p ON pi.ProductID = p.ProductID
INNER JOIN WAREHOUSE w ON pi.WarehouseID = w.WarehouseID
ORDER BY p.ProductID, w.WarehouseID;

-- ----------------------------------------------------------------------------
-- View 3: vw_OrderDetailsSummary (Auxiliary Fulfillment View)
-- Complete lifecycle view linking customer, order items, payment & shipment
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_OrderDetailsSummary AS
SELECT 
    o.OrderID,
    o.OrderDate,
    c.FullName AS CustomerName,
    c.Email AS CustomerEmail,
    c.City AS DeliveryCity,
    p.ProductName,
    oi.Quantity,
    oi.UnitPriceAtSale,
    o.TotalAmount,
    o.OrderStatus,
    pay.PaymentMethod,
    pay.PaymentStatus,
    s.TrackingNumber,
    s.DeliveryStatus,
    w.WarehouseName AS DispatchedFromHub
FROM ORDERS o
INNER JOIN CUSTOMER c ON o.CustomerID = c.CustomerID
INNER JOIN ORDER_ITEM oi ON o.OrderID = oi.OrderID
INNER JOIN PRODUCT p ON oi.ProductID = p.ProductID
LEFT JOIN PAYMENT pay ON o.OrderID = pay.OrderID
LEFT JOIN SHIPMENT s ON o.OrderID = s.OrderID
LEFT JOIN WAREHOUSE w ON s.WarehouseID = w.WarehouseID;

-- ----------------------------------------------------------------------------
-- Stored Procedure: sp_CheckWarehouseStock
-- Quick diagnostic stored procedure for querying stock of a specific product
-- ----------------------------------------------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS sp_CheckWarehouseStock$$
CREATE PROCEDURE sp_CheckWarehouseStock(IN in_product_id INT)
BEGIN
    SELECT 
        p.ProductID,
        p.ProductName,
        w.WarehouseID,
        w.WarehouseName,
        w.City,
        pi.StockQuantity,
        w.Latitude,
        w.Longitude
    FROM PRODUCT_INVENTORY pi
    INNER JOIN PRODUCT p ON pi.ProductID = p.ProductID
    INNER JOIN WAREHOUSE w ON pi.WarehouseID = w.WarehouseID
    WHERE pi.ProductID = in_product_id
    ORDER BY pi.StockQuantity DESC;
END$$

DELIMITER ;
