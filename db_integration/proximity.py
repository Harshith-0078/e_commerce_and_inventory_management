"""
Nexus Peripherals - Nearest-Warehouse Proximity Routing Module
Implements the Haversine great-circle distance algorithm and dynamic multi-warehouse
fulfillment evaluation based on real-time inventory levels.
"""

import math
from typing import Dict, List, Optional, Tuple, Any

try:
    from mysql.connector import MySQLConnection
except ImportError:
    MySQLConnection = Any  # type: ignore


# Standard City to Coordinate (Latitude, Longitude) Geocoding Directory
CITY_COORDINATES: Dict[str, Tuple[float, float]] = {
    "Vellore": (12.916500, 79.132500),
    "Chennai": (13.082700, 80.270700),
    "Bengaluru": (12.971600, 77.594600),
    "Visakhapatnam": (17.686800, 83.218500),
    "Mumbai": (19.076000, 72.877700),
    "Hyderabad": (17.385044, 78.486671),
    "Pune": (18.520430, 73.856744),
    "Delhi": (28.613939, 77.209021),
    "Kolkata": (22.572646, 88.363895),
    "Coimbatore": (11.016844, 76.955832)
}


def get_city_coordinates(city_name: str) -> Optional[Tuple[float, float]]:
    """
    Look up (latitude, longitude) for a standard city name (case-insensitive).
    """
    if not city_name:
        return None
    normalized = city_name.strip().title()
    return CITY_COORDINATES.get(normalized)


def calculate_haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate the great-circle distance between two points on the Earth's surface
    using the Haversine formula in pure Python.
    
    :param lat1: Latitude of point 1 in decimal degrees.
    :param lon1: Longitude of point 1 in decimal degrees.
    :param lat2: Latitude of point 2 in decimal degrees.
    :param lon2: Longitude of point 2 in decimal degrees.
    :return: Distance in kilometers (km), rounded to 2 decimal places.
    """
    # Mean Earth radius in kilometers
    EARTH_RADIUS_KM = 6371.0088

    # Convert decimal degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    
    # Clamp 'a' to [0, 1] to avoid domain error in math.sqrt due to floating-point precision
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance = EARTH_RADIUS_KM * c
    return round(distance, 2)


def compute_warehouse_fulfillment(
    warehouse_records: List[Dict[str, Any]],
    quantity: int,
    customer_lat: float,
    customer_lon: float
) -> List[Dict[str, Any]]:
    """
    Evaluates candidate warehouse inventory records against customer coordinates.
    Computes Haversine distance and checks if StockQuantity >= quantity.
    Returns list sorted by distance ascending.
    """
    evaluations = []
    for row in warehouse_records:
        w_lat = float(row["Latitude"])
        w_lon = float(row["Longitude"])
        distance = calculate_haversine_distance(customer_lat, customer_lon, w_lat, w_lon)
        has_stock = (row["StockQuantity"] >= quantity)
        evaluations.append({
            "warehouse_id": row["WarehouseID"],
            "warehouse_name": row["WarehouseName"],
            "city": row["City"],
            "state": row["State"],
            "latitude": w_lat,
            "longitude": w_lon,
            "stock_quantity": row["StockQuantity"],
            "has_sufficient_stock": has_stock,
            "distance_km": distance
        })

    # Sort candidates strictly by distance ascending
    evaluations.sort(key=lambda item: item["distance_km"])
    return evaluations


def evaluate_all_warehouses(
    conn: MySQLConnection,
    product_id: int,
    quantity: int,
    customer_lat: float,
    customer_lon: float
) -> List[Dict[str, Any]]:
    """
    Evaluates ALL warehouses holding the product, computing their Haversine distance
    to the customer and assessing whether they hold sufficient stock (StockQuantity >= quantity).
    Returns list sorted by distance ascending.
    """
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT 
            w.WarehouseID,
            w.WarehouseName,
            w.City,
            w.State,
            w.Latitude,
            w.Longitude,
            pi.StockQuantity
        FROM WAREHOUSE w
        INNER JOIN PRODUCT_INVENTORY pi ON w.WarehouseID = pi.WarehouseID
        WHERE pi.ProductID = %s
    """
    cursor.execute(query, (product_id,))
    rows = cursor.fetchall()
    cursor.close()

    return compute_warehouse_fulfillment(rows, quantity, customer_lat, customer_lon)


