"""
Nexus Peripherals - E-Commerce Order & Multi-Warehouse Inventory Management System
BACSE202 Database Systems Final Project

Three Distinct User Portals:
1. Customer:
   - Dynamic registration/authentication with SHA-256 password hashing.
   - Live Product Catalog (vw_ProductCatalog) in INR (₹).
   - Nearest-Warehouse Proximity Routing (Haversine formula).
   - ACID Order Fulfillment Checkout & Personal Order/Tracking History.

2. Warehouse Manager:
   - Stationed at a physical hub (Chennai, Bengaluru, Mumbai).
   - Monitors localized stock levels for their assigned WarehouseID.
   - Restocks low-inventory products (updates PRODUCT_INVENTORY.StockQuantity).
   - Manages incoming shipments assigned to their hub.
   - Updates shipment delivery statuses (PREPARING -> IN_TRANSIT -> OUT_FOR_DELIVERY -> DELIVERED).

3. System Administrator (Admin):
   - Executive oversight across all 9 normalized tables.
   - Cross-hub platform analytics (Total Revenue, Orders, Products, Warehouses).
   - Adds new products to PRODUCT with SKU and INR pricing.
   - Creates new categories in CATEGORY.
   - Expands fulfillment network by adding new WAREHOUSE facilities with geographic coordinates.
"""

import os
import sys
import uuid
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any, List
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Ensure local imports work whether launched from project root or frontend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
db_integ_dir = os.path.join(parent_dir, "db_integration")

for p in [parent_dir, current_dir, db_integ_dir]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

try:
    from db_integration.db import (
        get_db_connection,
        get_db_config,
        test_connection,
        initialize_schema_and_seed,
        DEFAULT_CONFIG
    )
    from db_integration.proximity import (
        CITY_COORDINATES,
        get_city_coordinates,
        calculate_haversine_distance,
        find_optimal_warehouse,
        evaluate_all_warehouses,
        find_optimal_warehouse_for_cart,
        evaluate_cart_fulfillment
    )
    from db_integration.eda_analytics import (
        ensure_eda_tables_and_seed,
        get_available_months,
        get_eda_kpis,
        get_monthly_trend_data,
        get_category_distribution,
        get_top_selling_products,
        generate_monthly_pdf_report,
        record_intake
    )
    from db_integration.smtp_mailer import (
        notify_customer_order_placed,
        notify_customer_shipment_updated,
        notify_hub_manager_new_order,
        notify_hub_manager_low_stock,
        notify_admin_directive_to_manager,
        get_outbox_history,
        get_smtp_config,
        update_smtp_config
    )
except ImportError:
    from db import (
        get_db_connection,
        get_db_config,
        test_connection,
        initialize_schema_and_seed,
        DEFAULT_CONFIG
    )
    from proximity import (
        CITY_COORDINATES,
        get_city_coordinates,
        calculate_haversine_distance,
        find_optimal_warehouse,
        evaluate_all_warehouses,
        find_optimal_warehouse_for_cart,
        evaluate_cart_fulfillment
    )
    from eda_analytics import (
        ensure_eda_tables_and_seed,
        get_available_months,
        get_eda_kpis,
        get_monthly_trend_data,
        get_category_distribution,
        get_top_selling_products,
        generate_monthly_pdf_report,
        record_intake
    )
    from smtp_mailer import (
        notify_customer_order_placed,
        notify_customer_shipment_updated,
        notify_hub_manager_new_order,
        notify_hub_manager_low_stock,
        notify_admin_directive_to_manager,
        get_outbox_history,
        get_smtp_config,
        update_smtp_config
    )


def hash_password(password: str) -> str:
    """Computes SHA-256 hex digest for secure credential storage."""
    return hashlib.sha256(password.strip().encode("utf-8")).hexdigest()


class NexusPeripheralsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nexus Peripherals — Multi-Warehouse Inventory & Order Fulfillment")
        self.geometry("1140x740")
        self.minsize(1020, 660)

        # Database credentials config (editable via settings dialog)
        self.db_config = DEFAULT_CONFIG.copy()

        # Active Session State
        # Role: 'CUSTOMER', 'WAREHOUSE_MANAGER', 'ADMIN', or None
        self.current_role: Optional[str] = None
        self.current_user: Optional[Dict[str, Any]] = None

        # Multi-Item Shopping Cart state: List of dicts
        # Each item: {'product_id', 'sku', 'product_name', 'unit_price', 'quantity', 'subtotal'}
        self.shopping_cart: List[Dict[str, Any]] = []
        self.selected_catalog_ids: set = set()
        self.products_map: Dict[int, Dict[str, Any]] = {}

        # Modern Styling setup
        self._setup_styles()

        # Build UI Shell
        self._build_header()
        self._build_notebook()
        self._build_statusbar()

        # Initial check
        self.after(300, self._initial_db_check)

    def _setup_styles(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        self.BG_MAIN = "#F3F4F6"
        self.HEADER_BG = "#111827"
        self.ACCENT_COLOR = "#2563EB"
        self.ACCENT_HOVER = "#1D4ED8"
        self.SUCCESS_COLOR = "#059669"
        self.WARNING_COLOR = "#D97706"
        self.DANGER_COLOR = "#DC2626"
        self.CARD_BG = "#FFFFFF"

        self.configure(bg=self.BG_MAIN)

        style.configure("TNotebook", background=self.BG_MAIN, tabmargins=[6, 6, 6, 0])
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[14, 8])
        style.map("TNotebook.Tab",
                  background=[("selected", "#FFFFFF"), ("!selected", "#E5E7EB")],
                  foreground=[("selected", "#1E3A8A"), ("!selected", "#4B5563")])

        style.configure("Treeview", font=("Segoe UI", 9), rowheight=26, background="#FFFFFF")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#E5E7EB", foreground="#111827")
        style.map("Treeview", background=[("selected", "#DBEAFE")], foreground=[("selected", "#1E3A8A")])

        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background=self.ACCENT_COLOR, foreground="#FFFFFF")
        style.map("Primary.TButton", background=[("active", self.ACCENT_HOVER)])

        style.configure("Success.TButton", font=("Segoe UI", 10, "bold"), background=self.SUCCESS_COLOR, foreground="#FFFFFF")
        style.map("Success.TButton", background=[("active", "#047857")])

    def _build_header(self):
        header_frame = tk.Frame(self, bg=self.HEADER_BG, height=64)
        header_frame.pack(side=tk.TOP, fill=tk.X)

        title_lbl = tk.Label(
            header_frame,
            text="NEXUS PERIPHERALS",
            font=("Segoe UI", 15, "bold"),
            bg=self.HEADER_BG,
            fg="#60A5FA"
        )
        title_lbl.pack(side=tk.LEFT, padx=(20, 8), pady=12)

        subtitle_lbl = tk.Label(
            header_frame,
            text="Multi-Warehouse Inventory & Proximity Routing System",
            font=("Segoe UI", 10),
            bg=self.HEADER_BG,
            fg="#9CA3AF"
        )
        subtitle_lbl.pack(side=tk.LEFT, pady=14)

        # Right-side session indicator & Header Action Buttons
        btn_settings = tk.Button(
            header_frame,
            text="⚙ DB Settings / Reset",
            font=("Segoe UI", 9, "bold"),
            bg="#374151",
            fg="#F9FAFB",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            command=self._open_db_settings_dialog
        )
        btn_settings.pack(side=tk.RIGHT, padx=16, pady=14)

        btn_mailer = tk.Button(
            header_frame,
            text="✉ Mailer & Outbox",
            font=("Segoe UI", 9, "bold"),
            bg="#1D4ED8",
            fg="#F9FAFB",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            command=self._open_mailer_dialog
        )
        btn_mailer.pack(side=tk.RIGHT, padx=(0, 6), pady=14)

        self.lbl_session = tk.Label(
            header_frame,
            text="Not Logged In",
            font=("Segoe UI", 9, "italic"),
            bg=self.HEADER_BG,
            fg="#F87171"
        )
        self.lbl_session.pack(side=tk.RIGHT, padx=14, pady=14)

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        # Tab Frames for Customer, Manager, and Admin
        self.tab_auth = ttk.Frame(self.notebook)
        self.tab_catalog = ttk.Frame(self.notebook)
        self.tab_order = ttk.Frame(self.notebook)
        self.tab_history = ttk.Frame(self.notebook)
        self.tab_warehouse = ttk.Frame(self.notebook)
        self.tab_manager = ttk.Frame(self.notebook)
        self.tab_admin = ttk.Frame(self.notebook)
        self.tab_eda = ttk.Frame(self.notebook)

        # Tab Registry with Canonical Metadata
        self.ALL_TABS = [
            ("auth", self.tab_auth, " 🔐 Authentication Portals "),
            ("catalog", self.tab_catalog, " 🛍️ Product Catalog "),
            ("order", self.tab_order, " 🛒 Order & Fulfillment Engine "),
            ("history", self.tab_history, " 📦 Order History & Shipments "),
            ("warehouse", self.tab_warehouse, " 📊 Warehouse Stock Monitor "),
            ("manager", self.tab_manager, " 🏭 Hub Manager Operations "),
            ("admin", self.tab_admin, " 🛡️ System Admin Suite "),
            ("eda", self.tab_eda, " 📈 Exploratory Data Analysis & Reports "),
        ]

        # Initially add all tabs so their widget trees instantiate cleanly
        for _, frame, title in self.ALL_TABS:
            self.notebook.add(frame, text=title)

        # Build Widget Views
        self._build_auth_tab()
        self._build_catalog_tab()
        self._build_order_tab()
        self._build_history_tab()
        self._build_warehouse_tab()
        self._build_manager_tab()
        self._build_admin_tab()
        self._build_eda_tab()

        # Enforce strict Role-Based Access Control (RBAC) immediately
        self._apply_role_tab_visibility()

    def _apply_role_tab_visibility(self):
        """
        Enforces Role-Based Access Control (RBAC) on the GUI tabs:
        - CUSTOMER:
            Sees:
              1. 👤 Account & Session (Auth tab)
              2. 🛍️ Product Catalog
              3. 🛒 Cart & Proximity Checkout
              4. 📦 My Orders & Tracking (personal orders only)
            STRICTLY HIDDEN:
              - Warehouse Stock Monitor (internal inventory levels across hubs)
              - Hub Manager Operations (hub restock & dispatch controls)
              - System Admin Suite (cross-hub analytics, add SKU/warehouse, master order management)
              - Exploratory Data Analysis (EDA) & Reports
        - WAREHOUSE_MANAGER:
            Sees:
              1. 👤 Staff Session
              2. 🏭 Hub Manager Operations (stock restock & dispatch for assigned warehouse)
              3. 📊 Warehouse Stock Monitor
              4. 📈 Localized Hub EDA & Monthly PDF Audit Reports
            STRICTLY HIDDEN:
              - Customer Cart & Checkout
              - System Admin Suite
              - Product Catalog
        - ADMIN:
            Sees all management tabs:
              1. 👤 Admin Session
              2. 🛡️ System Admin Suite (Executive KPIs, Add Product, Add Warehouse, Master Orders)
              3. 🛍️ Product Catalog
              4. 📊 Warehouse Stock Monitor
              5. 🏭 Hub Manager Operations
              6. 📦 Global Order Ledger & Manifests
              7. 📈 Global Cross-Hub EDA & Executive PDF Audit Reports
        - NOT LOGGED IN:
            Only sees Authentication Portals and Catalog (Browse Only).
        """
        role = self.current_role

        if role == "CUSTOMER":
            allowed_tab_keys = ["auth", "catalog", "order", "history"]
        elif role == "WAREHOUSE_MANAGER":
            allowed_tab_keys = ["auth", "manager", "warehouse", "eda"]
        elif role == "ADMIN":
            allowed_tab_keys = ["auth", "admin", "catalog", "warehouse", "manager", "history", "eda"]
        else:
            # Unauthenticated state: Only login portal and public catalog
            allowed_tab_keys = ["auth", "catalog"]

        # First hide all tabs
        for key, tab_frame, _ in self.ALL_TABS:
            try:
                self.notebook.hide(tab_frame)
            except Exception:
                pass

        # Re-add only authorized tabs with customized role-appropriate labels
        for key, tab_frame, default_title in self.ALL_TABS:
            if key in allowed_tab_keys:
                title = default_title
                if key == "auth" and role:
                    role_display = "Customer" if role == "CUSTOMER" else ("Manager" if role == "WAREHOUSE_MANAGER" else "Admin")
                    title = f" 👤 Session ({role_display}) "
                elif key == "history" and role == "CUSTOMER":
                    title = " 📦 My Orders & Tracking "
                elif key == "history" and role == "ADMIN":
                    title = " 📦 Global Order Ledger "
                elif key == "manager" and role == "WAREHOUSE_MANAGER":
                    hub_id = self.current_user.get('AssignedWarehouseID', '') if self.current_user else ''
                    title = f" 🏭 Hub #{hub_id} Operations "
                elif key == "eda" and role == "WAREHOUSE_MANAGER":
                    hub_id = self.current_user.get('AssignedWarehouseID', '') if self.current_user else ''
                    title = f" 📈 Hub #{hub_id} Analytics & Reports "
                elif key == "eda" and role == "ADMIN":
                    title = " 📈 Global Analytics & Reports "

                self.notebook.add(tab_frame, text=title)

    def _build_statusbar(self):
        self.status_bar = tk.Label(
            self,
            text="Ready. Database: MySQL 8.0 [nexus_peripherals]",
            font=("Segoe UI", 9),
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#E5E7EB",
            fg="#374151",
            padx=10,
            pady=3
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, message: str, is_error: bool = False):
        self.status_bar.config(
            text=message,
            fg=self.DANGER_COLOR if is_error else "#111827"
        )

    # -------------------------------------------------------------------------
    # TAB 1: AUTHENTICATION PORTALS (3 ROLES)
    # -------------------------------------------------------------------------
    def _build_auth_tab(self):
        container = tk.Frame(self.tab_auth, bg=self.BG_MAIN)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Role Selector Banner
        role_selector_frame = tk.Frame(container, bg="#E0E7FF", bd=1, relief=tk.SOLID)
        role_selector_frame.pack(fill=tk.X, pady=(0, 12), ipady=6, padx=4)

        tk.Label(
            role_selector_frame,
            text="Select Login Role Portal:",
            font=("Segoe UI", 10, "bold"),
            bg="#E0E7FF",
            fg="#1E3A8A"
        ).pack(side=tk.LEFT, padx=14)

        self.portal_role_var = tk.StringVar(value="CUSTOMER")
        roles = [
            ("👤 Customer Portal", "CUSTOMER"),
            ("🏭 Warehouse Manager Portal", "WAREHOUSE_MANAGER"),
            ("🛡️ System Administrator", "ADMIN")
        ]
        for label, val in roles:
            tk.Radiobutton(
                role_selector_frame,
                text=label,
                variable=self.portal_role_var,
                value=val,
                font=("Segoe UI", 9, "bold"),
                bg="#E0E7FF",
                command=self._on_portal_role_switched
            ).pack(side=tk.LEFT, padx=10)

        # Form Card Container
        self.auth_card = tk.Frame(container, bg=self.CARD_BG, bd=1, relief=tk.GROOVE)
        self.auth_card.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Role Information Banner
        self.lbl_portal_banner = tk.Label(
            self.auth_card,
            text="Customer Portal: Dynamic registration & nearest-warehouse checkout.",
            font=("Segoe UI", 10, "bold"),
            bg="#EFF6FF",
            fg="#1E40AF",
            bd=1,
            relief=tk.SOLID,
            padx=12,
            pady=6,
            anchor=tk.W
        )
        self.lbl_portal_banner.pack(fill=tk.X, padx=25, pady=(15, 10))

        # Customer dynamic toggle (Only visible in CUSTOMER role)
        self.cust_mode_frame = tk.Frame(self.auth_card, bg=self.CARD_BG)
        self.cust_mode_frame.pack(fill=tk.X, padx=25, pady=(0, 6))

        self.auth_mode_var = tk.StringVar(value="login")
        tk.Radiobutton(
            self.cust_mode_frame,
            text="Customer Login",
            variable=self.auth_mode_var,
            value="login",
            font=("Segoe UI", 9, "bold"),
            bg=self.CARD_BG,
            command=self._on_auth_mode_change
        ).pack(side=tk.LEFT, padx=(0, 15))

        tk.Radiobutton(
            self.cust_mode_frame,
            text="New Customer Registration",
            variable=self.auth_mode_var,
            value="register",
            font=("Segoe UI", 9, "bold"),
            bg=self.CARD_BG,
            command=self._on_auth_mode_change
        ).pack(side=tk.LEFT)

        # Fields Grid Frame
        self.fields_frame = tk.Frame(self.auth_card, bg=self.CARD_BG)
        self.fields_frame.pack(fill=tk.X, padx=25, pady=8)

        # Username / Email
        self.lbl_username = tk.Label(self.fields_frame, text="Email Address *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG)
        self.lbl_username.grid(row=0, column=0, sticky=tk.W, pady=5)
        self.entry_email = ttk.Entry(self.fields_frame, width=38, font=("Segoe UI", 10))
        self.entry_email.grid(row=0, column=1, sticky=tk.W, pady=5, padx=10)

        # Password
        self.lbl_password = tk.Label(self.fields_frame, text="Password *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG)
        self.lbl_password.grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entry_password = ttk.Entry(self.fields_frame, width=38, font=("Segoe UI", 10), show="•")
        self.entry_password.grid(row=1, column=1, sticky=tk.W, pady=5, padx=10)

        # Dynamic Registration Fields (Hidden in login/manager/admin)
        self.lbl_fullname = tk.Label(self.fields_frame, text="Full Name *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG)
        self.entry_fullname = ttk.Entry(self.fields_frame, width=38, font=("Segoe UI", 10))

        self.lbl_phone = tk.Label(self.fields_frame, text="Phone Number", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG)
        self.entry_phone = ttk.Entry(self.fields_frame, width=38, font=("Segoe UI", 10))

        self.lbl_city = tk.Label(self.fields_frame, text="Delivery City *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG)
        city_names = list(CITY_COORDINATES.keys())
        self.combo_city = ttk.Combobox(self.fields_frame, values=city_names, state="readonly", width=36, font=("Segoe UI", 10))
        self.combo_city.set("Vellore")
        self.combo_city.bind("<<ComboboxSelected>>", self._on_city_selected)

        self.lbl_coords = tk.Label(self.fields_frame, text="Coordinates (Auto):", font=("Segoe UI", 9), bg=self.CARD_BG, fg="#4B5563")
        self.lbl_coords_val = tk.Label(self.fields_frame, text="Lat: 12.916500, Lon: 79.132500", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG, fg="#1E40AF")

        self.lbl_address = tk.Label(self.fields_frame, text="Shipping Address *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG)
        self.entry_address = ttk.Entry(self.fields_frame, width=46, font=("Segoe UI", 10))
        self.entry_address.insert(0, "VIT Campus, Men's Hostel Block D, Vellore")

        # Action Buttons
        btn_frame = tk.Frame(self.auth_card, bg=self.CARD_BG)
        btn_frame.pack(fill=tk.X, padx=25, pady=12)

        self.btn_auth_action = tk.Button(
            btn_frame,
            text="Authenticate & Login",
            font=("Segoe UI", 10, "bold"),
            bg=self.ACCENT_COLOR,
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=18,
            pady=6,
            command=self._handle_auth_action
        )
        self.btn_auth_action.pack(side=tk.LEFT)

        self.btn_logout = tk.Button(
            btn_frame,
            text="Log Out",
            font=("Segoe UI", 9),
            bg="#9CA3AF",
            fg="#111827",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            command=self._handle_logout,
            state=tk.DISABLED
        )
        self.btn_logout.pack(side=tk.LEFT, padx=12)

        # Quick Demo Account Shortcuts Frame
        self.demo_shortcuts_frame = tk.Frame(self.auth_card, bg="#F9FAFB", bd=1, relief=tk.SOLID)
        self.demo_shortcuts_frame.pack(fill=tk.X, padx=25, pady=(8, 12), ipady=4)

        tk.Label(
            self.demo_shortcuts_frame,
            text="Quick Fill Credentials for Testing / Evaluation:",
            font=("Segoe UI", 8, "bold"),
            bg="#F9FAFB",
            fg="#4B5563"
        ).pack(anchor=tk.W, padx=10, pady=(2, 4))

        quick_btns_box = tk.Frame(self.demo_shortcuts_frame, bg="#F9FAFB")
        quick_btns_box.pack(fill=tk.X, padx=10, pady=(0, 4))

        tk.Button(
            quick_btns_box,
            text="Admin (admin / admin123)",
            font=("Segoe UI", 8),
            bg="#E5E7EB",
            relief=tk.FLAT,
            padx=6,
            pady=2,
            command=lambda: self._quick_fill_auth("ADMIN", "admin", "admin123")
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            quick_btns_box,
            text="Samarth Hub Mgr (samarth@gmail.com / manager123)",
            font=("Segoe UI", 8, "bold"),
            bg="#FEF3C7",
            fg="#92400E",
            relief=tk.FLAT,
            padx=6,
            pady=2,
            command=lambda: self._quick_fill_auth("WAREHOUSE_MANAGER", "samarth@gmail.com", "manager123")
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            quick_btns_box,
            text="Chennai Hub (manager_chennai / chennai123)",
            font=("Segoe UI", 8),
            bg="#E5E7EB",
            relief=tk.FLAT,
            padx=6,
            pady=2,
            command=lambda: self._quick_fill_auth("WAREHOUSE_MANAGER", "manager_chennai", "chennai123")
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            quick_btns_box,
            text="Bengaluru Hub (manager_bengaluru / bengaluru123)",
            font=("Segoe UI", 8),
            bg="#E5E7EB",
            relief=tk.FLAT,
            padx=6,
            pady=2,
            command=lambda: self._quick_fill_auth("WAREHOUSE_MANAGER", "manager_bengaluru", "bengaluru123")
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            quick_btns_box,
            text="Mumbai Hub (manager_mumbai / mumbai123)",
            font=("Segoe UI", 8),
            bg="#E5E7EB",
            relief=tk.FLAT,
            padx=6,
            pady=2,
            command=lambda: self._quick_fill_auth("WAREHOUSE_MANAGER", "manager_mumbai", "mumbai123")
        ).pack(side=tk.LEFT, padx=3)

        # Active Session Details Display
        self.customer_info_lbl = tk.Label(
            self.auth_card,
            text="No active session. Please log in or register above.",
            font=("Segoe UI", 9),
            bg=self.CARD_BG,
            fg="#4B5563",
            justify=tk.LEFT
        )
        self.customer_info_lbl.pack(anchor=tk.W, padx=25, pady=(4, 15))

    def _quick_fill_auth(self, role: str, username: str, password: str):
        self.portal_role_var.set(role)
        self._on_portal_role_switched()
        self.entry_email.delete(0, tk.END)
        self.entry_email.insert(0, username)
        self.entry_password.delete(0, tk.END)
        self.entry_password.insert(0, password)

    def _on_portal_role_switched(self):
        role = self.portal_role_var.get()
        if role == "CUSTOMER":
            self.lbl_portal_banner.config(
                text="👤 Customer Portal: Dynamic registration, product ordering, and nearest-warehouse fulfillment.",
                bg="#EFF6FF", fg="#1E40AF"
            )
            self.lbl_username.config(text="Email Address *")
            self.cust_mode_frame.pack(fill=tk.X, padx=25, pady=(0, 6), before=self.fields_frame)
            self._on_auth_mode_change()
        elif role == "WAREHOUSE_MANAGER":
            self.lbl_portal_banner.config(
                text="🏭 Warehouse Manager Portal: Restock local inventory and dispatch incoming warehouse shipments.",
                bg="#FEF3C7", fg="#92400E"
            )
            self.lbl_username.config(text="Staff Username / Email *")
            self.cust_mode_frame.pack_forget()
            self._hide_registration_fields()
            self.btn_auth_action.config(text="Manager Login", bg="#D97706")
        else:  # ADMIN
            self.lbl_portal_banner.config(
                text="🛡️ System Administrator Portal: Full platform control, add products/warehouses, cross-hub analytics.",
                bg="#FEE2E2", fg="#991B1B"
            )
            self.lbl_username.config(text="Admin Username / Email *")
            self.cust_mode_frame.pack_forget()
            self._hide_registration_fields()
            self.btn_auth_action.config(text="Administrator Login", bg="#DC2626")

    def _on_auth_mode_change(self):
        if self.portal_role_var.get() != "CUSTOMER":
            return
        mode = self.auth_mode_var.get()
        if mode == "register":
            self.lbl_fullname.grid(row=2, column=0, sticky=tk.W, pady=5)
            self.entry_fullname.grid(row=2, column=1, sticky=tk.W, pady=5, padx=10)

            self.lbl_phone.grid(row=3, column=0, sticky=tk.W, pady=5)
            self.entry_phone.grid(row=3, column=1, sticky=tk.W, pady=5, padx=10)

            self.lbl_city.grid(row=4, column=0, sticky=tk.W, pady=5)
            self.combo_city.grid(row=4, column=1, sticky=tk.W, pady=5, padx=10)

            self.lbl_coords.grid(row=5, column=0, sticky=tk.W, pady=4)
            self.lbl_coords_val.grid(row=5, column=1, sticky=tk.W, pady=4, padx=10)

            self.lbl_address.grid(row=6, column=0, sticky=tk.W, pady=5)
            self.entry_address.grid(row=6, column=1, sticky=tk.W, pady=5, padx=10)

            self.btn_auth_action.config(text="Create Customer & Start Session", bg=self.SUCCESS_COLOR)
        else:
            self._hide_registration_fields()
            self.btn_auth_action.config(text="Customer Login", bg=self.ACCENT_COLOR)

    def _hide_registration_fields(self):
        self.lbl_fullname.grid_remove()
        self.entry_fullname.grid_remove()
        self.lbl_phone.grid_remove()
        self.entry_phone.grid_remove()
        self.lbl_city.grid_remove()
        self.combo_city.grid_remove()
        self.lbl_coords.grid_remove()
        self.lbl_coords_val.grid_remove()
        self.lbl_address.grid_remove()
        self.entry_address.grid_remove()

    def _on_city_selected(self, event=None):
        city = self.combo_city.get()
        coords = get_city_coordinates(city)
        if coords:
            self.lbl_coords_val.config(text=f"Lat: {coords[0]:.6f}, Lon: {coords[1]:.6f}")

    def _handle_auth_action(self):
        portal = self.portal_role_var.get()
        identifier = self.entry_email.get().strip()
        password = self.entry_password.get()

        if not identifier or not password:
            messagebox.showwarning("Validation Error", "Please provide Username/Email and Password.")
            return

        hashed_pw = hash_password(password)

        if portal == "CUSTOMER":
            self._handle_customer_auth(identifier, password, hashed_pw)
        else:
            self._handle_staff_auth(identifier, hashed_pw, expected_role=portal)

    def _handle_customer_auth(self, email: str, raw_password: str, hashed_pw: str):
        mode = self.auth_mode_var.get()
        try:
            conn = get_db_connection(self.db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM CUSTOMER WHERE Email = %s", (email.lower(),))
            existing_user = cursor.fetchone()

            if mode == "login":
                if not existing_user:
                    register_now = messagebox.askyesno(
                        "Customer Not Found",
                        f"No account exists for '{email}'.\n\nWould you like to register as a new customer now?"
                    )
                    if register_now:
                        self.auth_mode_var.set("register")
                        self._on_auth_mode_change()
                        self.entry_fullname.focus_set()
                    cursor.close()
                    conn.close()
                    return

                if existing_user["PasswordHash"] == hashed_pw:
                    self._start_user_session("CUSTOMER", existing_user)
                    messagebox.showinfo("Login Success", f"Welcome back, {existing_user['FullName']}!")
                else:
                    messagebox.showerror("Authentication Failed", "Incorrect customer password.")

            else:  # Registration mode
                if existing_user:
                    messagebox.showerror("Conflict", f"An account with '{email}' already exists. Please log in.")
                    self.auth_mode_var.set("login")
                    self._on_auth_mode_change()
                    cursor.close()
                    conn.close()
                    return

                fullname = self.entry_fullname.get().strip()
                phone = self.entry_phone.get().strip()
                city = self.combo_city.get().strip()
                address = self.entry_address.get().strip()

                if not fullname or not city or not address:
                    messagebox.showwarning("Validation Error", "Full Name, Delivery City, and Address are required.")
                    cursor.close()
                    conn.close()
                    return

                coords = get_city_coordinates(city)
                lat, lon = coords if coords else (12.916500, 79.132500)

                insert_sql = """
                    INSERT INTO CUSTOMER (FullName, Email, PasswordHash, Phone, City, Latitude, Longitude, ShippingAddress)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_sql, (fullname, email.lower(), hashed_pw, phone, city, lat, lon, address))
                conn.commit()
                new_customer_id = cursor.lastrowid

                cursor.execute("SELECT * FROM CUSTOMER WHERE CustomerID = %s", (new_customer_id,))
                new_user = cursor.fetchone()
                self._start_user_session("CUSTOMER", new_user)
                messagebox.showinfo(
                    "Registration Successful",
                    f"Customer account created for '{fullname}' with SHA-256 security.\nSession started!"
                )

            cursor.close()
            conn.close()

        except Exception as e:
            messagebox.showerror("Database Error", f"Authentication error: {str(e)}")

    def _handle_staff_auth(self, identifier: str, hashed_pw: str, expected_role: str):
        try:
            conn = get_db_connection(self.db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM STAFF_USER WHERE (Username = %s OR Email = %s) AND Role = %s",
                (identifier, identifier, expected_role)
            )
            staff_user = cursor.fetchone()

            if not staff_user:
                # Check if this user exists in CUSTOMER table
                cursor.execute("SELECT * FROM CUSTOMER WHERE Email = %s", (identifier.lower(),))
                cust_match = cursor.fetchone()
                if cust_match:
                    cursor.close()
                    conn.close()
                    switch = messagebox.askyesno(
                        "Role Mismatch — Customer Account Detected",
                        f"'{identifier}' is registered as a Customer account, not a {expected_role.replace('_', ' ').title()}.\n\n"
                        f"Would you like to switch to the Customer Portal and log in now?"
                    )
                    if switch:
                        self.portal_role_var.set("CUSTOMER")
                        self._on_portal_role_switched()
                        self.auth_mode_var.set("login")
                        self._on_auth_mode_change()
                        self.entry_email.delete(0, tk.END)
                        self.entry_email.insert(0, identifier)
                        if cust_match["PasswordHash"] == hashed_pw:
                            self._start_user_session("CUSTOMER", cust_match)
                            messagebox.showinfo("Customer Login Success", f"Welcome back, {cust_match['FullName']}!\nYou are logged into the Customer Portal.")
                        else:
                            messagebox.showerror("Authentication Failed", "Incorrect password for customer account.")
                    return

                # Check if staff exists under a different staff role
                cursor.execute("SELECT * FROM STAFF_USER WHERE Username = %s OR Email = %s", (identifier, identifier))
                other_staff = cursor.fetchone()
                if other_staff:
                    other_role = other_staff["Role"]
                    cursor.close()
                    conn.close()
                    messagebox.showinfo(
                        "Role Mismatch",
                        f"'{identifier}' is registered as a {other_role.replace('_', ' ').title()}, not a {expected_role.replace('_', ' ').title()}.\n\n"
                        f"Please select the '{other_role.replace('_', ' ').title()}' radio button above."
                    )
                    return

                cursor.close()
                conn.close()
                role_label = expected_role.replace('_', ' ').title()
                hint = "admin / admin123" if expected_role == "ADMIN" else "manager_chennai / chennai123"
                messagebox.showerror(
                    "Access Denied",
                    f"No {role_label} account found matching '{identifier}'.\n\n"
                    f"• Customer Login: Select '👤 Customer Portal' above.\n"
                    f"• {role_label} Login: Use staff username (e.g. '{hint}') or click the Quick Fill buttons below."
                )
                return

            if staff_user["PasswordHash"] == hashed_pw:
                self._start_user_session(expected_role, staff_user)
                role_title = "Warehouse Manager" if expected_role == "WAREHOUSE_MANAGER" else "System Administrator"
                messagebox.showinfo("Staff Login Success", f"Welcome, {staff_user['FullName']}!\nRole: {role_title}")
            else:
                messagebox.showerror("Authentication Failed", "Incorrect password for staff account.")

        except Exception as e:
            messagebox.showerror("Database Error", f"Staff authentication error: {str(e)}")

    def _start_user_session(self, role: str, user_record: Dict[str, Any]):
        self.current_role = role
        self.current_user = user_record

        # Enforce strict Role-Based Access Control tab visibility immediately
        self._apply_role_tab_visibility()

        if role == "CUSTOMER":
            self.lbl_session.config(
                text=f"Customer: {user_record['FullName']} ({user_record['City']})",
                fg="#34D399"
            )
            self.customer_info_lbl.config(
                text=f"✓ Active Session: {user_record['FullName']} (Customer ID: #{user_record['CustomerID']})\n"
                     f"  Email: {user_record['Email']} | Phone: {user_record['Phone'] or 'N/A'}\n"
                     f"  City: {user_record['City']} (Lat: {float(user_record['Latitude']):.4f}, Lon: {float(user_record['Longitude']):.4f})\n"
                     f"  Address: {user_record['ShippingAddress']}",
                fg="#065F46"
            )
            self._update_order_tab_customer_info()
            self.refresh_order_history()
            self.notebook.select(self.tab_catalog)

        elif role == "WAREHOUSE_MANAGER":
            wh_id = user_record.get("AssignedWarehouseID")
            self.lbl_session.config(
                text=f"Manager: {user_record['FullName']} (Hub #{wh_id})",
                fg="#FBBF24"
            )
            self.customer_info_lbl.config(
                text=f"✓ Active Session: {user_record['FullName']} [Warehouse Manager]\n"
                     f"  Username: {user_record['Username']} | Email: {user_record['Email']}\n"
                     f"  Assigned Warehouse Hub: #{wh_id}\n"
                     f"  Access: Direct stock update & shipment dispatch manifest operations.",
                fg="#92400E"
            )
            self.refresh_manager_hub_view()
            self.refresh_warehouse_monitor()
            self.refresh_eda_view()
            self.notebook.select(self.tab_manager)

        elif role == "ADMIN":
            self.lbl_session.config(
                text=f"Administrator: {user_record['FullName']}",
                fg="#F87171"
            )
            self.customer_info_lbl.config(
                text=f"✓ Active Session: {user_record['FullName']} [System Administrator]\n"
                     f"  Username: {user_record['Username']} | Email: {user_record['Email']}\n"
                     f"  Access: Full administrative control across all 9 normalized tables & platform analytics.",
                fg="#991B1B"
            )
            self.refresh_admin_analytics()
            self.refresh_warehouse_monitor()
            self.refresh_order_history()
            self.refresh_eda_view()
            self.notebook.select(self.tab_admin)

        self.btn_logout.config(state=tk.NORMAL)
        self.set_status(f"Session started for {user_record['FullName']} [{role}]")
        self.refresh_catalog()

    def _handle_logout(self):
        self.current_role = None
        self.current_user = None
        self.lbl_session.config(text="Not Logged In", fg="#F87171")
        self.customer_info_lbl.config(
            text="No active session. Please log in or register above.",
            fg="#4B5563"
        )
        self.btn_logout.config(state=tk.DISABLED)
        self._update_order_tab_customer_info()
        self._apply_role_tab_visibility()
        self.notebook.select(self.tab_auth)
        self.set_status("User logged out.")
        messagebox.showinfo("Logged Out", "Session ended successfully.")

    # -------------------------------------------------------------------------
    # TAB 2: LIVE PRODUCT CATALOG (vw_ProductCatalog in ₹)
    # -------------------------------------------------------------------------
    def _build_catalog_tab(self):
        container = tk.Frame(self.tab_catalog, bg=self.BG_MAIN)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Top Control Toolbar
        control_bar = tk.Frame(container, bg=self.BG_MAIN)
        control_bar.pack(fill=tk.X, pady=(0, 6))

        tk.Label(control_bar, text="Filter by Category:", font=("Segoe UI", 9, "bold"), bg=self.BG_MAIN).pack(side=tk.LEFT, padx=(0, 6))
        self.catalog_cat_filter = ttk.Combobox(
            control_bar,
            values=["All Categories", "Mechanical Keyboards", "Mechanical Switches", "Keycaps & Accessories"],
            state="readonly",
            width=22
        )
        self.catalog_cat_filter.set("All Categories")
        self.catalog_cat_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_catalog())
        self.catalog_cat_filter.pack(side=tk.LEFT, padx=(0, 10))

        btn_refresh = tk.Button(
            control_bar,
            text="🔄 Refresh",
            font=("Segoe UI", 9),
            bg="#E5E7EB",
            relief=tk.FLAT,
            padx=8,
            pady=3,
            command=self.refresh_catalog
        )
        btn_refresh.pack(side=tk.LEFT, padx=(0, 10))

        # Select All / Clear Selection Buttons for effortless multi-item shopping
        btn_sel_all = tk.Button(
            control_bar,
            text="☑ Select All",
            font=("Segoe UI", 9, "bold"),
            bg="#EFF6FF",
            fg="#1E40AF",
            relief=tk.SOLID,
            bd=1,
            padx=8,
            pady=3,
            command=self._catalog_select_all
        )
        btn_sel_all.pack(side=tk.LEFT, padx=(0, 4))

        btn_desel_all = tk.Button(
            control_bar,
            text="☐ Clear",
            font=("Segoe UI", 9),
            bg="#F3F4F6",
            fg="#4B5563",
            relief=tk.SOLID,
            bd=1,
            padx=8,
            pady=3,
            command=self._catalog_deselect_all
        )
        btn_desel_all.pack(side=tk.LEFT, padx=(0, 10))

        self.lbl_catalog_sel_count = tk.Label(
            control_bar,
            text="0 items selected",
            font=("Segoe UI", 9, "bold"),
            bg=self.BG_MAIN,
            fg="#6B7280"
        )
        self.lbl_catalog_sel_count.pack(side=tk.LEFT, padx=(0, 12))

        # Multi-Item Cart Controls on Catalog Toolbar
        tk.Label(control_bar, text="Qty each:", font=("Segoe UI", 9, "bold"), bg=self.BG_MAIN).pack(side=tk.LEFT, padx=(0, 4))
        self.spin_catalog_qty = ttk.Spinbox(control_bar, from_=1, to=100, width=4, font=("Segoe UI", 9))
        self.spin_catalog_qty.set(1)
        self.spin_catalog_qty.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_add_cart = tk.Button(
            control_bar,
            text="🛒 Add to Cart",
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=12,
            pady=3,
            command=lambda: self._add_selected_from_catalog(proceed_to_checkout=False)
        )
        self.btn_add_cart.pack(side=tk.LEFT, padx=(0, 6))

        btn_checkout_sel = tk.Button(
            control_bar,
            text="⚡ Buy Selected Now",
            font=("Segoe UI", 9, "bold"),
            bg=self.SUCCESS_COLOR,
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=12,
            pady=3,
            command=lambda: self._add_selected_from_catalog(proceed_to_checkout=True)
        )
        btn_checkout_sel.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_cart_badge = tk.Button(
            control_bar,
            text="🛒 Cart: 0 items (₹0.00)",
            font=("Segoe UI", 9, "bold"),
            bg="#FEF3C7",
            fg="#92400E",
            relief=tk.SOLID,
            bd=1,
            padx=12,
            pady=3,
            command=self._on_cart_badge_clicked
        )
        self.btn_cart_badge.pack(side=tk.RIGHT)

        # Helpful visual guidance banner
        tip_frame = tk.Frame(container, bg="#EFF6FF", bd=1, relief=tk.SOLID)
        tip_frame.pack(fill=tk.X, pady=(0, 6), ipady=3)
        tk.Label(
            tip_frame,
            text="💡 Multi-Item Selection: Simply CLICK any component to toggle [☑ / ☐] — select 2, 3, or more items! "
                 "You can also use '☑ Select All' or hold Ctrl/Shift. Then click '🛒 Add to Cart' or '⚡ Buy Selected Now'.",
            font=("Segoe UI", 9),
            bg="#EFF6FF",
            fg="#1E40AF"
        ).pack(side=tk.LEFT, padx=10)

        # Treeview for vw_ProductCatalog with Checkbox column (selectmode="extended")
        columns = ("Select", "ProductID", "SKU", "ProductName", "CategoryName", "UnitPrice", "TotalAvailableStock", "StockStatus")
        self.catalog_tree = ttk.Treeview(container, columns=columns, show="headings", selectmode="extended")

        self.catalog_tree.heading("Select", text="Select")
        self.catalog_tree.heading("ProductID", text="ID")
        self.catalog_tree.heading("SKU", text="SKU")
        self.catalog_tree.heading("ProductName", text="Product Name")
        self.catalog_tree.heading("CategoryName", text="Category")
        self.catalog_tree.heading("UnitPrice", text="Unit Price (₹)")
        self.catalog_tree.heading("TotalAvailableStock", text="Total Network Stock")
        self.catalog_tree.heading("StockStatus", text="Status")

        self.catalog_tree.column("Select", width=55, anchor=tk.CENTER)
        self.catalog_tree.column("ProductID", width=45, anchor=tk.CENTER)
        self.catalog_tree.column("SKU", width=115, anchor=tk.CENTER)
        self.catalog_tree.column("ProductName", width=330, anchor=tk.W)
        self.catalog_tree.column("CategoryName", width=170, anchor=tk.W)
        self.catalog_tree.column("UnitPrice", width=115, anchor=tk.E)
        self.catalog_tree.column("TotalAvailableStock", width=130, anchor=tk.CENTER)
        self.catalog_tree.column("StockStatus", width=110, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.catalog_tree.yview)
        self.catalog_tree.configure(yscrollcommand=scrollbar.set)

        self.catalog_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Interactive click bindings: single click toggles row selection!
        self.catalog_tree.bind("<Button-1>", self._on_catalog_tree_click)
        self.catalog_tree.bind("<space>", self._on_catalog_space)
        self.catalog_tree.bind("<Double-1>", self._on_catalog_double_click)

    def _on_catalog_tree_click(self, event):
        region = self.catalog_tree.identify_region(event.x, event.y)
        if region not in ("cell", "tree"):
            return
        item_id = self.catalog_tree.identify_row(event.y)
        if not item_id:
            return
        try:
            pid = int(item_id)
        except ValueError:
            return

        if pid in self.selected_catalog_ids:
            self.selected_catalog_ids.remove(pid)
        else:
            self.selected_catalog_ids.add(pid)

        self._sync_catalog_selection_visuals()
        return "break"

    def _on_catalog_space(self, event):
        focused = self.catalog_tree.focus()
        if focused:
            try:
                pid = int(focused)
                if pid in self.selected_catalog_ids:
                    self.selected_catalog_ids.remove(pid)
                else:
                    self.selected_catalog_ids.add(pid)
                self._sync_catalog_selection_visuals()
            except ValueError:
                pass
        return "break"

    def _on_catalog_double_click(self, event):
        item_id = self.catalog_tree.identify_row(event.y)
        if item_id:
            try:
                pid = int(item_id)
                self.selected_catalog_ids.add(pid)
                self._sync_catalog_selection_visuals()
                self._add_selected_from_catalog(proceed_to_checkout=True)
            except ValueError:
                pass

    def _catalog_select_all(self):
        for item_id in self.catalog_tree.get_children():
            try:
                self.selected_catalog_ids.add(int(item_id))
            except ValueError:
                pass
        self._sync_catalog_selection_visuals()

    def _catalog_deselect_all(self):
        self.selected_catalog_ids.clear()
        self._sync_catalog_selection_visuals()

    def _sync_catalog_selection_visuals(self):
        """Syncs the visual checkmarks and selection highlighting in catalog_tree."""
        highlight_iids = []
        for item_id in self.catalog_tree.get_children():
            try:
                pid = int(item_id)
            except ValueError:
                continue
            is_checked = pid in self.selected_catalog_ids
            vals = list(self.catalog_tree.item(item_id, "values"))
            if vals:
                vals[0] = "☑" if is_checked else "☐"
                self.catalog_tree.item(item_id, values=vals)
            if is_checked:
                highlight_iids.append(item_id)

        self.catalog_tree.selection_set(highlight_iids)
        count = len(self.selected_catalog_ids)
        if hasattr(self, "lbl_catalog_sel_count"):
            if count == 0:
                self.lbl_catalog_sel_count.config(text="0 items selected", fg="#6B7280")
                if hasattr(self, "btn_add_cart"):
                    self.btn_add_cart.config(text="🛒 Add to Cart")
            elif count == 1:
                self.lbl_catalog_sel_count.config(text="1 item selected", fg="#2563EB")
                if hasattr(self, "btn_add_cart"):
                    self.btn_add_cart.config(text="🛒 Add 1 Item to Cart")
            else:
                self.lbl_catalog_sel_count.config(text=f"{count} items selected", fg="#059669")
                if hasattr(self, "btn_add_cart"):
                    self.btn_add_cart.config(text=f"🛒 Add {count} Items to Cart")

    def refresh_catalog(self):
        for item in self.catalog_tree.get_children():
            self.catalog_tree.delete(item)

        selected_cat = self.catalog_cat_filter.get()

        try:
            conn = get_db_connection(self.db_config)
            cursor = conn.cursor(dictionary=True)

            query = "SELECT * FROM vw_ProductCatalog"
            params = []
            if selected_cat and selected_cat != "All Categories":
                query += " WHERE CategoryName = %s"
                params.append(selected_cat)
            query += " ORDER BY ProductID"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                pid = int(row["ProductID"])
                self.products_map[pid] = row
                stock = int(row["TotalAvailableStock"])
                status = "OUT OF STOCK" if stock == 0 else ("LOW STOCK" if stock <= 15 else "IN STOCK")
                is_selected = pid in self.selected_catalog_ids
                chk_icon = "☑" if is_selected else "☐"
                self.catalog_tree.insert(
                    "",
                    tk.END,
                    iid=str(pid),
                    values=(
                        chk_icon,
                        pid,
                        row["SKU"],
                        row["ProductName"],
                        row["CategoryName"],
                        f"₹{float(row['UnitPrice']):,.2f}",
                        stock,
                        status
                    )
                )

            cursor.close()
            conn.close()
            self._sync_catalog_selection_visuals()
            self.set_status(f"Catalog refreshed from vw_ProductCatalog ({len(rows)} items loaded).")
        except Exception as e:
            self.set_status(f"Error loading catalog: {str(e)}", is_error=True)

    def _add_selected_from_catalog(self, proceed_to_checkout: bool = False):
        """Adds all selected items from catalog treeview to the shopping cart."""
        target_pids = list(self.selected_catalog_ids)
        if not target_pids:
            for item_id in self.catalog_tree.selection():
                try:
                    target_pids.append(int(item_id))
                except ValueError:
                    pass

        if not target_pids:
            messagebox.showinfo(
                "Select Items",
                "Please select one or more components from the catalog.\n\n"
                "Tip: Click any item row to check it [☑ / ☐], or click '☑ Select All'!"
            )
            return

        try:
            qty = max(1, int(self.spin_catalog_qty.get()))
        except ValueError:
            qty = 1

        added_names = []
        for pid in target_pids:
            self._add_product_to_cart(pid, quantity=qty)
            prod = self.products_map.get(pid)
            if prod:
                added_names.append(prod["ProductName"])
            else:
                added_names.append(f"Product #{pid}")

        self._update_cart_display()

        if proceed_to_checkout:
            if self.current_role == "CUSTOMER":
                self.notebook.select(self.tab_order)
                self._preview_fulfillment_routing()
            else:
                messagebox.showinfo(
                    "Customer Login Required",
                    f"Selected {len(added_names)} component(s) added to Cart!\n\n"
                    "Please log in or register as a Customer on Tab 1 to proceed with Nearest-Warehouse Proximity Checkout."
                )
                self.notebook.select(self.tab_auth)
        else:
            self.set_status(f"Added {len(added_names)} component(s) to shopping cart.")
            messagebox.showinfo(
                "Added to Cart",
                f"Successfully added {len(added_names)} component(s) (Qty: {qty} each) to your Shopping Cart!\n\n"
                f"Components Added:\n• " + "\n• ".join(added_names[:5]) + ("\n• ..." if len(added_names) > 5 else "") +
                f"\n\n👉 Switch to Tab 3 ('Order & Fulfillment Engine') to view proximity routing and confirm checkout."
            )

    def _on_cart_badge_clicked(self):
        """Navigates to the shopping cart tab if authenticated as Customer, otherwise prompts to log in."""
        if self.current_role == "CUSTOMER":
            self.notebook.select(self.tab_order)
        else:
            messagebox.showinfo(
                "Customer Login Required",
                "Please log in or register as a Customer on Tab 1 to access your Shopping Cart & Proximity Checkout."
            )
            self.notebook.select(self.tab_auth)

    def _add_product_to_cart(self, product_id: int, quantity: int = 1):
        """Adds or updates an item in self.shopping_cart."""
        product = self.products_map.get(product_id)
        if not product:
            return

        unit_price = float(product["UnitPrice"])
        for item in self.shopping_cart:
            if item["product_id"] == product_id:
                item["quantity"] += quantity
                item["subtotal"] = item["quantity"] * unit_price
                return

        self.shopping_cart.append({
            "product_id": product_id,
            "sku": product["SKU"],
            "product_name": product["ProductName"],
            "unit_price": unit_price,
            "quantity": quantity,
            "subtotal": quantity * unit_price
        })

    def _update_cart_display(self):
        """Updates the cart table in Tab 3 and the cart badges."""
        if hasattr(self, "cart_tree"):
            for item in self.cart_tree.get_children():
                self.cart_tree.delete(item)

            for cart_item in self.shopping_cart:
                self.cart_tree.insert(
                    "",
                    tk.END,
                    values=(
                        cart_item["product_id"],
                        cart_item["product_name"],
                        f"₹{cart_item['unit_price']:,.2f}",
                        cart_item["quantity"],
                        f"₹{cart_item['subtotal']:,.2f}"
                    )
                )

        total_unique = len(self.shopping_cart)
        total_units = sum(i["quantity"] for i in self.shopping_cart)
        grand_total = sum(i["subtotal"] for i in self.shopping_cart)

        badge_text = f"🛒 Cart: {total_unique} item(s) (₹{grand_total:,.2f})"
        if hasattr(self, "btn_cart_badge"):
            self.btn_cart_badge.config(text=badge_text)

        if hasattr(self, "lbl_pricing_summary"):
            self.lbl_pricing_summary.config(
                text=f"Cart Items: {total_unique} unique SKU(s) | {total_units} total unit(s)\n"
                     f"Grand Total: ₹{grand_total:,.2f}"
            )

    def _modify_cart_qty(self, delta: int):
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showinfo("Select Cart Item", "Please select an item from your cart table to adjust quantity.")
            return

        values = self.cart_tree.item(selected[0], "values")
        product_id = int(values[0])

        for idx, item in enumerate(self.shopping_cart):
            if item["product_id"] == product_id:
                new_qty = item["quantity"] + delta
                if new_qty <= 0:
                    del self.shopping_cart[idx]
                else:
                    item["quantity"] = new_qty
                    item["subtotal"] = new_qty * item["unit_price"]
                break

        self._update_cart_display()
        self._preview_fulfillment_routing()

    def _remove_cart_item(self):
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showinfo("Select Cart Item", "Please select an item from your cart table to remove.")
            return

        values = self.cart_tree.item(selected[0], "values")
        product_id = int(values[0])
        self.shopping_cart = [i for i in self.shopping_cart if i["product_id"] != product_id]
        self._update_cart_display()
        self._preview_fulfillment_routing()

    def _clear_cart(self):
        if not self.shopping_cart:
            return
        if messagebox.askyesno("Clear Cart", "Are you sure you want to remove all items from your cart?"):
            self.shopping_cart = []
            self._update_cart_display()
            for item in self.routing_tree.get_children():
                self.routing_tree.delete(item)
            self.optimal_hub_banner.config(
                text="Cart is empty. Add components from Tab 2 or using the quick-add selector below.",
                bg="#F3F4F6", fg="#6B7280"
            )

    # -------------------------------------------------------------------------
    # TAB 3: MULTI-ITEM SHOPPING CART & PROXIMITY FULFILLMENT ENGINE
    # -------------------------------------------------------------------------
    def _build_order_tab(self):
        container = tk.Frame(self.tab_order, bg=self.BG_MAIN)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Left Column: Cart & Order Actions
        left_col = tk.Frame(container, bg=self.CARD_BG, bd=1, relief=tk.GROOVE)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), ipadx=8, ipady=8)

        tk.Label(left_col, text="1. Multi-Item Shopping Cart & Checkout", font=("Segoe UI", 11, "bold"), bg=self.CARD_BG, fg="#1F2937").pack(anchor=tk.W, padx=10, pady=(2, 6))

        # Customer Delivery Snapshot
        self.order_cust_lbl = tk.Label(
            left_col,
            text="Customer: Please log in as a Customer from Tab 1.",
            font=("Segoe UI", 9),
            bg="#FEF3C7",
            fg="#92400E",
            bd=1,
            relief=tk.SOLID,
            justify=tk.LEFT,
            padx=8,
            pady=5
        )
        self.order_cust_lbl.pack(fill=tk.X, padx=10, pady=(0, 8))

        # Shopping Cart Table Frame
        cart_box = tk.LabelFrame(left_col, text=" Items in Cart ", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG, padx=6, pady=6)
        cart_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        cart_cols = ("ProductID", "ProductName", "UnitPrice", "Quantity", "Subtotal")
        self.cart_tree = ttk.Treeview(cart_box, columns=cart_cols, show="headings", height=5, selectmode="browse")
        self.cart_tree.heading("ProductID", text="ID")
        self.cart_tree.heading("ProductName", text="Component")
        self.cart_tree.heading("UnitPrice", text="Unit Price (₹)")
        self.cart_tree.heading("Quantity", text="Qty")
        self.cart_tree.heading("Subtotal", text="Subtotal (₹)")

        self.cart_tree.column("ProductID", width=40, anchor=tk.CENTER)
        self.cart_tree.column("ProductName", width=180, anchor=tk.W)
        self.cart_tree.column("UnitPrice", width=85, anchor=tk.E)
        self.cart_tree.column("Quantity", width=45, anchor=tk.CENTER)
        self.cart_tree.column("Subtotal", width=95, anchor=tk.E)

        cart_scroll = ttk.Scrollbar(cart_box, orient=tk.VERTICAL, command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_scroll.set)
        self.cart_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cart_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Cart Item Action Buttons
        cart_actions_frame = tk.Frame(left_col, bg=self.CARD_BG)
        cart_actions_frame.pack(fill=tk.X, padx=10, pady=(0, 8))

        tk.Button(cart_actions_frame, text="➕ Qty", font=("Segoe UI", 8, "bold"), bg="#E5E7EB", relief=tk.FLAT, padx=6, pady=2, command=lambda: self._modify_cart_qty(1)).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(cart_actions_frame, text="➖ Qty", font=("Segoe UI", 8, "bold"), bg="#E5E7EB", relief=tk.FLAT, padx=6, pady=2, command=lambda: self._modify_cart_qty(-1)).pack(side=tk.LEFT, padx=4)
        tk.Button(cart_actions_frame, text="🗑️ Remove", font=("Segoe UI", 8), bg="#FEE2E2", fg="#991B1B", relief=tk.FLAT, padx=6, pady=2, command=self._remove_cart_item).pack(side=tk.LEFT, padx=4)
        tk.Button(cart_actions_frame, text="🧹 Clear Cart", font=("Segoe UI", 8), bg="#F3F4F6", fg="#4B5563", relief=tk.FLAT, padx=6, pady=2, command=self._clear_cart).pack(side=tk.RIGHT)

        # Quick Multi-Item Catalog Shortcut
        tk.Button(
            left_col,
            text="🛍️ Select Multiple Items from Catalog (Tab 2)",
            font=("Segoe UI", 9, "bold"),
            bg="#EFF6FF",
            fg="#1E40AF",
            relief=tk.SOLID,
            bd=1,
            padx=10,
            pady=4,
            command=lambda: self.notebook.select(self.tab_catalog)
        ).pack(fill=tk.X, padx=10, pady=(0, 6))

        # Quick Component Add Row
        quick_frame = tk.LabelFrame(left_col, text=" Quick Add Component to Cart ", font=("Segoe UI", 8, "bold"), bg=self.CARD_BG, padx=6, pady=6)
        quick_frame.pack(fill=tk.X, padx=10, pady=(0, 8))

        self.order_product_combo = ttk.Combobox(quick_frame, state="readonly", width=28, font=("Segoe UI", 9))
        self.order_product_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self.spin_quantity = ttk.Spinbox(quick_frame, from_=1, to=100, width=4, font=("Segoe UI", 9))
        self.spin_quantity.set(1)
        self.spin_quantity.pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            quick_frame,
            text="➕ Add",
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=8,
            pady=2,
            command=self._handle_quick_add_to_cart
        ).pack(side=tk.RIGHT)

        # Payment Method & Pricing
        pay_frame = tk.Frame(left_col, bg=self.CARD_BG)
        pay_frame.pack(fill=tk.X, padx=10, pady=(0, 8))

        tk.Label(pay_frame, text="Payment Method:", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).pack(side=tk.LEFT, padx=(0, 6))
        self.order_payment_combo = ttk.Combobox(pay_frame, values=["UPI", "CARD", "NETBANKING", "COD"], state="readonly", width=14, font=("Segoe UI", 9))
        self.order_payment_combo.set("UPI")
        self.order_payment_combo.pack(side=tk.LEFT)

        # Order Grand Total Box
        self.lbl_pricing_summary = tk.Label(
            left_col,
            text="Cart Items: 0 unique SKU(s) | 0 total unit(s)\nGrand Total: ₹0.00",
            font=("Segoe UI", 9, "bold"),
            bg="#F3F4F6",
            fg="#111827",
            bd=1,
            relief=tk.SUNKEN,
            padx=10,
            pady=6,
            justify=tk.LEFT
        )
        self.lbl_pricing_summary.pack(fill=tk.X, padx=10, pady=(0, 8))

        # Action Buttons
        self.btn_preview_routing = tk.Button(
            left_col,
            text="🧭 Preview Haversine Routing for Cart",
            font=("Segoe UI", 9, "bold"),
            bg="#3B82F6",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=10,
            pady=6,
            command=self._preview_fulfillment_routing
        )
        self.btn_preview_routing.pack(fill=tk.X, padx=10, pady=(0, 6))

        self.btn_confirm_order = tk.Button(
            left_col,
            text="⚡ Confirm Multi-Item Order (ACID Commit)",
            font=("Segoe UI", 10, "bold"),
            bg=self.SUCCESS_COLOR,
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=12,
            pady=8,
            command=self._execute_acid_order_transaction
        )
        self.btn_confirm_order.pack(fill=tk.X, padx=10, pady=(0, 4))

        # Right Column: Multi-Item Proximity Routing Visualization
        right_col = tk.Frame(container, bg=self.CARD_BG, bd=1, relief=tk.GROOVE)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(
            right_col,
            text="2. Nearest-Warehouse Proximity Routing Analysis (Haversine Formula)",
            font=("Segoe UI", 11, "bold"),
            bg=self.CARD_BG,
            fg="#1F2937"
        ).pack(anchor=tk.W, padx=14, pady=(10, 4))

        self.routing_explanation_lbl = tk.Label(
            right_col,
            text="Evaluates geodesic distance from customer coordinates to each hub to find the closest hub holding 100% of cart stock.",
            font=("Segoe UI", 9),
            bg=self.CARD_BG,
            fg="#4B5563",
            justify=tk.LEFT
        )
        self.routing_explanation_lbl.pack(anchor=tk.W, padx=14, pady=(0, 8))

        # Candidate Warehouses Treeview
        columns = ("WarehouseID", "WarehouseName", "City", "DistanceKM", "CartStockStatus", "FulfillmentStatus")
        self.routing_tree = ttk.Treeview(right_col, columns=columns, show="headings", height=5)

        self.routing_tree.heading("WarehouseID", text="ID")
        self.routing_tree.heading("WarehouseName", text="Warehouse Hub")
        self.routing_tree.heading("City", text="Hub City")
        self.routing_tree.heading("DistanceKM", text="Haversine Distance (km)")
        self.routing_tree.heading("CartStockStatus", text="Cart Availability")
        self.routing_tree.heading("FulfillmentStatus", text="Routing Decision")

        self.routing_tree.column("WarehouseID", width=35, anchor=tk.CENTER)
        self.routing_tree.column("WarehouseName", width=170, anchor=tk.W)
        self.routing_tree.column("City", width=95, anchor=tk.W)
        self.routing_tree.column("DistanceKM", width=150, anchor=tk.E)
        self.routing_tree.column("CartStockStatus", width=140, anchor=tk.CENTER)
        self.routing_tree.column("FulfillmentStatus", width=160, anchor=tk.W)

        self.routing_tree.pack(fill=tk.X, padx=14, pady=(0, 10))

        # Optimal Hub Callout Banner
        self.optimal_hub_banner = tk.Label(
            right_col,
            text="No active cart route previewed. Add items to cart and click 'Preview Haversine Routing for Cart'.",
            font=("Segoe UI", 9, "bold"),
            bg="#F3F4F6",
            fg="#6B7280",
            bd=1,
            relief=tk.SOLID,
            padx=12,
            pady=8,
            justify=tk.LEFT
        )
        self.optimal_hub_banner.pack(fill=tk.X, padx=14, pady=(0, 10))

        # ACID Transaction Live Telemetry Box
        tk.Label(right_col, text="3. ACID Multi-Item Transaction Log & Telemetry:", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG, fg="#111827").pack(anchor=tk.W, padx=14)
        self.txt_txn_log = tk.Text(right_col, height=8, font=("Consolas", 9), bg="#111827", fg="#10B981")
        self.txt_txn_log.pack(fill=tk.BOTH, expand=True, padx=14, pady=(4, 10))
        self.txt_txn_log.insert(tk.END, "-- Transaction Console Ready. Add items and place order --\n")

        self.products_map: Dict[int, Dict[str, Any]] = {}
        self._populate_product_dropdown()

    def _handle_quick_add_to_cart(self):
        selection = self.order_product_combo.get()
        if not selection:
            messagebox.showwarning("Selection Missing", "Please select a component from the dropdown to add.")
            return

        pid = int(selection.split(" - ")[0].replace("#", ""))
        try:
            qty = max(1, int(self.spin_quantity.get()))
        except ValueError:
            qty = 1

        self._add_product_to_cart(pid, quantity=qty)
        self._update_cart_display()
        self.set_status(f"Added product #{pid} (qty {qty}) to cart.")

    def _populate_product_dropdown(self):
        try:
            conn = get_db_connection(self.db_config)
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT ProductID, SKU, ProductName, UnitPrice FROM PRODUCT ORDER BY ProductID")
            rows = cur.fetchall()
            cur.close()
            conn.close()

            self.products_map = {row["ProductID"]: row for row in rows}
            options = [f"#{r['ProductID']} - {r['ProductName']} (₹{float(r['UnitPrice']):,.2f})" for r in rows]
            self.order_product_combo["values"] = options
            if options:
                self.order_product_combo.current(0)
        except Exception:
            pass

    def _update_order_tab_customer_info(self):
        if self.current_role == "CUSTOMER" and self.current_user:
            c = self.current_user
            self.order_cust_lbl.config(
                text=f"Customer: {c['FullName']}\n"
                     f"City: {c['City']} (Lat: {float(c['Latitude']):.4f}, Lon: {float(c['Longitude']):.4f})\n"
                     f"Address: {c['ShippingAddress'][:30]}...",
                bg="#D1FAE5",
                fg="#065F46"
            )
        else:
            self.order_cust_lbl.config(
                text="Customer: Please log in as a Customer from Tab 1 to checkout.",
                bg="#FEF3C7",
                fg="#92400E"
            )

    def _preview_fulfillment_routing(self) -> Optional[Dict[str, Any]]:
        """
        Runs the multi-item Haversine proximity evaluation on self.shopping_cart.
        """
        if self.current_role != "CUSTOMER" or not self.current_user:
            messagebox.showwarning("Customer Login Required", "Please log in to the Customer Portal from Tab 1 to preview fulfillment.")
            self.notebook.select(self.tab_auth)
            return None

        if not self.shopping_cart:
            messagebox.showwarning("Cart Empty", "Your shopping cart is empty! Please select one or more items from Tab 2 or using the quick-add selector.")
            return None

        c_lat = float(self.current_user["Latitude"])
        c_lon = float(self.current_user["Longitude"])

        for item in self.routing_tree.get_children():
            self.routing_tree.delete(item)

        try:
            conn = get_db_connection(self.db_config)
            evaluations = evaluate_cart_fulfillment(conn, self.shopping_cart, c_lat, c_lon)
            conn.close()

            optimal_hub = None
            for hub in evaluations:
                if hub["can_fulfill_all"] and optimal_hub is None:
                    decision = "★ SELECTED (Optimal Nearest)"
                    optimal_hub = hub
                elif not hub["can_fulfill_all"]:
                    missing = [it["product_name"][:18] for it in hub["items_status"] if not it["has_sufficient_stock"]]
                    decision = f"✗ Missing Stock ({', '.join(missing)})"
                else:
                    decision = "Eligible (Greater Distance)"

                stock_status = "✓ 100% In Stock" if hub["can_fulfill_all"] else "⚠ Partial / Low Stock"

                self.routing_tree.insert(
                    "",
                    tk.END,
                    values=(
                        hub["warehouse_id"],
                        hub["warehouse_name"],
                        hub["city"],
                        f"{hub['distance_km']:.2f} km",
                        stock_status,
                        decision
                    )
                )

            if optimal_hub:
                self.optimal_hub_banner.config(
                    text=f"✓ Optimal Route Found: Dispatching entire order from '{optimal_hub['warehouse_name']}' ({optimal_hub['city']})\n"
                         f"  Geodesic Distance: {optimal_hub['distance_km']:.2f} km | All {len(self.shopping_cart)} line-items available in stock!",
                    bg="#D1FAE5",
                    fg="#065F46"
                )
                self.routing_explanation_lbl.config(
                    text=f"Customer Location: {self.current_user['City']} ({c_lat:.4f}, {c_lon:.4f}). Nearest hub with 100% cart availability selected."
                )
            else:
                self.optimal_hub_banner.config(
                    text="⚠ INSUFFICIENT NETWORK STOCK: No single warehouse holds 100% of the requested quantities for all cart items.",
                    bg="#FEE2E2",
                    fg="#991B1B"
                )

            return optimal_hub

        except Exception as e:
            messagebox.showerror("Routing Error", f"Error calculating cart proximity: {str(e)}")
            return None

    def _execute_acid_order_transaction(self):
        """
        Executes atomic multi-item order placement under strict MySQL transaction isolation.
        Atomically:
        1. FOR UPDATE row locks on all (ProductID, WarehouseID) pairs in cart.
        2. Validates stock for each item.
        3. Decrements stock for each item.
        4. Inserts single parent record into ORDERS.
        5. Inserts multiple line-item records into ORDER_ITEM.
        6. Inserts transaction record into PAYMENT.
        7. Inserts manifest record into SHIPMENT.
        8. Commits (or rolls back on conflict).
        """
        if self.current_role != "CUSTOMER" or not self.current_user:
            messagebox.showwarning("Customer Login Required", "Please log in to the Customer Portal before checking out.")
            self.notebook.select(self.tab_auth)
            return

        if not self.shopping_cart:
            messagebox.showwarning("Cart Empty", "Please add items to your cart before confirming an order.")
            return

        optimal_hub = self._preview_fulfillment_routing()
        if not optimal_hub:
            messagebox.showerror(
                "Transaction Aborted",
                "Cannot fulfill order: No warehouse has sufficient inventory for all items in your cart."
            )
            return

        grand_total = sum(i["subtotal"] for i in self.shopping_cart)
        payment_method = self.order_payment_combo.get()
        customer_id = self.current_user["CustomerID"]
        shipping_address = self.current_user["ShippingAddress"]
        warehouse_id = optimal_hub["warehouse_id"]
        tracking_number = f"TRK-NX-{uuid.uuid4().hex[:10].upper()}"

        self.txt_txn_log.delete("1.0", tk.END)
        self._log_txn("[BEGIN TRANSACTION] Starting atomic multi-item order fulfillment sequence...")

        conn = None
        try:
            conn = get_db_connection(self.db_config, autocommit=False)
            cursor = conn.cursor(dictionary=True)

            # Step 1: Verify & Lock stock for each cart item
            for item in self.shopping_cart:
                pid = item["product_id"]
                req_qty = item["quantity"]
                self._log_txn(f"[LOCK] Acquiring FOR UPDATE lock on PRODUCT_INVENTORY (P:{pid}, W:{warehouse_id})...")
                check_stock_sql = """
                    SELECT StockQuantity 
                    FROM PRODUCT_INVENTORY 
                    WHERE ProductID = %s AND WarehouseID = %s 
                    FOR UPDATE
                """
                cursor.execute(check_stock_sql, (pid, warehouse_id))
                stock_record = cursor.fetchone()

                if not stock_record or stock_record["StockQuantity"] < req_qty:
                    self._log_txn(f"[ERROR] Stock conflict on {item['product_name']}: Required {req_qty}, had {stock_record['StockQuantity'] if stock_record else 0}")
                    self._log_txn("[ROLLBACK] Aborting transaction, 0 records written.")
                    conn.rollback()
                    messagebox.showerror("Order Failed", f"Inventory conflict on '{item['product_name']}'. Transaction rolled back.")
                    cursor.close()
                    conn.close()
                    return

                cur_stk = stock_record["StockQuantity"]
                self._log_txn(f"[INVENTORY] P:{pid} stock {cur_stk} -> deduct {req_qty} -> new {cur_stk - req_qty}")

                # Step 2: Decrement stock
                deduct_sql = """
                    UPDATE PRODUCT_INVENTORY 
                    SET StockQuantity = StockQuantity - %s 
                    WHERE ProductID = %s AND WarehouseID = %s
                """
                cursor.execute(deduct_sql, (req_qty, pid, warehouse_id))

            # Step 3: Insert single parent record into ORDERS
            self._log_txn(f"[ORDERS] Creating Master Order for Customer #{customer_id}, Grand Total: ₹{grand_total:,.2f}...")
            insert_order_sql = """
                INSERT INTO ORDERS (CustomerID, TotalAmount, OrderStatus, ShippingAddress)
                VALUES (%s, %s, 'PROCESSING', %s)
            """
            cursor.execute(insert_order_sql, (customer_id, grand_total, shipping_address))
            order_id = cursor.lastrowid
            self._log_txn(f"[ORDERS] Created OrderID: #{order_id}")

            # Step 4: Insert line-items into ORDER_ITEM
            for item in self.shopping_cart:
                pid = item["product_id"]
                qty = item["quantity"]
                uprice = item["unit_price"]
                self._log_txn(f"[ORDER_ITEM] Inserting line-item: P:{pid} x {qty} @ ₹{uprice:,.2f}...")
                insert_item_sql = """
                    INSERT INTO ORDER_ITEM (OrderID, ProductID, Quantity, UnitPriceAtSale)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_item_sql, (order_id, pid, qty, uprice))

            # Step 5: Insert into PAYMENT
            self._log_txn(f"[PAYMENT] Recording payment via {payment_method} for ₹{grand_total:,.2f} (Status: COMPLETED)...")
            insert_payment_sql = """
                INSERT INTO PAYMENT (OrderID, PaymentMethod, AmountPaid, PaymentStatus)
                VALUES (%s, %s, %s, 'COMPLETED')
            """
            cursor.execute(insert_payment_sql, (order_id, payment_method, grand_total))

            # Step 6: Insert into SHIPMENT
            self._log_txn(f"[SHIPMENT] Generating dispatch manifest from Hub '{optimal_hub['warehouse_name']}'...")
            insert_shipment_sql = """
                INSERT INTO SHIPMENT (OrderID, WarehouseID, TrackingNumber, DispatchedDate, DeliveryStatus)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, 'PREPARING')
            """
            cursor.execute(insert_shipment_sql, (order_id, warehouse_id, tracking_number))

            # Step 7: Commit transaction atomically
            conn.commit()
            self._log_txn("[COMMIT] Multi-Item ACID Transaction committed successfully to MySQL 8.0!")
            self._log_txn(f"[SUCCESS] Order #{order_id} active. Tracking: {tracking_number}")

            cursor.close()
            conn.close()

            # Preserve cart items for email receipt and clear cart
            placed_items = list(self.shopping_cart)

            # --- AUTOMATED SMTP NOTIFICATION DISPATCH ---
            # 1. Notify Customer with Itemized Order Confirmation
            if self.current_user and self.current_user.get("Email"):
                notify_customer_order_placed(
                    customer_email=self.current_user["Email"],
                    customer_name=self.current_user.get("FullName", "Customer"),
                    order_id=order_id,
                    total_amount=grand_total,
                    items=placed_items,
                    shipping_address=shipping_address,
                    warehouse_name=optimal_hub["warehouse_name"],
                    tracking_number=tracking_number
                )
                self._log_txn(f"[SMTP] Order confirmation email dispatched to Customer ({self.current_user['Email']})")

            # 2. Notify Assigned Hub Manager (e.g. samarth@gmail.com) of New Dispatch Task
            try:
                mgr_conn = get_db_connection(self.db_config)
                mgr_cur = mgr_conn.cursor(dictionary=True)
                mgr_cur.execute(
                    "SELECT FullName, Email FROM STAFF_USER WHERE Role = 'WAREHOUSE_MANAGER' AND AssignedWarehouseID = %s LIMIT 1",
                    (warehouse_id,)
                )
                mgr_user = mgr_cur.fetchone()
                mgr_cur.close()
                mgr_conn.close()

                if mgr_user and mgr_user.get("Email"):
                    notify_hub_manager_new_order(
                        manager_email=mgr_user["Email"],
                        manager_name=mgr_user.get("FullName", "Hub Manager"),
                        warehouse_name=optimal_hub["warehouse_name"],
                        order_id=order_id,
                        customer_name=self.current_user.get("FullName", "Customer") if self.current_user else "Customer",
                        destination_city=self.current_user.get("City", "") if self.current_user else "",
                        items=placed_items,
                        tracking_number=tracking_number
                    )
                    self._log_txn(f"[SMTP] Incoming order dispatch alert sent to Hub Manager ({mgr_user['Email']})")
            except Exception as e:
                print(f"Error dispatching manager alert: {e}")

            # 3. Check for Depleted Stock & Send Low Stock Warning if triggered
            try:
                for it in placed_items:
                    pid = it["product_id"]
                    chk_conn = get_db_connection(self.db_config)
                    chk_cur = chk_conn.cursor(dictionary=True)
                    chk_cur.execute("""
                        SELECT pi.StockQuantity, pi.ReorderLevel, p.ProductName, p.SKU, w.WarehouseName, su.Email as ManagerEmail, su.FullName as ManagerName
                        FROM PRODUCT_INVENTORY pi
                        INNER JOIN PRODUCT p ON pi.ProductID = p.ProductID
                        INNER JOIN WAREHOUSE w ON pi.WarehouseID = w.WarehouseID
                        LEFT JOIN STAFF_USER su ON su.Role = 'WAREHOUSE_MANAGER' AND su.AssignedWarehouseID = pi.WarehouseID
                        WHERE pi.ProductID = %s AND pi.WarehouseID = %s
                    """, (pid, warehouse_id))
                    stk_info = chk_cur.fetchone()
                    chk_cur.close()
                    chk_conn.close()

                    if stk_info and stk_info["StockQuantity"] <= stk_info["ReorderLevel"] and stk_info.get("ManagerEmail"):
                        notify_hub_manager_low_stock(
                            manager_email=stk_info["ManagerEmail"],
                            manager_name=stk_info.get("ManagerName", "Hub Manager"),
                            warehouse_name=stk_info["WarehouseName"],
                            product_name=stk_info["ProductName"],
                            sku=stk_info["SKU"],
                            current_stock=stk_info["StockQuantity"],
                            reorder_level=stk_info["ReorderLevel"]
                        )
                        self._log_txn(f"[SMTP] Low stock alert sent for {stk_info['SKU']} to {stk_info['ManagerEmail']}")
            except Exception as e:
                print(f"Error checking low stock threshold: {e}")

            # Build itemized confirmation receipt
            items_summary_text = "\n".join([f"• {it['product_name']} x {it['quantity']} = ₹{it['subtotal']:,.2f}" for it in placed_items])
            receipt_msg = (
                f"🎉 Multi-Item Order Placed Successfully!\n\n"
                f"Order ID: #{order_id}\n"
                f"Line Items ({len(placed_items)} unique items):\n{items_summary_text}\n\n"
                f"Grand Total Paid: ₹{grand_total:,.2f} ({payment_method})\n"
                f"Fulfillment Hub: {optimal_hub['warehouse_name']} ({optimal_hub['city']})\n"
                f"Delivery Distance: {optimal_hub['distance_km']:.2f} km\n"
                f"Tracking Number: {tracking_number}\n\n"
                f"Status: PREPARING FOR DISPATCH\n\n"
                f"✉ An email confirmation has been dispatched to your email address."
            )

            # Clear cart
            self.shopping_cart = []
            self._update_cart_display()

            # Refresh views
            self.refresh_catalog()
            self.refresh_warehouse_monitor()
            self.refresh_order_history()
            self.refresh_manager_hub_view()

            messagebox.showinfo("Order Confirmation", receipt_msg)

        except Exception as e:
            if conn:
                conn.rollback()
            self._log_txn(f"[ROLLBACK] Exception encountered: {str(e)}")
            messagebox.showerror("Transaction Rolled Back", f"Order could not be processed:\n{str(e)}")
        finally:
            if conn and conn.is_connected():
                conn.close()

    def _log_txn(self, text: str):
        self.txt_txn_log.insert(tk.END, text + "\n")
        self.txt_txn_log.see(tk.END)

    # -------------------------------------------------------------------------
    # TAB 4: WAREHOUSE STOCK MONITOR (vw_WarehouseStockBreakdown)
    # -------------------------------------------------------------------------
    def _build_warehouse_tab(self):
        container = tk.Frame(self.tab_warehouse, bg=self.BG_MAIN)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        control_bar = tk.Frame(container, bg=self.BG_MAIN)
        control_bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            control_bar,
            text="Multi-Warehouse Stock Breakdown (vw_WarehouseStockBreakdown)",
            font=("Segoe UI", 11, "bold"),
            bg=self.BG_MAIN,
            fg="#111827"
        ).pack(side=tk.LEFT)

        btn_refresh = tk.Button(
            control_bar,
            text="🔄 Refresh Hub Breakdown",
            font=("Segoe UI", 9, "bold"),
            bg="#3B82F6",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            command=self.refresh_warehouse_monitor
        )
        btn_refresh.pack(side=tk.RIGHT)

        # Treeview
        columns = ("ProductID", "ProductName", "WarehouseName", "City", "StockQuantity", "ReorderLevel", "StockStatus")
        self.wh_tree = ttk.Treeview(container, columns=columns, show="headings", selectmode="browse")

        self.wh_tree.heading("ProductID", text="Product ID")
        self.wh_tree.heading("ProductName", text="Product Name")
        self.wh_tree.heading("WarehouseName", text="Warehouse Hub")
        self.wh_tree.heading("City", text="City")
        self.wh_tree.heading("StockQuantity", text="Remaining Stock")
        self.wh_tree.heading("ReorderLevel", text="Reorder Level")
        self.wh_tree.heading("StockStatus", text="Status")

        self.wh_tree.column("ProductID", width=70, anchor=tk.CENTER)
        self.wh_tree.column("ProductName", width=320, anchor=tk.W)
        self.wh_tree.column("WarehouseName", width=220, anchor=tk.W)
        self.wh_tree.column("City", width=120, anchor=tk.W)
        self.wh_tree.column("StockQuantity", width=120, anchor=tk.CENTER)
        self.wh_tree.column("ReorderLevel", width=100, anchor=tk.CENTER)
        self.wh_tree.column("StockStatus", width=130, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.wh_tree.yview)
        self.wh_tree.configure(yscrollcommand=scrollbar.set)

        self.wh_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh_warehouse_monitor(self):
        for item in self.wh_tree.get_children():
            self.wh_tree.delete(item)

        try:
            conn = get_db_connection(self.db_config)
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM vw_WarehouseStockBreakdown ORDER BY ProductID, WarehouseName")
            rows = cur.fetchall()
            cur.close()
            conn.close()

            for row in rows:
                self.wh_tree.insert(
                    "",
                    tk.END,
                    values=(
                        row["ProductID"],
                        row["ProductName"],
                        row["WarehouseName"],
                        row["City"],
                        row["StockQuantity"],
                        row["ReorderLevel"],
                        row["StockStatus"]
                    )
                )
            self.set_status(f"Warehouse monitor updated ({len(rows)} hub-product mappings).")
        except Exception as e:
            self.set_status(f"Failed to refresh warehouse monitor: {str(e)}", is_error=True)

    # -------------------------------------------------------------------------
    # TAB 5: ORDER HISTORY & SHIPMENT TRACKER
    # -------------------------------------------------------------------------
    def _build_history_tab(self):
        container = tk.Frame(self.tab_history, bg=self.BG_MAIN)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        control_bar = tk.Frame(container, bg=self.BG_MAIN)
        control_bar.pack(fill=tk.X, pady=(0, 10))

        self.lbl_history_title = tk.Label(
            control_bar,
            text="Order History & Live Shipment Tracking",
            font=("Segoe UI", 11, "bold"),
            bg=self.BG_MAIN,
            fg="#111827"
        )
        self.lbl_history_title.pack(side=tk.LEFT)

        btn_refresh = tk.Button(
            control_bar,
            text="🔄 Refresh Orders",
            font=("Segoe UI", 9, "bold"),
            bg="#3B82F6",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            command=self.refresh_order_history
        )
        btn_refresh.pack(side=tk.RIGHT)

        columns = ("OrderID", "OrderDate", "CustomerName", "ProductName", "Quantity", "TotalAmount", "Payment", "TrackingNumber", "DispatchedFrom", "DeliveryStatus")
        self.history_tree = ttk.Treeview(container, columns=columns, show="headings", selectmode="browse")

        self.history_tree.heading("OrderID", text="Order #")
        self.history_tree.heading("OrderDate", text="Date & Time")
        self.history_tree.heading("CustomerName", text="Customer")
        self.history_tree.heading("ProductName", text="Product")
        self.history_tree.heading("Quantity", text="Qty")
        self.history_tree.heading("TotalAmount", text="Total Paid")
        self.history_tree.heading("Payment", text="Method")
        self.history_tree.heading("TrackingNumber", text="Tracking Number")
        self.history_tree.heading("DispatchedFrom", text="Dispatched Hub")
        self.history_tree.heading("DeliveryStatus", text="Delivery Status")

        self.history_tree.column("OrderID", width=60, anchor=tk.CENTER)
        self.history_tree.column("OrderDate", width=130, anchor=tk.CENTER)
        self.history_tree.column("CustomerName", width=120, anchor=tk.W)
        self.history_tree.column("ProductName", width=220, anchor=tk.W)
        self.history_tree.column("Quantity", width=50, anchor=tk.CENTER)
        self.history_tree.column("TotalAmount", width=95, anchor=tk.E)
        self.history_tree.column("Payment", width=80, anchor=tk.CENTER)
        self.history_tree.column("TrackingNumber", width=170, anchor=tk.CENTER)
        self.history_tree.column("DispatchedFrom", width=160, anchor=tk.W)
        self.history_tree.column("DeliveryStatus", width=120, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh_order_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        try:
            conn = get_db_connection(self.db_config)
            cur = conn.cursor(dictionary=True)

            query = """
                SELECT 
                    o.OrderID,
                    o.OrderDate,
                    c.FullName AS CustomerName,
                    p.ProductName,
                    oi.Quantity,
                    o.TotalAmount,
                    pay.PaymentMethod,
                    s.TrackingNumber,
                    w.WarehouseName AS DispatchedFrom,
                    s.DeliveryStatus
                FROM ORDERS o
                INNER JOIN CUSTOMER c ON o.CustomerID = c.CustomerID
                INNER JOIN ORDER_ITEM oi ON o.OrderID = oi.OrderID
                INNER JOIN PRODUCT p ON oi.ProductID = p.ProductID
                LEFT JOIN PAYMENT pay ON o.OrderID = pay.OrderID
                LEFT JOIN SHIPMENT s ON o.OrderID = s.OrderID
                LEFT JOIN WAREHOUSE w ON s.WarehouseID = w.WarehouseID
            """
            params = []
            if self.current_role == "CUSTOMER" and self.current_user:
                query += " WHERE o.CustomerID = %s"
                params.append(self.current_user["CustomerID"])
                self.lbl_history_title.config(text=f"Order History for {self.current_user['FullName']}")
            elif self.current_role == "ADMIN":
                self.lbl_history_title.config(text="Global Customer Order Ledger (Administrator View)")
            else:
                self.lbl_history_title.config(text="Order History (Please log in to view orders)")

            query += " ORDER BY o.OrderID DESC"
            cur.execute(query, params)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            for row in rows:
                self.history_tree.insert(
                    "",
                    tk.END,
                    values=(
                        f"#{row['OrderID']}",
                        str(row["OrderDate"])[:19],
                        row["CustomerName"],
                        row["ProductName"],
                        row["Quantity"],
                        f"₹{float(row['TotalAmount']):,.2f}",
                        row["PaymentMethod"],
                        row["TrackingNumber"] or "N/A",
                        row["DispatchedFrom"] or "N/A",
                        row["DeliveryStatus"] or "PENDING"
                    )
                )

        except Exception as e:
            self.set_status(f"Error fetching orders: {str(e)}", is_error=True)

    # -------------------------------------------------------------------------
    # TAB 6: WAREHOUSE MANAGER OPERATIONS PORTAL
    # -------------------------------------------------------------------------
    def _build_manager_tab(self):
        container = tk.Frame(self.tab_manager, bg=self.BG_MAIN)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Manager Header / Hub Assignment Banner
        self.mgr_hub_banner = tk.Label(
            container,
            text="Warehouse Manager Operations Portal: Log in with a Manager account to manage hub inventory and shipments.",
            font=("Segoe UI", 10, "bold"),
            bg="#FEF3C7",
            fg="#92400E",
            bd=1,
            relief=tk.SOLID,
            padx=14,
            pady=8,
            anchor=tk.W
        )
        self.mgr_hub_banner.pack(fill=tk.X, pady=(0, 12))

        # Main Split: Top (Inventory & Restock), Bottom (Shipments & Dispatch)
        # Top: Inventory at this Hub
        inv_frame = tk.LabelFrame(container, text=" Local Hub Inventory & Restock Controls ", font=("Segoe UI", 10, "bold"), bg=self.CARD_BG, padx=12, pady=10)
        inv_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Treeview for hub inventory
        inv_cols = ("ProductID", "ProductName", "StockQuantity", "ReorderLevel", "StockStatus")
        self.mgr_inv_tree = ttk.Treeview(inv_frame, columns=inv_cols, show="headings", height=5)
        self.mgr_inv_tree.heading("ProductID", text="ID")
        self.mgr_inv_tree.heading("ProductName", text="Keyboard Component / Product")
        self.mgr_inv_tree.heading("StockQuantity", text="Current Stock")
        self.mgr_inv_tree.heading("ReorderLevel", text="Reorder Level")
        self.mgr_inv_tree.heading("StockStatus", text="Status")

        self.mgr_inv_tree.column("ProductID", width=50, anchor=tk.CENTER)
        self.mgr_inv_tree.column("ProductName", width=380, anchor=tk.W)
        self.mgr_inv_tree.column("StockQuantity", width=120, anchor=tk.CENTER)
        self.mgr_inv_tree.column("ReorderLevel", width=120, anchor=tk.CENTER)
        self.mgr_inv_tree.column("StockStatus", width=140, anchor=tk.CENTER)

        inv_scroll = ttk.Scrollbar(inv_frame, orient=tk.VERTICAL, command=self.mgr_inv_tree.yview)
        self.mgr_inv_tree.configure(yscrollcommand=inv_scroll.set)
        self.mgr_inv_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        inv_scroll.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        # Restock Actions Sidebar
        restock_panel = tk.Frame(inv_frame, bg=self.CARD_BG)
        restock_panel.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(restock_panel, text="Restock Amount:", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).pack(anchor=tk.W, pady=(4, 2))
        self.spin_restock_qty = ttk.Spinbox(restock_panel, from_=5, to=1000, increment=5, width=12, font=("Segoe UI", 10))
        self.spin_restock_qty.set(25)
        self.spin_restock_qty.pack(anchor=tk.W, pady=(0, 10))

        btn_restock = tk.Button(
            restock_panel,
            text="📦 Restock Selected",
            font=("Segoe UI", 9, "bold"),
            bg=self.SUCCESS_COLOR,
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            command=self._handle_manager_restock
        )
        btn_restock.pack(fill=tk.X, pady=(0, 6))

        btn_refresh_mgr = tk.Button(
            restock_panel,
            text="🔄 Refresh Hub",
            font=("Segoe UI", 9),
            bg="#E5E7EB",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            command=self.refresh_manager_hub_view
        )
        btn_refresh_mgr.pack(fill=tk.X)

        # Bottom: Shipments Routed to this Hub
        ship_frame = tk.LabelFrame(container, text=" Incoming Hub Dispatch Manifest & Shipment Tracking ", font=("Segoe UI", 10, "bold"), bg=self.CARD_BG, padx=12, pady=10)
        ship_frame.pack(fill=tk.BOTH, expand=True)

        ship_cols = ("ShipmentID", "OrderID", "TrackingNumber", "CustomerName", "DeliveryCity", "DeliveryStatus", "DispatchedDate")
        self.mgr_ship_tree = ttk.Treeview(ship_frame, columns=ship_cols, show="headings", height=5)
        self.mgr_ship_tree.heading("ShipmentID", text="Shipment #")
        self.mgr_ship_tree.heading("OrderID", text="Order #")
        self.mgr_ship_tree.heading("TrackingNumber", text="Tracking Number")
        self.mgr_ship_tree.heading("CustomerName", text="Customer")
        self.mgr_ship_tree.heading("DeliveryCity", text="Destination City")
        self.mgr_ship_tree.heading("DeliveryStatus", text="Current Status")
        self.mgr_ship_tree.heading("DispatchedDate", text="Dispatched Timestamp")

        self.mgr_ship_tree.column("ShipmentID", width=80, anchor=tk.CENTER)
        self.mgr_ship_tree.column("OrderID", width=60, anchor=tk.CENTER)
        self.mgr_ship_tree.column("TrackingNumber", width=170, anchor=tk.CENTER)
        self.mgr_ship_tree.column("CustomerName", width=140, anchor=tk.W)
        self.mgr_ship_tree.column("DeliveryCity", width=110, anchor=tk.W)
        self.mgr_ship_tree.column("DeliveryStatus", width=130, anchor=tk.CENTER)
        self.mgr_ship_tree.column("DispatchedDate", width=150, anchor=tk.CENTER)

        ship_scroll = ttk.Scrollbar(ship_frame, orient=tk.VERTICAL, command=self.mgr_ship_tree.yview)
        self.mgr_ship_tree.configure(yscrollcommand=ship_scroll.set)
        self.mgr_ship_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ship_scroll.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        # Status Update Sidebar
        status_panel = tk.Frame(ship_frame, bg=self.CARD_BG)
        status_panel.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(status_panel, text="Update Status:", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).pack(anchor=tk.W, pady=(4, 2))
        self.combo_ship_status = ttk.Combobox(
            status_panel,
            values=["PREPARING", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED"],
            state="readonly",
            width=16,
            font=("Segoe UI", 9)
        )
        self.combo_ship_status.set("IN_TRANSIT")
        self.combo_ship_status.pack(anchor=tk.W, pady=(0, 10))

        btn_update_ship = tk.Button(
            status_panel,
            text="🚚 Update Status",
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            command=self._handle_manager_update_shipment
        )
        btn_update_ship.pack(fill=tk.X)

    def refresh_manager_hub_view(self):
        for item in self.mgr_inv_tree.get_children():
            self.mgr_inv_tree.delete(item)
        for item in self.mgr_ship_tree.get_children():
            self.mgr_ship_tree.delete(item)

        if not self.current_user or (self.current_role != "WAREHOUSE_MANAGER" and self.current_role != "ADMIN"):
            self.mgr_hub_banner.config(
                text="Warehouse Manager Operations: Please log in as a Warehouse Manager or Administrator from Tab 1.",
                bg="#FEF3C7", fg="#92400E"
            )
            return

        # Determine target warehouse
        wh_id = self.current_user.get("AssignedWarehouseID") or 1

        try:
            conn = get_db_connection(self.db_config)
            cur = conn.cursor(dictionary=True)

            # Get Warehouse Details
            cur.execute("SELECT * FROM WAREHOUSE WHERE WarehouseID = %s", (wh_id,))
            wh = cur.fetchone()
            if wh:
                self.mgr_hub_banner.config(
                    text=f"🏭 Active Operations Hub: {wh['WarehouseName']} ({wh['City']}, {wh['State']}) | "
                         f"Coordinates: {float(wh['Latitude']):.4f}° N, {float(wh['Longitude']):.4f}° E | Storage Capacity: {wh['Capacity']:,} units",
                    bg="#D1FAE5", fg="#065F46"
                )

            # Fetch Local Inventory
            cur.execute("""
                SELECT 
                    p.ProductID,
                    p.ProductName,
                    pi.StockQuantity,
                    pi.ReorderLevel,
                    CASE 
                        WHEN pi.StockQuantity = 0 THEN 'OUT_OF_STOCK'
                        WHEN pi.StockQuantity <= pi.ReorderLevel THEN 'LOW_STOCK'
                        ELSE 'OPTIMAL'
                    END AS StockStatus
                FROM PRODUCT_INVENTORY pi
                INNER JOIN PRODUCT p ON pi.ProductID = p.ProductID
                WHERE pi.WarehouseID = %s
                ORDER BY pi.StockQuantity ASC
            """, (wh_id,))
            inv_rows = cur.fetchall()
            for r in inv_rows:
                self.mgr_inv_tree.insert("", tk.END, values=(
                    r["ProductID"],
                    r["ProductName"],
                    r["StockQuantity"],
                    r["ReorderLevel"],
                    r["StockStatus"]
                ))

            # Fetch Hub Shipments
            cur.execute("""
                SELECT 
                    s.ShipmentID,
                    s.OrderID,
                    s.TrackingNumber,
                    c.FullName AS CustomerName,
                    c.City AS DeliveryCity,
                    s.DeliveryStatus,
                    s.DispatchedDate
                FROM SHIPMENT s
                INNER JOIN ORDERS o ON s.OrderID = o.OrderID
                INNER JOIN CUSTOMER c ON o.CustomerID = c.CustomerID
                WHERE s.WarehouseID = %s
                ORDER BY s.ShipmentID DESC
            """, (wh_id,))
            ship_rows = cur.fetchall()
            for s in ship_rows:
                self.mgr_ship_tree.insert("", tk.END, values=(
                    s["ShipmentID"],
                    s["OrderID"],
                    s["TrackingNumber"],
                    s["CustomerName"],
                    s["DeliveryCity"],
                    s["DeliveryStatus"],
                    str(s["DispatchedDate"])[:19] if s["DispatchedDate"] else "PENDING DISPATCH"
                ))

            cur.close()
            conn.close()

        except Exception as e:
            self.set_status(f"Error loading manager view: {str(e)}", is_error=True)

    def _handle_manager_restock(self):
        if not self.current_user or (self.current_role != "WAREHOUSE_MANAGER" and self.current_role != "ADMIN"):
            messagebox.showwarning("Restricted", "Only Warehouse Managers or Admins can restock inventory.")
            return

        selected = self.mgr_inv_tree.selection()
        if not selected:
            messagebox.showinfo("Select Product", "Please select a product row from the inventory list to restock.")
            return

        values = self.mgr_inv_tree.item(selected[0], "values")
        product_id = int(values[0])
        product_name = values[1]

        try:
            restock_amt = int(self.spin_restock_qty.get())
            if restock_amt <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Invalid Amount", "Please enter a valid positive restock quantity.")
            return

        wh_id = self.current_user.get("AssignedWarehouseID") or 1

        try:
            conn = get_db_connection(self.db_config, autocommit=True)
            cur = conn.cursor()
            cur.execute("""
                UPDATE PRODUCT_INVENTORY 
                SET StockQuantity = StockQuantity + %s 
                WHERE ProductID = %s AND WarehouseID = %s
            """, (restock_amt, product_id, wh_id))
            cur.close()
            conn.close()

            # Audit log intake event in INVENTORY_INTAKE
            staff_id = self.current_user.get("StaffID") if self.current_user else None
            record_intake(wh_id, product_id, restock_amt, staff_id)

            messagebox.showinfo("Stock Updated", f"Successfully added +{restock_amt} units to '{product_name}' at Hub #{wh_id}!")
            self.refresh_manager_hub_view()
            self.refresh_catalog()
            self.refresh_warehouse_monitor()
            self.refresh_eda_view()

        except Exception as e:
            messagebox.showerror("Restock Failed", f"Database error updating stock: {str(e)}")

    def _handle_manager_update_shipment(self):
        if not self.current_user or (self.current_role != "WAREHOUSE_MANAGER" and self.current_role != "ADMIN"):
            messagebox.showwarning("Restricted", "Only Warehouse Managers or Admins can update shipment statuses.")
            return

        selected = self.mgr_ship_tree.selection()
        if not selected:
            messagebox.showinfo("Select Shipment", "Please select a shipment row to update.")
            return

        values = self.mgr_ship_tree.item(selected[0], "values")
        shipment_id = int(values[0])
        tracking_no = values[2]
        new_status = self.combo_ship_status.get()

        try:
            conn = get_db_connection(self.db_config, autocommit=True)
            cur = conn.cursor()
            cur.execute("""
                UPDATE SHIPMENT 
                SET DeliveryStatus = %s,
                    DispatchedDate = CASE 
                        WHEN %s IN ('IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED') AND DispatchedDate IS NULL 
                        THEN CURRENT_TIMESTAMP 
                        ELSE DispatchedDate 
                    END
                WHERE ShipmentID = %s
            """, (new_status, new_status, shipment_id))
            cur.close()
            conn.close()

            # Automated SMTP Customer Notification Dispatch
            try:
                info_conn = get_db_connection(self.db_config)
                info_cur = info_conn.cursor(dictionary=True)
                info_cur.execute("""
                    SELECT c.Email, c.FullName, s.OrderID, s.TrackingNumber, w.WarehouseName
                    FROM SHIPMENT s
                    INNER JOIN ORDERS o ON s.OrderID = o.OrderID
                    INNER JOIN CUSTOMER c ON o.CustomerID = c.CustomerID
                    INNER JOIN WAREHOUSE w ON s.WarehouseID = w.WarehouseID
                    WHERE s.ShipmentID = %s
                """, (shipment_id,))
                ship_info = info_cur.fetchone()
                info_cur.close()
                info_conn.close()

                if ship_info and ship_info.get("Email"):
                    notify_customer_shipment_updated(
                        customer_email=ship_info["Email"],
                        customer_name=ship_info.get("FullName", "Customer"),
                        order_id=ship_info["OrderID"],
                        tracking_number=ship_info["TrackingNumber"],
                        new_status=new_status,
                        warehouse_name=ship_info["WarehouseName"]
                    )
            except Exception as e:
                print(f"Error dispatching shipment email: {e}")

            messagebox.showinfo("Shipment Updated", f"Tracking: {tracking_no}\nStatus updated to '{new_status}'.\n\n✉ Automated status update email dispatched to customer.")
            self.refresh_manager_hub_view()
            self.refresh_order_history()

        except Exception as e:
            messagebox.showerror("Update Error", f"Could not update shipment: {str(e)}")

    # -------------------------------------------------------------------------
    # TAB 7: SYSTEM ADMINISTRATOR SUITE & ANALYTICS
    # -------------------------------------------------------------------------
    def _build_admin_tab(self):
        container = tk.Frame(self.tab_admin, bg=self.BG_MAIN)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Admin Banner
        admin_banner = tk.Label(
            container,
            text="🛡️ System Administration & Master Data Management (BACSE202 Architecture)",
            font=("Segoe UI", 11, "bold"),
            bg="#FEE2E2",
            fg="#991B1B",
            bd=1,
            relief=tk.SOLID,
            padx=14,
            pady=8,
            anchor=tk.W
        )
        admin_banner.pack(fill=tk.X, pady=(0, 10))

        # KPI Metrics Cards Frame
        kpi_frame = tk.Frame(container, bg=self.BG_MAIN)
        kpi_frame.pack(fill=tk.X, pady=(0, 12))

        self.kpi_revenue = self._create_kpi_card(kpi_frame, "Total Platform Revenue", "₹0.00", "#1E3A8A", "#DBEAFE")
        self.kpi_orders = self._create_kpi_card(kpi_frame, "Total Orders Placed", "0", "#065F46", "#D1FAE5")
        self.kpi_products = self._create_kpi_card(kpi_frame, "Active Products", "0", "#7C2D12", "#FFEDD5")
        self.kpi_warehouses = self._create_kpi_card(kpi_frame, "Fulfillment Hubs", "0", "#581C87", "#F3E8FF")
        self.kpi_low_stock = self._create_kpi_card(kpi_frame, "Low / Out-of-Stock SKUs", "0", "#991B1B", "#FEE2E2")

        # Admin Actions Notebook (Product Manager, Category Manager, Warehouse Manager)
        admin_sub_notebook = ttk.Notebook(container)
        admin_sub_notebook.pack(fill=tk.BOTH, expand=True)

        tab_add_product = ttk.Frame(admin_sub_notebook)
        tab_add_category = ttk.Frame(admin_sub_notebook)
        tab_add_warehouse = ttk.Frame(admin_sub_notebook)
        tab_mail_directive = ttk.Frame(admin_sub_notebook)

        admin_sub_notebook.add(tab_add_product, text=" ➕ Add New Component / Product ")
        admin_sub_notebook.add(tab_add_category, text=" 📁 Add Category ")
        admin_sub_notebook.add(tab_add_warehouse, text=" 📍 Add Fulfillment Warehouse ")
        admin_sub_notebook.add(tab_mail_directive, text=" ✉️ Email Hub Managers ")

        # Sub-Tab 1: Add New Product
        self._build_add_product_form(tab_add_product)
        # Sub-Tab 2: Add New Category
        self._build_add_category_form(tab_add_category)
        # Sub-Tab 3: Add New Warehouse
        self._build_add_warehouse_form(tab_add_warehouse)
        # Sub-Tab 4: Admin Directive Dispatcher
        self._build_admin_mailer_form(tab_mail_directive)

    def _create_kpi_card(self, parent, title: str, initial_val: str, fg_col: str, bg_col: str):
        card = tk.Frame(parent, bg=bg_col, bd=1, relief=tk.SOLID, padx=12, pady=8)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        tk.Label(card, text=title, font=("Segoe UI", 8, "bold"), bg=bg_col, fg="#4B5563").pack(anchor=tk.W)
        lbl_val = tk.Label(card, text=initial_val, font=("Segoe UI", 13, "bold"), bg=bg_col, fg=fg_col)
        lbl_val.pack(anchor=tk.W, pady=(2, 0))
        return lbl_val

    def refresh_admin_analytics(self):
        try:
            conn = get_db_connection(self.db_config)
            cur = conn.cursor(dictionary=True)

            # Total Revenue
            cur.execute("SELECT COALESCE(SUM(TotalAmount), 0) AS TotalRev FROM ORDERS WHERE OrderStatus != 'CANCELLED'")
            tot_rev = float(cur.fetchone()["TotalRev"])
            self.kpi_revenue.config(text=f"₹{tot_rev:,.2f}")

            # Total Orders
            cur.execute("SELECT COUNT(*) AS OrderCount FROM ORDERS")
            self.kpi_orders.config(text=str(cur.fetchone()["OrderCount"]))

            # Active Products
            cur.execute("SELECT COUNT(*) AS ProdCount FROM PRODUCT")
            self.kpi_products.config(text=str(cur.fetchone()["ProdCount"]))

            # Fulfillment Hubs
            cur.execute("SELECT COUNT(*) AS WhCount FROM WAREHOUSE")
            self.kpi_warehouses.config(text=str(cur.fetchone()["WhCount"]))

            # Low / Out of stock SKUs across network
            cur.execute("SELECT COUNT(*) AS LowCount FROM vw_WarehouseStockBreakdown WHERE StockStatus IN ('LOW_STOCK', 'OUT_OF_STOCK')")
            self.kpi_low_stock.config(text=str(cur.fetchone()["LowCount"]))

            cur.close()
            conn.close()

        except Exception as e:
            self.set_status(f"Error loading analytics: {str(e)}", is_error=True)

    def _build_add_product_form(self, parent):
        f = tk.Frame(parent, bg=self.CARD_BG, padx=25, pady=20)
        f.pack(fill=tk.BOTH, expand=True)

        tk.Label(f, text="Insert New Mechanical Keyboard Hardware SKU into PRODUCT Table", font=("Segoe UI", 10, "bold"), bg=self.CARD_BG, fg="#1F2937").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))

        tk.Label(f, text="Product Name *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=1, column=0, sticky=tk.W, pady=6)
        self.adm_prod_name = ttk.Entry(f, width=40, font=("Segoe UI", 10))
        self.adm_prod_name.grid(row=1, column=1, sticky=tk.W, pady=6, padx=10)

        tk.Label(f, text="SKU Identifier *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=2, column=0, sticky=tk.W, pady=6)
        self.adm_prod_sku = ttk.Entry(f, width=40, font=("Segoe UI", 10))
        self.adm_prod_sku.grid(row=2, column=1, sticky=tk.W, pady=6, padx=10)

        tk.Label(f, text="Category *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=3, column=0, sticky=tk.W, pady=6)
        self.adm_prod_cat = ttk.Combobox(f, values=["1 - Mechanical Keyboards", "2 - Mechanical Switches", "3 - Keycaps & Accessories"], state="readonly", width=38, font=("Segoe UI", 10))
        self.adm_prod_cat.current(0)
        self.adm_prod_cat.grid(row=3, column=1, sticky=tk.W, pady=6, padx=10)

        tk.Label(f, text="Unit Price (₹ INR) *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=4, column=0, sticky=tk.W, pady=6)
        self.adm_prod_price = ttk.Entry(f, width=20, font=("Segoe UI", 10))
        self.adm_prod_price.insert(0, "4999.00")
        self.adm_prod_price.grid(row=4, column=1, sticky=tk.W, pady=6, padx=10)

        tk.Label(f, text="Initial Stock per Hub", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=5, column=0, sticky=tk.W, pady=6)
        self.adm_prod_stock = ttk.Spinbox(f, from_=0, to=1000, width=12, font=("Segoe UI", 10))
        self.adm_prod_stock.set(25)
        self.adm_prod_stock.grid(row=5, column=1, sticky=tk.W, pady=6, padx=10)

        btn_add = tk.Button(
            f,
            text="➕ Save & Publish Product",
            font=("Segoe UI", 10, "bold"),
            bg=self.SUCCESS_COLOR,
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            command=self._handle_admin_add_product
        )
        btn_add.grid(row=6, column=1, sticky=tk.W, pady=(15, 0), padx=10)

    def _handle_admin_add_product(self):
        name = self.adm_prod_name.get().strip()
        sku = self.adm_prod_sku.get().strip().upper()
        cat_str = self.adm_prod_cat.get()
        cat_id = int(cat_str.split(" - ")[0])
        
        try:
            price = float(self.adm_prod_price.get().strip())
            stock = int(self.adm_prod_stock.get().strip())
            if price <= 0 or stock < 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Validation Error", "Price must be > 0 and stock must be >= 0.")
            return

        if not name or not sku:
            messagebox.showwarning("Validation Error", "Product Name and SKU are required.")
            return

        try:
            conn = get_db_connection(self.db_config, autocommit=False)
            cur = conn.cursor()

            # Insert Product
            cur.execute("""
                INSERT INTO PRODUCT (SKU, ProductName, UnitPrice, CategoryID)
                VALUES (%s, %s, %s, %s)
            """, (sku, name, price, cat_id))
            new_pid = cur.lastrowid

            # Initialize Inventory across all active warehouses
            cur.execute("SELECT WarehouseID FROM WAREHOUSE")
            wh_ids = [row[0] for row in cur.fetchall()]

            for wid in wh_ids:
                cur.execute("""
                    INSERT INTO PRODUCT_INVENTORY (ProductID, WarehouseID, StockQuantity, ReorderLevel)
                    VALUES (%s, %s, %s, 10)
                """, (new_pid, wid, stock))

            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Product Created", f"Successfully created Product #{new_pid}: '{name}'\nDistributed {stock} units across all warehouses.")
            self.adm_prod_name.delete(0, tk.END)
            self.adm_prod_sku.delete(0, tk.END)
            self.refresh_catalog()
            self.refresh_warehouse_monitor()
            self.refresh_admin_analytics()
            self._populate_product_dropdown()

        except Exception as e:
            messagebox.showerror("Insert Error", f"Could not create product:\n{str(e)}")

    def _build_add_category_form(self, parent):
        f = tk.Frame(parent, bg=self.CARD_BG, padx=25, pady=20)
        f.pack(fill=tk.BOTH, expand=True)

        tk.Label(f, text="Create New Category in CATEGORY Table", font=("Segoe UI", 10, "bold"), bg=self.CARD_BG, fg="#1F2937").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))

        tk.Label(f, text="Category Name *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=1, column=0, sticky=tk.W, pady=6)
        self.adm_cat_name = ttk.Entry(f, width=38, font=("Segoe UI", 10))
        self.adm_cat_name.grid(row=1, column=1, sticky=tk.W, pady=6, padx=10)

        tk.Label(f, text="Description", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=2, column=0, sticky=tk.W, pady=6)
        self.adm_cat_desc = ttk.Entry(f, width=48, font=("Segoe UI", 10))
        self.adm_cat_desc.grid(row=2, column=1, sticky=tk.W, pady=6, padx=10)

        btn_add = tk.Button(
            f,
            text="📁 Save Category",
            font=("Segoe UI", 10, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            command=self._handle_admin_add_category
        )
        btn_add.grid(row=3, column=1, sticky=tk.W, pady=(15, 0), padx=10)

    def _handle_admin_add_category(self):
        name = self.adm_cat_name.get().strip()
        desc = self.adm_cat_desc.get().strip()
        if not name:
            messagebox.showwarning("Validation Error", "Category Name is required.")
            return

        try:
            conn = get_db_connection(self.db_config, autocommit=True)
            cur = conn.cursor()
            cur.execute("INSERT INTO CATEGORY (CategoryName, Description) VALUES (%s, %s)", (name, desc))
            cur.close()
            conn.close()

            messagebox.showinfo("Success", f"Category '{name}' created successfully!")
            self.adm_cat_name.delete(0, tk.END)
            self.adm_cat_desc.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add category:\n{str(e)}")

    def _build_add_warehouse_form(self, parent):
        f = tk.Frame(parent, bg=self.CARD_BG, padx=25, pady=20)
        f.pack(fill=tk.BOTH, expand=True)

        tk.Label(f, text="Expand Fulfillment Network: Add New WAREHOUSE with Geodesic Coordinates", font=("Segoe UI", 10, "bold"), bg=self.CARD_BG, fg="#1F2937").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))

        tk.Label(f, text="Warehouse Name *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=1, column=0, sticky=tk.W, pady=6)
        self.adm_wh_name = ttk.Entry(f, width=38, font=("Segoe UI", 10))
        self.adm_wh_name.grid(row=1, column=1, sticky=tk.W, pady=6, padx=10)

        tk.Label(f, text="City *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=2, column=0, sticky=tk.W, pady=6)
        self.adm_wh_city = ttk.Entry(f, width=28, font=("Segoe UI", 10))
        self.adm_wh_city.grid(row=2, column=1, sticky=tk.W, pady=6, padx=10)

        tk.Label(f, text="State *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=3, column=0, sticky=tk.W, pady=6)
        self.adm_wh_state = ttk.Entry(f, width=28, font=("Segoe UI", 10))
        self.adm_wh_state.grid(row=3, column=1, sticky=tk.W, pady=6, padx=10)

        tk.Label(f, text="Latitude *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=4, column=0, sticky=tk.W, pady=6)
        self.adm_wh_lat = ttk.Entry(f, width=20, font=("Segoe UI", 10))
        self.adm_wh_lat.grid(row=4, column=1, sticky=tk.W, pady=6, padx=10)

        tk.Label(f, text="Longitude *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=5, column=0, sticky=tk.W, pady=6)
        self.adm_wh_lon = ttk.Entry(f, width=20, font=("Segoe UI", 10))
        self.adm_wh_lon.grid(row=5, column=1, sticky=tk.W, pady=6, padx=10)

        tk.Label(f, text="Capacity (units) *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=6, column=0, sticky=tk.W, pady=6)
        self.adm_wh_cap = ttk.Entry(f, width=20, font=("Segoe UI", 10))
        self.adm_wh_cap.insert(0, "50000")
        self.adm_wh_cap.grid(row=6, column=1, sticky=tk.W, pady=6, padx=10)

        btn_add = tk.Button(
            f,
            text="📍 Add Warehouse Facility",
            font=("Segoe UI", 10, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            command=self._handle_admin_add_warehouse
        )
        btn_add.grid(row=7, column=1, sticky=tk.W, pady=(15, 0), padx=10)

    def _handle_admin_add_warehouse(self):
        name = self.adm_wh_name.get().strip()
        city = self.adm_wh_city.get().strip()
        state = self.adm_wh_state.get().strip()

        try:
            lat = float(self.adm_wh_lat.get().strip())
            lon = float(self.adm_wh_lon.get().strip())
            cap = int(self.adm_wh_cap.get().strip())
            if cap <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Validation Error", "Valid numeric coordinates and positive capacity required.")
            return

        if not name or not city or not state:
            messagebox.showwarning("Validation Error", "Name, City, and State are required.")
            return

        try:
            conn = get_db_connection(self.db_config, autocommit=False)
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO WAREHOUSE (WarehouseName, City, State, Latitude, Longitude, Capacity)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, city, state, lat, lon, cap))
            new_wid = cur.lastrowid

            # Populate initial zero-inventory for all existing products
            cur.execute("SELECT ProductID FROM PRODUCT")
            pids = [row[0] for row in cur.fetchall()]

            for pid in pids:
                cur.execute("""
                    INSERT INTO PRODUCT_INVENTORY (ProductID, WarehouseID, StockQuantity, ReorderLevel)
                    VALUES (%s, %s, 15, 10)
                """, (pid, new_wid))

            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Warehouse Added", f"New fulfillment hub #{new_wid} ('{name}', {city}) added to routing network!")
            self.refresh_warehouse_monitor()
            self.refresh_admin_analytics()

        except Exception as e:
            messagebox.showerror("Error", f"Could not create warehouse:\n{str(e)}")

    def _build_admin_mailer_form(self, parent):
        f = tk.Frame(parent, bg=self.CARD_BG, padx=25, pady=20)
        f.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            f,
            text="Executive Operational Directives & Broadcast Dispatcher (SMTP)",
            font=("Segoe UI", 11, "bold"),
            bg=self.CARD_BG,
            fg="#1E3A8A"
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 4))

        tk.Label(
            f,
            text="Dispatch real-time directives, urgent restock alerts, or operational notices directly to hub managers.",
            font=("Segoe UI", 9),
            bg=self.CARD_BG,
            fg="#4B5563"
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 12))

        tk.Label(f, text="Recipient Hub Manager *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=2, column=0, sticky=tk.W, pady=6)
        self.adm_mail_recipient = ttk.Combobox(
            f,
            values=[
                "Broadcast to All Hub Managers",
                "Chennai Hub (#1) - Samarth (samarth@gmail.com)",
                "Bengaluru Hub (#2) - Manager (manager.bengaluru@nexus.local)",
                "Mumbai Hub (#3) - Manager (manager.mumbai@nexus.local)"
            ],
            state="readonly",
            width=50,
            font=("Segoe UI", 9)
        )
        self.adm_mail_recipient.current(0)
        self.adm_mail_recipient.grid(row=2, column=1, sticky=tk.W, pady=6, padx=10)

        tk.Label(f, text="Directive Category *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=3, column=0, sticky=tk.W, pady=6)
        self.adm_mail_category = ttk.Combobox(
            f,
            values=[
                "Operational Directive",
                "Urgent Restock Warning",
                "Pre-Dispatch Inventory Audit",
                "Holiday Fulfillment Protocol",
                "Platform Maintenance Notice"
            ],
            state="readonly",
            width=50,
            font=("Segoe UI", 9)
        )
        self.adm_mail_category.current(0)
        self.adm_mail_category.grid(row=3, column=1, sticky=tk.W, pady=6, padx=10)

        tk.Label(f, text="Subject Line *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=4, column=0, sticky=tk.W, pady=6)
        self.adm_mail_subject = ttk.Entry(f, width=52, font=("Segoe UI", 9))
        self.adm_mail_subject.insert(0, "Mandatory Pre-Dispatch Hardware Quality Check")
        self.adm_mail_subject.grid(row=4, column=1, sticky=tk.W, pady=6, padx=10)

        tk.Label(f, text="Message Body *", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=5, column=0, sticky=tk.NW, pady=6)
        self.adm_mail_body = tk.Text(f, width=52, height=6, font=("Segoe UI", 9), relief=tk.SOLID, bd=1)
        self.adm_mail_body.insert(
            tk.END,
            "Please ensure all outgoing keyboard kits and switches are thoroughly inspected, packed with anti-static bubble wrap, and marked as IN_TRANSIT immediately upon carrier handover."
        )
        self.adm_mail_body.grid(row=5, column=1, sticky=tk.W, pady=6, padx=10)

        self.lbl_mail_status = tk.Label(f, text="", font=("Segoe UI", 9), bg=self.CARD_BG, fg="#059669")
        self.lbl_mail_status.grid(row=6, column=1, sticky=tk.W, pady=4, padx=10)

        btn_send_directive = tk.Button(
            f,
            text="🚀 Dispatch Directive Email via SMTP",
            font=("Segoe UI", 9, "bold"),
            bg="#1E3A8A",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=14,
            pady=8,
            command=self._handle_send_admin_directive
        )
        btn_send_directive.grid(row=7, column=1, sticky=tk.W, pady=(8, 0), padx=10)

    def _handle_send_admin_directive(self):
        target = self.adm_mail_recipient.get()
        category = self.adm_mail_category.get()
        subject_raw = self.adm_mail_subject.get().strip()
        body = self.adm_mail_body.get("1.0", tk.END).strip()

        if not subject_raw or not body:
            messagebox.showwarning("Incomplete Form", "Please provide both a Subject Line and Message Body.")
            return

        subject = f"[{category.upper()}] {subject_raw}"
        admin_name = self.current_user.get("FullName", "System Administrator") if self.current_user else "System Administrator"

        targets = []
        if "All Hub Managers" in target:
            try:
                conn = get_db_connection(self.db_config)
                cur = conn.cursor(dictionary=True)
                cur.execute("""
                    SELECT su.FullName, su.Email, w.WarehouseName 
                    FROM STAFF_USER su 
                    LEFT JOIN WAREHOUSE w ON su.AssignedWarehouseID = w.WarehouseID 
                    WHERE su.Role = 'WAREHOUSE_MANAGER'
                """)
                rows = cur.fetchall()
                cur.close()
                conn.close()
                for r in rows:
                    if r.get("Email"):
                        targets.append((r["Email"], r.get("FullName", "Hub Manager"), r.get("WarehouseName", "Network Hub")))
            except Exception as e:
                messagebox.showerror("Database Error", f"Could not fetch hub managers:\n{str(e)}")
                return
        else:
            email = target.split("(")[-1].replace(")", "").strip()
            name = target.split(" - ")[1].split("(")[0].strip() if " - " in target else "Hub Manager"
            hub = target.split(" - ")[0].strip() if " - " in target else None
            targets.append((email, name, hub))

        if not targets:
            messagebox.showinfo("No Recipients", "No active warehouse manager email targets found.")
            return

        for email, name, hub in targets:
            notify_admin_directive_to_manager(
                sender_admin_name=admin_name,
                recipient_email=email,
                recipient_name=name,
                subject_line=subject,
                directive_body=body,
                warehouse_name=hub
            )

        self.lbl_mail_status.config(text=f"✓ Directive successfully dispatched to {len(targets)} manager(s) via SMTP!", fg="#059669")
        messagebox.showinfo("Directive Dispatched", f"Executive Directive successfully dispatched to {len(targets)} recipient(s):\n" + "\n".join([f"• {t[1]} ({t[0]})" for t in targets]))

    def _open_mailer_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Nexus Peripherals — SMTP Notification Engine & Outbox Manifest")
        dialog.geometry("740, 560")
        dialog.transient(self)
        dialog.grab_set()

        frame = tk.Frame(dialog, padx=16, pady=12, bg="#F9FAFB")
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="✉ SMTP Mailer Configuration & Live Outbox Telemetry", font=("Segoe UI", 12, "bold"), bg="#F9FAFB", fg="#1E3A8A").pack(anchor=tk.W, pady=(0, 6))

        cfg = get_smtp_config()

        # Config Frame
        cfg_frame = tk.LabelFrame(frame, text=" SMTP Server Settings ", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", padx=12, pady=8)
        cfg_frame.pack(fill=tk.X, pady=(0, 10))

        row1 = tk.Frame(cfg_frame, bg="#FFFFFF")
        row1.pack(fill=tk.X, pady=3)
        tk.Label(row1, text="SMTP Host:", width=12, anchor=tk.W, font=("Segoe UI", 8, "bold"), bg="#FFFFFF").pack(side=tk.LEFT)
        e_host = ttk.Entry(row1, width=22)
        e_host.insert(0, cfg.get("smtp_host", "smtp.gmail.com"))
        e_host.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(row1, text="Port:", width=6, anchor=tk.W, font=("Segoe UI", 8, "bold"), bg="#FFFFFF").pack(side=tk.LEFT)
        e_port = ttk.Entry(row1, width=8)
        e_port.insert(0, str(cfg.get("smtp_port", 587)))
        e_port.pack(side=tk.LEFT)

        row2 = tk.Frame(cfg_frame, bg="#FFFFFF")
        row2.pack(fill=tk.X, pady=3)
        tk.Label(row2, text="Sender User:", width=12, anchor=tk.W, font=("Segoe UI", 8, "bold"), bg="#FFFFFF").pack(side=tk.LEFT)
        e_user = ttk.Entry(row2, width=32)
        e_user.insert(0, cfg.get("smtp_user", "notifications.nexusperipherals@gmail.com"))
        e_user.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(row2, text="Password:", width=10, anchor=tk.W, font=("Segoe UI", 8, "bold"), bg="#FFFFFF").pack(side=tk.LEFT)
        e_pass = ttk.Entry(row2, width=16, show="•")
        e_pass.insert(0, cfg.get("smtp_password", ""))
        e_pass.pack(side=tk.LEFT)

        var_sim = tk.BooleanVar(value=cfg.get("simulate_mode", True))
        chk_sim = ttk.Checkbutton(cfg_frame, text="Enable Sandbox / Simulation Mode (Safely logs outgoing dispatches without live internet SMTP)", variable=var_sim)
        chk_sim.pack(anchor=tk.W, pady=(6, 4))

        def save_cfg():
            update_smtp_config({
                "smtp_host": e_host.get().strip(),
                "smtp_port": int(e_port.get().strip() or "587"),
                "smtp_user": e_user.get().strip(),
                "smtp_password": e_pass.get(),
                "simulate_mode": var_sim.get()
            })
            messagebox.showinfo("Settings Saved", "SMTP Notification engine configuration updated!")

        def test_mail():
            save_cfg()
            recipient = self.current_user.get("Email") if self.current_user else "test.receiver@nexus.local"
            notify_customer_order_placed(
                customer_email=recipient,
                customer_name="Test Customer",
                order_id=777,
                total_amount=16999.00,
                items=[{"product_name": "Keychron Q1 Pro (Test)", "quantity": 1, "unit_price": 16999.00, "subtotal": 16999.00}],
                shipping_address="Test Delivery Lane, Chennai",
                warehouse_name="South Fulfillment Hub",
                tracking_number="TRK-TEST-777"
            )
            refresh_outbox()
            messagebox.showinfo("Test Dispatched", f"Test notification dispatched to '{recipient}'!\nCheck the Outbox manifest table below.")

        btn_row = tk.Frame(cfg_frame, bg="#FFFFFF")
        btn_row.pack(fill=tk.X, pady=(4, 0))
        tk.Button(btn_row, text="💾 Save SMTP Settings", font=("Segoe UI", 8, "bold"), bg="#2563EB", fg="#FFFFFF", padx=8, pady=3, command=save_cfg).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(btn_row, text="🧪 Dispatch Test Email", font=("Segoe UI", 8, "bold"), bg="#059669", fg="#FFFFFF", padx=8, pady=3, command=test_mail).pack(side=tk.LEFT)

        # Outbox Manifest Section
        outbox_frame = tk.LabelFrame(frame, text=" Live Email Notification Outbox Manifest ", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", padx=10, pady=8)
        outbox_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("Timestamp", "Type", "Recipient", "Subject", "Status")
        tree_outbox = ttk.Treeview(outbox_frame, columns=cols, show="headings", height=8)
        tree_outbox.heading("Timestamp", text="Timestamp")
        tree_outbox.heading("Type", text="Type")
        tree_outbox.heading("Recipient", text="Recipient")
        tree_outbox.heading("Subject", text="Subject")
        tree_outbox.heading("Status", text="Status")

        tree_outbox.column("Timestamp", width=130, anchor=tk.CENTER)
        tree_outbox.column("Type", width=150, anchor=tk.CENTER)
        tree_outbox.column("Recipient", width=160, anchor=tk.W)
        tree_outbox.column("Subject", width=220, anchor=tk.W)
        tree_outbox.column("Status", width=140, anchor=tk.CENTER)

        tree_outbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(outbox_frame, orient=tk.VERTICAL, command=tree_outbox.yview)
        tree_outbox.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.LEFT, fill=tk.Y)

        def refresh_outbox():
            for item in tree_outbox.get_children():
                tree_outbox.delete(item)
            for entry in get_outbox_history():
                tree_outbox.insert("", tk.END, values=(
                    entry.get("timestamp", ""),
                    entry.get("type", ""),
                    entry.get("to", ""),
                    entry.get("subject", ""),
                    entry.get("status", "")
                ))

        refresh_outbox()
        tk.Button(frame, text="🔄 Refresh Outbox Manifest", font=("Segoe UI", 8), bg="#E5E7EB", padx=8, pady=3, command=refresh_outbox).pack(anchor=tk.E, pady=(6, 0))

    # -------------------------------------------------------------------------
    # TAB 8: EXPLORATORY DATA ANALYSIS (EDA) & MONTHLY PDF REPORTS
    # -------------------------------------------------------------------------
    def _build_eda_tab(self):
        container = tk.Frame(self.tab_eda, bg=self.BG_MAIN)
        container.pack(fill=tk.BOTH, expand=True, padx=16, pady=10)

        # 1. Top Controls Bar: Scope & Month Selection + Actions
        ctrl_card = tk.LabelFrame(
            container,
            text=" Exploratory Data Analysis & Audit Report Filters ",
            font=("Segoe UI", 10, "bold"),
            bg=self.CARD_BG,
            padx=12,
            pady=8
        )
        ctrl_card.pack(fill=tk.X, pady=(0, 8))

        # Warehouse scope
        tk.Label(ctrl_card, text="Fulfillment Hub Scope:", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).pack(side=tk.LEFT, padx=(4, 6))
        self.combo_eda_wh = ttk.Combobox(
            ctrl_card,
            values=["Global Network (All Hubs)", "Chennai Hub (#1)", "Bengaluru Hub (#2)", "Mumbai Hub (#3)"],
            state="readonly",
            width=24,
            font=("Segoe UI", 9)
        )
        self.combo_eda_wh.set("Global Network (All Hubs)")
        self.combo_eda_wh.pack(side=tk.LEFT, padx=(0, 14))
        self.combo_eda_wh.bind("<<ComboboxSelected>>", self._on_eda_filter_changed)

        # Month selector
        tk.Label(ctrl_card, text="Target Month:", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).pack(side=tk.LEFT, padx=(4, 6))
        self.combo_eda_month = ttk.Combobox(
            ctrl_card,
            values=["All Months (Annual Multi-Month Trend)"],
            state="readonly",
            width=24,
            font=("Segoe UI", 9)
        )
        self.combo_eda_month.set("All Months (Annual Multi-Month Trend)")
        self.combo_eda_month.pack(side=tk.LEFT, padx=(0, 14))
        self.combo_eda_month.bind("<<ComboboxSelected>>", self._on_eda_filter_changed)

        # Action Buttons
        btn_refresh_eda = tk.Button(
            ctrl_card,
            text="🔄 Refresh Analytics",
            font=("Segoe UI", 9, "bold"),
            bg="#374151",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            command=self.refresh_eda_view
        )
        btn_refresh_eda.pack(side=tk.LEFT, padx=6)

        btn_pdf = tk.Button(
            ctrl_card,
            text="📄 Download Monthly PDF Report",
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            command=self._download_eda_pdf
        )
        btn_pdf.pack(side=tk.RIGHT, padx=4)

        # 2. Executive KPI Cards Row
        kpi_frame = tk.Frame(container, bg=self.BG_MAIN)
        kpi_frame.pack(fill=tk.X, pady=(0, 8))

        self.eda_kpi_cards = {}
        kpi_specs = [
            ("total_sales", "Total Revenue (Sales)", "₹0.00", "#059669"),
            ("total_orders", "Orders Fulfilled", "0 orders", "#2563EB"),
            ("total_intake", "Restock Intake Volume", "0 units", "#7C3AED"),
            ("aov", "Average Order Value", "₹0.00", "#D97706"),
        ]

        for i, (key, title, default_val, clr) in enumerate(kpi_specs):
            card = tk.Frame(kpi_frame, bg=self.CARD_BG, bd=1, relief=tk.SOLID, padx=10, pady=6)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if i == 0 else 6, 0))
            tk.Label(card, text=title, font=("Segoe UI", 8, "bold"), bg=self.CARD_BG, fg="#6B7280").pack(anchor=tk.W)
            lbl_val = tk.Label(card, text=default_val, font=("Segoe UI", 12, "bold"), bg=self.CARD_BG, fg=clr)
            lbl_val.pack(anchor=tk.W, pady=(2, 0))
            self.eda_kpi_cards[key] = lbl_val

        # 3. Embedded Matplotlib Visual Analytics Frame
        chart_container = tk.Frame(container, bg="#FFFFFF", bd=1, relief=tk.SOLID)
        chart_container.pack(fill=tk.BOTH, expand=True)

        self.eda_fig = Figure(figsize=(10.5, 4.8), dpi=95, facecolor="#FFFFFF")
        self.eda_canvas = FigureCanvasTkAgg(self.eda_fig, master=chart_container)
        self.eda_canvas_widget = self.eda_canvas.get_tk_widget()
        self.eda_canvas_widget.pack(fill=tk.BOTH, expand=True)

    def _get_selected_eda_scope(self):
        wh_text = self.combo_eda_wh.get()
        if "Chennai" in wh_text or "(#1)" in wh_text:
            wid = 1
        elif "Bengaluru" in wh_text or "(#2)" in wh_text:
            wid = 2
        elif "Mumbai" in wh_text or "(#3)" in wh_text:
            wid = 3
        else:
            wid = None

        m_text = self.combo_eda_month.get()
        if "All Months" in m_text or not m_text:
            month = "ALL"
        else:
            month = m_text.split(" ")[0].strip()

        return wid, month

    def _on_eda_filter_changed(self, event=None):
        wid, month = self._get_selected_eda_scope()
        self._render_eda_view(wid, month)

    def refresh_eda_view(self):
        if not hasattr(self, "combo_eda_wh") or not self.combo_eda_wh.winfo_exists():
            return

        # Configure warehouse scope availability based on current role
        if self.current_role == "WAREHOUSE_MANAGER":
            assigned_wid = self.current_user.get("AssignedWarehouseID") if self.current_user else 1
            hub_mapping = {1: "Chennai Hub (#1)", 2: "Bengaluru Hub (#2)", 3: "Mumbai Hub (#3)"}
            hub_name = hub_mapping.get(assigned_wid, f"Hub #{assigned_wid}")
            self.combo_eda_wh.config(values=[hub_name], state="disabled")
            self.combo_eda_wh.set(hub_name)
            wid = assigned_wid
        else:
            self.combo_eda_wh.config(
                values=["Global Network (All Hubs)", "Chennai Hub (#1)", "Bengaluru Hub (#2)", "Mumbai Hub (#3)"],
                state="readonly"
            )
            wid, _ = self._get_selected_eda_scope()

        # Update available months
        available_months = get_available_months(wid)
        month_vals = ["All Months (Annual Multi-Month Trend)"] + available_months
        current_m = self.combo_eda_month.get()
        self.combo_eda_month.config(values=month_vals)
        if current_m in month_vals:
            self.combo_eda_month.set(current_m)
        else:
            self.combo_eda_month.set("All Months (Annual Multi-Month Trend)")

        wid, month = self._get_selected_eda_scope()
        self._render_eda_view(wid, month)

    def _render_eda_view(self, warehouse_id, month):
        try:
            # 1. Update KPI Cards
            kpis = get_eda_kpis(warehouse_id, month)
            self.eda_kpi_cards["total_sales"].config(text=f"₹{kpis['total_sales']:,.2f}")
            self.eda_kpi_cards["total_orders"].config(text=f"{kpis['total_orders']:,} orders")
            self.eda_kpi_cards["total_intake"].config(text=f"{kpis['total_intake']:,} units")
            self.eda_kpi_cards["aov"].config(text=f"₹{kpis['aov']:,.2f}")

            # 2. Render Charts on Matplotlib Canvas
            self.eda_fig.clear()
            import matplotlib.gridspec as gridspec
            import matplotlib.ticker as ticker
            gs = gridspec.GridSpec(2, 2, figure=self.eda_fig, width_ratios=[1.3, 1.0], height_ratios=[1, 1],
                                   left=0.08, right=0.95, top=0.90, bottom=0.14, wspace=0.28, hspace=0.48)

            ax1 = self.eda_fig.add_subplot(gs[:, 0])
            ax2 = self.eda_fig.add_subplot(gs[0, 1])
            ax3 = self.eda_fig.add_subplot(gs[1, 1])

            # Plot 1: Monthly Operations (Sales Revenue vs Intake vs Order Count)
            trends = get_monthly_trend_data(warehouse_id)
            if trends:
                x_labels = [t["month"] for t in trends]
                sales_k = [t["sales"] / 1000.0 for t in trends]
                intakes = [t["intake"] for t in trends]
                orders = [t["orders"] for t in trends]

                x = np.arange(len(x_labels))
                w = 0.35

                ax1.bar(x - w/2, sales_k, w, label="Sales (₹ in Thousands)", color="#3B82F6", alpha=0.85)
                ax1.bar(x + w/2, intakes, w, label="Intake Restock (Units)", color="#10B981", alpha=0.85)
                ax1.set_xticks(x)
                ax1.set_xticklabels(x_labels, fontsize=8)
                ax1.set_ylabel("Revenue (₹ Thousands) / Units", fontsize=8.5, color="#374151")
                ax1.set_title("Monthly Operations Trend (Sales vs Restock Intake)", fontsize=9.5, weight="bold", color="#1F2937", pad=8)
                ax1.grid(axis="y", linestyle="--", alpha=0.35)

                ax1_twin = ax1.twinx()
                ax1_twin.plot(x, orders, color="#DC2626", marker="o", linewidth=2, label="Order Count")
                ax1_twin.set_ylabel("Order Count", fontsize=8.5, color="#DC2626")
                ax1_twin.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

                h1, l1 = ax1.get_legend_handles_labels()
                h2, l2 = ax1_twin.get_legend_handles_labels()
                ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=7.5, framealpha=0.9)
            else:
                ax1.text(0.5, 0.5, "No multi-month historical data recorded", ha="center", va="center")

            # Plot 2: Category Revenue Distribution (Pie Chart)
            categories = get_category_distribution(warehouse_id, month)
            if categories and sum(c["revenue"] for c in categories) > 0:
                cat_labels = [c["category"] for c in categories]
                cat_revs = [c["revenue"] for c in categories]
                palette = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899"]
                wedges, texts, autotexts = ax2.pie(
                    cat_revs,
                    labels=None,
                    autopct="%1.1f%%",
                    startangle=140,
                    colors=palette[:len(cat_revs)],
                    pctdistance=0.75,
                    textprops=dict(color="#FFFFFF", weight="bold", fontsize=7)
                )
                ax2.set_title("Category Revenue Share", fontsize=9, weight="bold", color="#1F2937", pad=6)
                ax2.legend(wedges, cat_labels, loc="lower center", bbox_to_anchor=(0.5, -0.32), fontsize=6.5, frameon=False)
            else:
                ax2.text(0.5, 0.5, "No category sales recorded", ha="center", va="center", fontsize=8)
                ax2.axis("off")

            # Plot 3: Top Selling Products (Horizontal Bar Chart)
            top_prods = get_top_selling_products(warehouse_id, month, limit=4)
            if top_prods:
                names = [p["product_name"][:16] + ".." if len(p["product_name"]) > 16 else p["product_name"] for p in top_prods]
                revs = [p["revenue"] / 1000.0 for p in top_prods]
                y_indices = range(len(names))
                ax3.barh(y_indices, revs, color="#6366F1", alpha=0.85)
                ax3.set_yticks(y_indices)
                ax3.set_yticklabels(names, fontsize=7)
                ax3.invert_yaxis()
                ax3.set_xlabel("Revenue (₹ Thousands)", fontsize=7.5)
                ax3.set_title("Top Selling Products", fontsize=9, weight="bold", color="#1F2937", pad=6)
                ax3.grid(axis="x", linestyle="--", alpha=0.35)
            else:
                ax3.text(0.5, 0.5, "No product sales recorded", ha="center", va="center", fontsize=8)
                ax3.axis("off")

            self.eda_canvas.draw()
        except Exception as e:
            self.set_status(f"Error rendering EDA analytics: {str(e)}", is_error=True)

    def _download_eda_pdf(self):
        wid, month = self._get_selected_eda_scope()
        hub_tag = f"Hub_{wid}" if wid else "Global_Network"
        month_tag = month.replace("-", "_") if month != "ALL" else "All_Time"
        default_filename = f"Nexus_Peripherals_Audit_Report_{month_tag}_{hub_tag}.pdf"

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Monthly Operations & Financial Audit Report PDF",
            initialfile=default_filename,
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        staff_name = self.current_user.get("FullName", "Authorized Staff") if self.current_user else "Authorized Staff"
        staff_role = self.current_role.replace("_", " ").title() if self.current_role else "Staff"

        ok, msg = generate_monthly_pdf_report(
            output_path=file_path,
            warehouse_id=wid,
            month=month,
            staff_name=staff_name,
            staff_role=staff_role
        )

        if ok:
            open_now = messagebox.askyesno(
                "PDF Report Generated",
                f"Audit Report PDF generated successfully!\n\nFile saved to:\n{file_path}\n\nWould you like to open it now?"
            )
            if open_now:
                try:
                    os.startfile(file_path)
                except Exception:
                    pass
        else:
            messagebox.showerror("Export Failed", f"Could not generate PDF report:\n{msg}")

    # -------------------------------------------------------------------------
    # DB SETTINGS & INITIALIZATION
    # -------------------------------------------------------------------------
    def _initial_db_check(self):
        ok, msg = test_connection(self.db_config)
        if ok:
            self.set_status(f"MySQL Connected: {msg}")
            self.refresh_catalog()
            self.refresh_warehouse_monitor()
            self._populate_product_dropdown()
        else:
            self.set_status(f"Database Connection Notice: {msg}", is_error=True)

    def _open_db_settings_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("MySQL Database Connection Settings")
        dialog.geometry("480, 420")
        dialog.transient(self)
        dialog.grab_set()

        frame = tk.Frame(dialog, padx=20, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Configure MySQL 8.0 Connection", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))

        fields = [
            ("Host:", "host", self.db_config.get("host", "localhost")),
            ("Port:", "port", str(self.db_config.get("port", 3306))),
            ("User:", "user", self.db_config.get("user", "root")),
            ("Password:", "password", self.db_config.get("password", "")),
            ("Database:", "database", self.db_config.get("database", "nexus_peripherals")),
        ]

        entries = {}
        for label_text, key, val in fields:
            f_row = tk.Frame(frame)
            f_row.pack(fill=tk.X, pady=4)
            tk.Label(f_row, text=label_text, width=12, anchor=tk.W, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
            entry = ttk.Entry(f_row, width=28)
            entry.insert(0, val)
            if key == "password":
                entry.config(show="•")
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            entries[key] = entry

        lbl_test_result = tk.Label(frame, text="", font=("Segoe UI", 8), wraplength=420, justify=tk.LEFT)
        lbl_test_result.pack(fill=tk.X, pady=(10, 5))

        def test_conn():
            temp_config = {
                "host": entries["host"].get().strip(),
                "port": int(entries["port"].get().strip() or "3306"),
                "user": entries["user"].get().strip(),
                "password": entries["password"].get(),
                "database": entries["database"].get().strip(),
            }
            ok, msg = test_connection(temp_config)
            if ok:
                lbl_test_result.config(text=f"✓ {msg}", fg="#059669")
            else:
                lbl_test_result.config(text=f"✗ {msg}", fg="#DC2626")

        def save_conn():
            self.db_config["host"] = entries["host"].get().strip()
            self.db_config["port"] = int(entries["port"].get().strip() or "3306")
            self.db_config["user"] = entries["user"].get().strip()
            self.db_config["password"] = entries["password"].get()
            self.db_config["database"] = entries["database"].get().strip()

            test_conn()
            self.refresh_catalog()
            self.refresh_warehouse_monitor()
            self._populate_product_dropdown()
            messagebox.showinfo("Saved", "Database configuration updated.")
            dialog.destroy()

        def run_schema_init():
            confirm = messagebox.askyesno(
                "Reset & Initialize Schema",
                "This will execute 01_schema.sql, 02_seed_data.sql, and 03_procedures_views.sql.\n\n"
                "All existing tables will be cleanly recreated and re-seeded. Proceed?"
            )
            if not confirm:
                return

            sql_dir = os.path.join(parent_dir, "db")
            if not os.path.exists(sql_dir):
                sql_dir = os.path.join(parent_dir, "sql")
            temp_config = {
                "host": entries["host"].get().strip(),
                "port": int(entries["port"].get().strip() or "3306"),
                "user": entries["user"].get().strip(),
                "password": entries["password"].get(),
                "database": entries["database"].get().strip(),
            }

            ok, msg = initialize_schema_and_seed(sql_dir, custom_config=temp_config)
            if ok:
                lbl_test_result.config(text=f"✓ {msg}", fg="#059669")
                save_conn()
            else:
                lbl_test_result.config(text=f"✗ {msg}", fg="#DC2626")

        btn_box = tk.Frame(frame)
        btn_box.pack(fill=tk.X, pady=(15, 0))

        tk.Button(btn_box, text="Test Connection", command=test_conn, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(btn_box, text="Initialize / Reset DB", command=run_schema_init, bg="#DC2626", fg="#FFFFFF", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_box, text="Save & Close", command=save_conn, bg="#2563EB", fg="#FFFFFF", font=("Segoe UI", 9, "bold")).pack(side=tk.RIGHT)


if __name__ == "__main__":
    app = NexusPeripheralsApp()
    app.mainloop()