def find_optimal_warehouse(
    conn: MySQLConnection,
    product_id: int,
    quantity: int,
    customer_lat: float,
    customer_lon: float
) -> Optional[Dict[str, Any]]:
    """
    Finds the optimal nearest warehouse holding sufficient stock.
    
    Nearest-Warehouse Proximity Routing Logic:
    1. Filter warehouses holding StockQuantity >= quantity for product_id.
    2. Compute Haversine distance from customer coordinates to each eligible warehouse.
    3. Return the warehouse with the minimum distance.
    4. If the closest warehouse has insufficient stock, automatically routes to the next nearest.
    5. Returns None if no warehouse anywhere has sufficient stock.
    
    :return: Dict containing WarehouseID, WarehouseName, City, StockQuantity, distance_km or None.
    """
    all_hubs = evaluate_all_warehouses(conn, product_id, quantity, customer_lat, customer_lon)
    
    # Filter for candidates with sufficient stock
    eligible_hubs = [hub for hub in all_hubs if hub["has_sufficient_stock"]]
    if not eligible_hubs:
        return None

    # Closest candidate with stock is optimal
    return eligible_hubs[0]


def evaluate_cart_fulfillment(
    conn: MySQLConnection,
    cart_items: List[Dict[str, Any]],
    customer_lat: float,
    customer_lon: float
) -> List[Dict[str, Any]]:
    """
    Evaluates all warehouses against an entire cart of multiple items.
    Each item in cart_items must contain: 'product_id', 'quantity' (and optionally 'product_name').
    Computes distance to customer, and checks whether the warehouse has sufficient stock
    for ALL items in the cart.
    """
    if not cart_items:
        return []

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT WarehouseID, WarehouseName, City, State, Latitude, Longitude FROM WAREHOUSE ORDER BY WarehouseID")
    warehouses = cursor.fetchall()

    hub_evaluations = []
    for wh in warehouses:
        wid = wh["WarehouseID"]
        w_lat = float(wh["Latitude"])
        w_lon = float(wh["Longitude"])
        distance = calculate_haversine_distance(customer_lat, customer_lon, w_lat, w_lon)

        items_status = []
        can_fulfill_all = True

        for item in cart_items:
            pid = item["product_id"]
            qty = item["quantity"]
            cursor.execute("SELECT StockQuantity FROM PRODUCT_INVENTORY WHERE ProductID = %s AND WarehouseID = %s", (pid, wid))
            row = cursor.fetchone()
            available = row["StockQuantity"] if row else 0
            has_stock = (available >= qty)
            if not has_stock:
                can_fulfill_all = False

            items_status.append({
                "product_id": pid,
                "product_name": item.get("product_name", f"Product #{pid}"),
                "requested_quantity": qty,
                "available_stock": available,
                "has_sufficient_stock": has_stock
            })

        hub_evaluations.append({
            "warehouse_id": wid,
            "warehouse_name": wh["WarehouseName"],
            "city": wh["City"],
            "state": wh["State"],
            "latitude": w_lat,
            "longitude": w_lon,
            "distance_km": distance,
            "can_fulfill_all": can_fulfill_all,
            "items_status": items_status
        })

    cursor.close()
    hub_evaluations.sort(key=lambda h: h["distance_km"])
    return hub_evaluations


def find_optimal_warehouse_for_cart(
    conn: MySQLConnection,
    cart_items: List[Dict[str, Any]],
    customer_lat: float,
    customer_lon: float
) -> Optional[Dict[str, Any]]:
    """
    Finds the optimal nearest warehouse that holds sufficient stock for ALL items in the cart.
    Returns the closest eligible hub or None if no single warehouse can fulfill all items.
    """
    evaluations = evaluate_cart_fulfillment(conn, cart_items, customer_lat, customer_lon)
    eligible = [h for h in evaluations if h["can_fulfill_all"]]
    return eligible[0] if eligible else None
