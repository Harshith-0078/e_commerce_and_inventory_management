/**
 * NEXUS PERIPHERALS — MODERN WEB FRONTEND ENGINE
 * Multi-Warehouse Inventory & Proximity Routing Application
 * BACSE202 Database Systems Final Project
 * 
 * Features:
 * 1. RBAC Portals (Customer, Hub Manager, System Administrator)
 * 2. Haversine Geodesic Proximity Routing & Candidate Warehouse Evaluation
 * 3. Shopping Cart & Simulated Atomic ACID MySQL Commit
 * 4. Hub Manager Bin Matrix & Kanban Dispatch Pipeline
 * 5. Exploratory Data Analysis (EDA) Interactive Canvas Charts
 * 6. Admin SMTP Directive Mailer & Outbox Telemetry Log
 */

// ============================================================================
// DATA REPOSITORY (Synchronized with 01_schema.sql & 02_seed_data.sql)
// ============================================================================

const WAREHOUSES = [
  { id: 1, name: "South Fulfillment Hub", city: "Chennai", lat: 13.0827, lon: 80.2707, state: "Tamil Nadu", manager: "Samarth (samarth@gmail.com)" },
  { id: 2, name: "Tech Corridor Warehouse", city: "Bengaluru", lat: 12.9716, lon: 77.5946, state: "Karnataka", manager: "manager_bengaluru" },
  { id: 3, name: "West Distribution Center", city: "Mumbai", lat: 19.0760, lon: 72.8777, state: "Maharashtra", manager: "manager_mumbai" }
];

const CITIES = {
  "Vellore": { lat: 12.9165, lon: 79.1325 },
  "Bengaluru": { lat: 12.9716, lon: 77.5946 },
  "Chennai": { lat: 13.0827, lon: 80.2707 },
  "Mumbai": { lat: 19.0760, lon: 72.8777 },
  "Hyderabad": { lat: 17.3850, lon: 78.4867 },
  "Delhi": { lat: 28.7041, lon: 77.1025 },
  "Coimbatore": { lat: 11.0168, lon: 76.9558 }
};

const PRODUCTS = [
  {
    id: 1,
    sku: "KB-KEY-Q1B-01",
    name: "Keychron Q1 Barebone Custom Keyboard",
    category_id: 1,
    category_name: "Mechanical Keyboards",
    price: 14999.00,
    desc: "CNC Machined Aluminum 75% Layout, QMK/VIA Custom Programmable, Gasket Mount Design.",
    image: "images/keychron_q1.jpg",
    inventory: { 1: 4, 2: 18, 3: 12 }, // wh_id: stock
    reorder_level: 5
  },
  {
    id: 2,
    sku: "KB-GLO-GMM-02",
    name: "Glorious GMMK Pro 75% White Ice",
    category_id: 1,
    category_name: "Mechanical Keyboards",
    price: 16499.00,
    desc: "Rotary Encoder Knob, South-Facing RGB LEDs, Factory Aluminum Top Plate.",
    image: "images/gmmk_pro.jpg",
    inventory: { 1: 8, 2: 14, 3: 6 },
    reorder_level: 5
  },
  {
    id: 3,
    sku: "SW-GAT-OIL-70",
    name: "Gateron Oil King Linear Switches (Pack of 70)",
    category_id: 2,
    category_name: "Switches",
    price: 2899.00,
    desc: "Factory pre-lubed, 55g actuation force, nylon PA66 upper housing with black INX base.",
    image: "images/gateron_oil_king.jpg",
    inventory: { 1: 2, 2: 25, 3: 15 },
    reorder_level: 6
  },
  {
    id: 4,
    sku: "SW-ZEP-LIN-70",
    name: "Zephyr Linear Switches (Pack of 70)",
    category_id: 2,
    category_name: "Switches",
    price: 3100.00,
    desc: "Smooth linear operation, POM stem, 62g bottom-out gold-plated spring.",
    image: "images/zephyr_linear.jpg",
    inventory: { 1: 15, 2: 30, 3: 20 },
    reorder_level: 5
  },
  {
    id: 5,
    sku: "SW-AKK-CSM-45",
    name: "Akko CS Matcha Green Switches (Pack of 45)",
    category_id: 2,
    category_name: "Switches",
    price: 1299.00,
    desc: "50g actuation, progressive spring, dustproof stem design for gaming & typing.",
    image: "images/akko_matcha.jpg",
    inventory: { 1: 20, 2: 40, 3: 18 },
    reorder_level: 8
  },
  {
    id: 6,
    sku: "KC-BOT-FOR-PBT",
    name: "Botanical Forest Cherry Profile PBT Keycaps",
    category_id: 3,
    category_name: "Keycaps",
    price: 3499.00,
    desc: "Dye-sublimated 142-key set, thick 1.5mm PBT plastic, sage green colorway.",
    image: "images/botanical_keycaps.jpg",
    inventory: { 1: 12, 2: 22, 3: 10 },
    reorder_level: 4
  },
  {
    id: 7,
    sku: "KC-SHI-80S-RET",
    name: "Shiba 80s Retro Keycap Set",
    category_id: 3,
    category_name: "Keycaps",
    price: 2999.00,
    desc: "OEM profile, dual-tone beige and cream aesthetic with novelty artisan accents.",
    image: "images/shiba_keycaps.svg",
    inventory: { 1: 6, 2: 12, 3: 15 },
    reorder_level: 4
  },
  {
    id: 8,
    sku: "LU-KRY-205-05",
    name: "Krytox 205g0 Mechanical Switch Lubricant (5g)",
    category_id: 4,
    category_name: "Lube & Accessories",
    price: 549.00,
    desc: "Genuine Chemours Krytox lubricant for linear switch stems, sliders, and stabilizers.",
    image: "images/krytox_lube.svg",
    inventory: { 1: 35, 2: 60, 3: 40 },
    reorder_level: 10
  },
  {
    id: 9,
    sku: "TL-ALU-SWP-01",
    name: "Precision Aluminum Switch & Keycap Puller",
    category_id: 4,
    category_name: "Lube & Accessories",
    price: 499.00,
    desc: "Ergonomic anodized metal body, zero PCB scratch risk, double-ended.",
    image: "images/switch_puller.svg",
    inventory: { 1: 25, 2: 50, 3: 30 },
    reorder_level: 10
  },
  {
    id: 10,
    sku: "AC-COI-USB-CBL",
    name: "Nexus Custom Coiled Aviator USB-C Cable",
    category_id: 4,
    category_name: "Lube & Accessories",
    price: 1899.00,
    desc: "GX16 5-pin detachable aviator connector, double-sleeved Paracord + Techflex.",
    image: "images/coiled_cable.svg",
    inventory: { 1: 14, 2: 28, 3: 16 },
    reorder_level: 5
  }
];

let SHIPMENTS = [
  { id: 1001, tracking: "TRK-NX-4F91280A", order_id: 8401, customer: "Aarav Mehta", city: "Bengaluru", items: 2, status: "PREPARING", hub_id: 2 },
  { id: 1002, tracking: "TRK-NX-B723149C", order_id: 8402, customer: "Pooja Reddy", city: "Chennai", items: 1, status: "IN_TRANSIT", hub_id: 1 },
  { id: 1003, tracking: "TRK-NX-C910482D", order_id: 8403, customer: "Karan Johar", city: "Mumbai", items: 3, status: "OUT_FOR_DELIVERY", hub_id: 3 },
  { id: 1004, tracking: "TRK-NX-D849102E", order_id: 8400, customer: "Rohan Sharma", city: "Vellore", items: 2, status: "DELIVERED", hub_id: 2 }
];

let OUTBOX_LOGS = [
  { timestamp: "2026-10-07 10:14:02", type: "CUSTOMER_ORDER_PLACED", to: "rohan@gmail.com", subject: "Order #8400 Confirmed [Nexus Peripherals]", status: "DELIVERED" },
  { timestamp: "2026-10-07 10:14:03", type: "HUB_NEW_ORDER_ALERT", to: "samarth@gmail.com", subject: "ACTION REQUIRED: New Order #8400 Routed to Hub #1", status: "DELIVERED" },
  { timestamp: "2026-10-07 10:14:04", type: "HUB_LOW_STOCK_WARNING", to: "samarth@gmail.com", subject: "WARNING: Low Stock Threshold Reached at Hub #1 (SW-GAT-OIL-70)", status: "DELIVERED" },
  { timestamp: "2026-10-07 09:30:15", type: "ADMIN_DIRECTIVE", to: "samarth@gmail.com", subject: "[ADMIN DIRECTIVE] Annual Inventory Audit Schedule", status: "DELIVERED" }
];

// Active State
let currentPortal = "customer";
let activeRole = "CUSTOMER";
let currentCustomerCity = "Vellore";
let currentCategoryFilter = "ALL";
let shoppingCart = []; // array of { product_id, quantity }
let optimalHub = null;

// ============================================================================
// HAVERSINE GEODESIC PROXIMITY ENGINE
// ============================================================================

function calculateHaversineDistance(lat1, lon1, lat2, lon2) {
  const R = 6371.0; // Earth's mean radius in km
  const toRad = deg => (deg * Math.PI) / 180.0;
  
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function evaluateCandidateHubs() {
  const custCoords = CITIES[currentCustomerCity] || { lat: 12.9165, lon: 79.1325 };
  
  const evaluations = WAREHOUSES.map(wh => {
    const distKm = calculateHaversineDistance(custCoords.lat, custCoords.lon, wh.lat, wh.lon);
    
    // Check if warehouse has 100% stock for every item in shopping cart
    let canFulfillAll = true;
    for (const item of shoppingCart) {
      const prod = PRODUCTS.find(p => p.id === item.product_id);
      if (!prod) continue;
      const stock = prod.inventory[wh.id] || 0;
      if (stock < item.quantity) {
        canFulfillAll = false;
        break;
      }
    }

    return {
      ...wh,
      distanceKm: distKm,
      canFulfillAll
    };
  });

  // Sort candidate warehouses by distance ascending
  evaluations.sort((a, b) => a.distanceKm - b.distanceKm);

  // Optimal hub is the closest one that can fulfill 100% of the cart
  optimalHub = evaluations.find(h => h.canFulfillAll) || evaluations[0];
  return { evaluations, optimalHub };
}

// ============================================================================
// UI RENDERING ROUTINES
// ============================================================================

function renderProducts() {
  const grid = document.getElementById("product-card-grid");
  if (!grid) return;

  const searchQuery = (document.getElementById("global-search-input")?.value || "").toLowerCase().trim();

  const filtered = PRODUCTS.filter(p => {
    const matchCat = currentCategoryFilter === "ALL" || p.category_id.toString() === currentCategoryFilter;
    const matchSearch = !searchQuery || p.name.toLowerCase().includes(searchQuery) || p.sku.toLowerCase().includes(searchQuery);
    return matchCat && matchSearch;
  });

  document.getElementById("product-count-display").innerText = `Showing ${filtered.length} component${filtered.length === 1 ? '' : 's'}`;

  grid.innerHTML = filtered.map(p => {
    const totalStock = Object.values(p.inventory).reduce((a, b) => a + b, 0);
    const isLow = totalStock <= (p.reorder_level * 3);

    return `
      <div class="product-card" data-id="${p.id}">
        <div class="product-img-wrapper">
          <span class="product-category-tag">${p.category_name}</span>
          <span class="product-stock-tag ${isLow ? 'stock-low' : 'stock-in'}">
            ${isLow ? '⚠ Low Stock' : '✓ In Stock'} (${totalStock} units)
          </span>
          <img class="product-img" src="${p.image}" alt="${p.name}" loading="lazy" />
        </div>
        <div class="product-card-body">
          <span class="product-sku">${p.sku}</span>
          <h4 class="product-name">${p.name}</h4>
          <p class="product-desc">${p.desc}</p>
          <div class="product-card-footer">
            <div class="product-price">₹${p.price.toLocaleString('en-IN', {minimumFractionDigits: 2})} <span>INR</span></div>
            <button class="btn-add-cart" onclick="addToCart(${p.id})">➕ Add to Cart</button>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function renderProximityWidget() {
  const { evaluations, optimalHub } = evaluateCandidateHubs();
  const listEl = document.getElementById("candidate-hubs-list");
  if (!listEl) return;

  listEl.innerHTML = evaluations.map(hub => {
    const isChosen = hub.id === optimalHub.id;
    return `
      <div class="candidate-hub-row ${isChosen ? 'selected' : ''}">
        <div class="hub-row-info">
          <span class="hub-row-name">${hub.name} (${hub.city})</span>
          <span class="hub-row-dist">🧭 Geodesic: ${hub.distanceKm.toFixed(1)} km</span>
        </div>
        <div class="hub-row-status ${hub.canFulfillAll ? 'text-emerald' : 'text-crimson'}">
          ${hub.canFulfillAll ? (isChosen ? '★ OPTIMAL CHOICE' : '✓ 100% In Stock') : '⚠ Partial Stock'}
        </div>
      </div>
    `;
  }).join("");

  // Update summary badge
  const badge = document.getElementById("proximity-routing-summary-badge");
  if (badge) {
    badge.innerHTML = `<span class="sparkle-icon">🧭</span> Nearest Hub: <strong>${optimalHub.name}</strong> (${optimalHub.distanceKm.toFixed(1)} km away)`;
  }

  // Update decision banner
  const banner = document.getElementById("routing-decision-banner");
  if (banner) {
    banner.innerHTML = `
      <div class="decision-icon">✓</div>
      <div class="decision-text">
        <strong>Optimal Route:</strong> Dispatched from <strong>${optimalHub.name}</strong> (${optimalHub.city}). Geodesic distance: <strong>${optimalHub.distanceKm.toFixed(1)} km</strong>. All line-items in stock!
      </div>
    `;
  }
}

function renderMiniCart() {
  const container = document.getElementById("mini-cart-items-list");
  const subtotalHeader = document.getElementById("cart-subtotal-header");
  const countBadge = document.getElementById("cart-item-count-badge");
  const grandTotalEl = document.getElementById("mini-cart-grand-total");

  const totalItems = shoppingCart.reduce((sum, item) => sum + item.quantity, 0);
  const grandTotal = shoppingCart.reduce((sum, item) => {
    const p = PRODUCTS.find(prod => prod.id === item.product_id);
    return sum + (p ? p.price * item.quantity : 0);
  }, 0);

  if (countBadge) countBadge.innerText = totalItems;
  if (subtotalHeader) subtotalHeader.innerText = `₹${grandTotal.toLocaleString('en-IN')}`;
  if (grandTotalEl) grandTotalEl.innerText = `₹${grandTotal.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;

  if (!container) return;

  if (shoppingCart.length === 0) {
    container.innerHTML = `
      <div class="empty-cart-message">
        <span class="empty-icon">🛒</span>
        <p>Your shopping cart is empty.<br>Click "Add to Cart" on any keyboard component.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = shoppingCart.map(item => {
    const p = PRODUCTS.find(prod => prod.id === item.product_id);
    if (!p) return "";
    return `
      <div class="mini-cart-item">
        <img class="mini-item-thumb" src="${p.image}" alt="${p.name}" />
        <div class="mini-item-info">
          <span class="mini-item-name">${p.name}</span>
          <span class="mini-item-meta">₹${p.price.toLocaleString('en-IN')} × ${item.quantity}</span>
        </div>
        <div class="mini-item-controls">
          <button class="qty-btn" onclick="updateCartQty(${p.id}, -1)">−</button>
          <span class="qty-val">${item.quantity}</span>
          <button class="qty-btn" onclick="updateCartQty(${p.id}, 1)">+</button>
        </div>
      </div>
    `;
  }).join("");
}

// ============================================================================
// SHOPPING CART ACTIONS
// ============================================================================

window.addToCart = function(productId, qty = 1) {
  const existing = shoppingCart.find(i => i.product_id === productId);
  if (existing) {
    existing.quantity += qty;
  } else {
    shoppingCart.push({ product_id: productId, quantity: qty });
  }

  const prod = PRODUCTS.find(p => p.id === productId);
  showToast(`Added ${prod?.name || 'Component'} to Shopping Cart!`, "success");
  
  renderMiniCart();
  renderProximityWidget();
};

window.updateCartQty = function(productId, delta) {
  const idx = shoppingCart.findIndex(i => i.product_id === productId);
  if (idx === -1) return;

  shoppingCart[idx].quantity += delta;
  if (shoppingCart[idx].quantity <= 0) {
    shoppingCart.splice(idx, 1);
  }

  renderMiniCart();
  renderProximityWidget();
};

// ============================================================================
// MODAL & ACID CHECKOUT TRANSACTION SIMULATION
// ============================================================================

function openCheckoutModal() {
  if (shoppingCart.length === 0) {
    showToast("Your cart is empty! Please add components first.", "warning");
    return;
  }

  const backdrop = document.getElementById("checkout-modal-backdrop");
  if (!backdrop) return;

  const { optimalHub } = evaluateCandidateHubs();
  
  document.getElementById("modal-chosen-hub-name").innerText = `${optimalHub.name} — ${optimalHub.city}`;
  document.getElementById("modal-chosen-hub-stats").innerHTML = `
    Geodesic Distance: <strong>${optimalHub.distanceKm.toFixed(1)} km</strong> from ${currentCustomerCity}<br>
    Stock Status: <strong class="text-emerald">100% In Stock</strong> for all cart items!
  `;

  // Render modal item list with product thumbnails
  const listEl = document.getElementById("modal-checkout-items-list");
  let total = 0;
  listEl.innerHTML = shoppingCart.map(item => {
    const p = PRODUCTS.find(prod => prod.id === item.product_id);
    if (!p) return "";
    const sub = p.price * item.quantity;
    total += sub;
    return `
      <div class="modal-checkout-item-row">
        <img class="modal-item-thumb" src="${p.image}" alt="${p.name}" />
        <div class="modal-item-info">
          <div class="modal-item-title">${p.name}</div>
          <div class="modal-item-sub">${p.sku} · Qty: <strong>${item.quantity}</strong></div>
        </div>
        <div class="modal-item-price">₹${sub.toLocaleString('en-IN', {minimumFractionDigits: 2})}</div>
      </div>
    `;
  }).join("");

  document.getElementById("modal-checkout-grand-total").innerText = `₹${total.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;

  // Reset terminal
  const term = document.getElementById("acid-terminal-screen");
  term.innerHTML = `
    <div class="t-line t-dim">-- Nexus Peripherals ACID Transaction Console Ready --</div>
    <div class="t-line t-dim">-- Click 'Confirm Atomic Order' to start sequence --</div>
  `;

  backdrop.classList.add("open");
}

function executeAcidCommit() {
  const term = document.getElementById("acid-terminal-screen");
  const { optimalHub } = evaluateCandidateHubs();
  const orderId = Math.floor(8404 + Math.random() * 500);
  const trackingNumber = `TRK-NX-${Math.random().toString(16).substring(2, 10).toUpperCase()}`;
  const totalAmount = shoppingCart.reduce((sum, item) => {
    const p = PRODUCTS.find(prod => prod.id === item.product_id);
    return sum + (p ? p.price * item.quantity : 0);
  }, 0);

  const steps = [
    { text: `[BEGIN TRANSACTION] Starting atomic multi-item order fulfillment sequence...`, class: "t-dim", delay: 100 },
    { text: `[PROXIMITY] Customer Location: ${currentCustomerCity}. Nearest Hub: ${optimalHub.name} (${optimalHub.distanceKm.toFixed(1)} km)`, class: "t-cyan", delay: 350 },
    { text: `[LOCK] Acquiring FOR UPDATE row locks on PRODUCT_INVENTORY for ${shoppingCart.length} line items...`, class: "t-dim", delay: 700 },
    { text: `[INVENTORY] Verified 100% stock in Hub #${optimalHub.id}. Decrementing bin counts atomically...`, class: "t-cyan", delay: 1050 },
    { text: `[ORDERS] Inserting Master Record: OrderID #${orderId}, Total: ₹${totalAmount.toLocaleString('en-IN')}`, class: "t-dim", delay: 1400 },
    { text: `[ORDER_ITEM] Writing ${shoppingCart.length} itemized child rows into database...`, class: "t-dim", delay: 1750 },
    { text: `[PAYMENT] Recording transaction status: COMPLETED via UPI Gateway`, class: "t-dim", delay: 2100 },
    { text: `[SHIPMENT] Generating courier dispatch manifest with Tracking ID: ${trackingNumber}`, class: "t-warn", delay: 2450 },
    { text: `[COMMIT] Transaction committed successfully to MySQL 8.0! (Isolation Level: REPEATABLE-READ)`, class: "text-emerald font-bold", delay: 2800 },
    { text: `[SMTP] Asynchronous confirmation invoice dispatched to customer email address.`, class: "t-cyan", delay: 3150 },
    { text: `[SUCCESS] Order #${orderId} active. Hub manager notified for dispatch!`, class: "text-emerald font-bold", delay: 3400 }
  ];

  term.innerHTML = "";
  steps.forEach(step => {
    setTimeout(() => {
      const line = document.createElement("div");
      line.className = `t-line ${step.class || ''}`;
      line.innerText = step.text;
      term.appendChild(line);
      term.scrollTop = term.scrollHeight;

      if (step.text.includes("[SUCCESS]")) {
        // Deduct inventory locally
        shoppingCart.forEach(item => {
          const prod = PRODUCTS.find(p => p.id === item.product_id);
          if (prod && prod.inventory[optimalHub.id]) {
            prod.inventory[optimalHub.id] -= item.quantity;
          }
        });

        // Add to shipments list
        SHIPMENTS.unshift({
          id: orderId,
          tracking: trackingNumber,
          order_id: orderId,
          customer: "Rohan Sharma",
          city: currentCustomerCity,
          items: shoppingCart.length,
          status: "PREPARING",
          hub_id: optimalHub.id
        });

        // Clear cart
        shoppingCart = [];
        renderMiniCart();
        renderProducts();
        renderProximityWidget();
        renderHubInventory();
        renderKanban();

        showToast(`🎉 Order #${orderId} Placed! Tracking: ${trackingNumber}`, "success");
      }
    }, step.delay);
  });
}

// ============================================================================
// WAREHOUSE MANAGER PORTAL LOGIC
// ============================================================================

function renderHubInventory() {
  const tbody = document.getElementById("hub-inventory-table-body");
  if (!tbody) return;

  const currentHubId = 2; // Bengaluru Hub
  let lowCount = 0;

  tbody.innerHTML = PRODUCTS.map(p => {
    const stock = p.inventory[currentHubId] || 0;
    const isLow = stock <= p.reorder_level;
    if (isLow) lowCount++;

    return `
      <tr>
        <td><strong>${p.name}</strong></td>
        <td><code>${p.sku}</code></td>
        <td><strong style="font-size:14px; color:${isLow ? '#F87171' : '#34D399'}">${stock}</strong> units</td>
        <td>${p.reorder_level} units</td>
        <td>
          <span class="badge ${isLow ? 'badge-warning' : 'badge-success'}">
            ${isLow ? '⚠️ REORDER NEEDED' : '✓ HEALTHY'}
          </span>
        </td>
        <td>
          <button class="btn btn-secondary" style="padding:3px 8px; font-size:11px;" onclick="quickRestock(${p.id}, 10)">
            +10 Units
          </button>
        </td>
      </tr>
    `;
  }).join("");

  const badge = document.getElementById("low-stock-count-badge");
  if (badge) {
    badge.innerText = `${lowCount} Low Stock Warnings`;
  }
}

window.quickRestock = function(productId, qty) {
  const prod = PRODUCTS.find(p => p.id === productId);
  if (!prod) return;
  prod.inventory[2] = (prod.inventory[2] || 0) + qty;
  renderHubInventory();
  renderProducts();
  showToast(`Restocked ${prod.name} (+${qty} units)!`, "success");
};

function renderKanban() {
  const cols = {
    PREPARING: document.getElementById("kanban-col-preparing"),
    IN_TRANSIT: document.getElementById("kanban-col-in-transit"),
    OUT_FOR_DELIVERY: document.getElementById("kanban-col-out-delivery"),
    DELIVERED: document.getElementById("kanban-col-delivered")
  };

  const counts = {
    PREPARING: document.getElementById("count-col-preparing"),
    IN_TRANSIT: document.getElementById("count-col-in-transit"),
    OUT_FOR_DELIVERY: document.getElementById("count-col-out-delivery"),
    DELIVERED: document.getElementById("count-col-delivered")
  };

  Object.values(cols).forEach(c => { if (c) c.innerHTML = ""; });

  const statuses = ["PREPARING", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED"];

  SHIPMENTS.forEach(s => {
    const targetCol = cols[s.status];
    if (!targetCol) return;

    const currentIdx = statuses.indexOf(s.status);
    const nextStatus = statuses[currentIdx + 1];

    const card = document.createElement("div");
    card.className = "shipment-card";
    card.innerHTML = `
      <div class="shipment-tracking-id">${s.tracking}</div>
      <div class="shipment-dest">${s.customer} (${s.city})</div>
      <div class="shipment-items-count">${s.items} line-items to pack</div>
      ${nextStatus ? `<button class="shipment-advance-btn" onclick="advanceShipmentStatus('${s.tracking}', '${nextStatus}')">Advance to ${nextStatus.replace(/_/g, ' ')} &rarr;</button>` : '<span class="text-emerald" style="font-size:11px; font-weight:700;">✓ Completed Delivery</span>'}
    `;
    targetCol.appendChild(card);
  });

  statuses.forEach(st => {
    const count = SHIPMENTS.filter(s => s.status === st).length;
    if (counts[st]) counts[st].innerText = count;
  });
}

window.advanceShipmentStatus = function(tracking, newStatus) {
  const sh = SHIPMENTS.find(s => s.tracking === tracking);
  if (!sh) return;
  sh.status = newStatus;
  renderKanban();

  // Log SMTP dispatch
  OUTBOX_LOGS.unshift({
    timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
    type: "SHIPMENT_STATUS_UPDATE",
    to: "rohan@gmail.com",
    subject: `Tracking Update: Order #${sh.order_id} is now ${newStatus.replace(/_/g, ' ')}`,
    status: "DELIVERED"
  });

  showToast(`Shipment ${tracking} advanced to ${newStatus.replace(/_/g, ' ')}! Email notification sent.`, "info");
};

// ============================================================================
// SYSTEM ADMINISTRATOR & EDA CANVAS CHARTS
// ============================================================================

function drawOperationsTrendChart() {
  const canvas = document.getElementById("canvas-operations-trend");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  // Fix resolution for high DPI displays
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const w = rect.width;
  const h = rect.height;

  // Clear
  ctx.clearRect(0, 0, w, h);

  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];
  const sales = [14.2, 19.8, 12.5, 24.1, 31.5, 38.8]; // in Lakhs
  const intake = [18.0, 15.0, 22.0, 19.5, 28.0, 25.0]; // in Hundreds

  const padX = 50;
  const padY = 40;
  const chartW = w - padX * 2;
  const chartH = h - padY * 2;

  // Draw grid lines
  ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = padY + (chartH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padX, y);
    ctx.lineTo(w - padX, y);
    ctx.stroke();
  }

  // Draw months on x-axis
  ctx.fillStyle = "#64748B";
  ctx.font = "11px Inter";
  ctx.textAlign = "center";
  months.forEach((m, idx) => {
    const x = padX + (chartW / (months.length - 1)) * idx;
    ctx.fillText(m, x, h - 15);
  });

  // Plot Sales Curve (Cyan)
  const maxSale = 45.0;
  ctx.beginPath();
  const getSaleY = val => padY + chartH - (val / maxSale) * chartH;
  const getX = idx => padX + (chartW / (months.length - 1)) * idx;

  sales.forEach((val, idx) => {
    const x = getX(idx);
    const y = getSaleY(val);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });

  ctx.strokeStyle = "#06B6D4";
  ctx.lineWidth = 3;
  ctx.stroke();

  // Gradient fill for Sales
  const grad = ctx.createLinearGradient(0, padY, 0, padY + chartH);
  grad.addColorStop(0, "rgba(6, 182, 212, 0.35)");
  grad.addColorStop(1, "rgba(6, 182, 212, 0.0)");
  ctx.lineTo(getX(sales.length - 1), padY + chartH);
  ctx.lineTo(getX(0), padY + chartH);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // Plot Intake Curve (Purple)
  ctx.beginPath();
  intake.forEach((val, idx) => {
    const x = getX(idx);
    const y = getSaleY(val);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.strokeStyle = "#A855F7";
  ctx.lineWidth = 2.5;
  ctx.setLineDash([4, 4]);
  ctx.stroke();
  ctx.setLineDash([]);
}

function drawCategoryDonutChart() {
  const canvas = document.getElementById("canvas-category-donut");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const cx = rect.width / 2;
  const cy = rect.height / 2;
  const radius = Math.min(cx, cy) - 18;
  const innerRadius = radius * 0.65;

  const data = [
    { label: "Keyboards", share: 0.52, color: "#3B82F6" },
    { label: "Switches", share: 0.28, color: "#06B6D4" },
    { label: "Keycaps", share: 0.14, color: "#8B5CF6" },
    { label: "Lube & Acc.", share: 0.06, color: "#F59E0B" }
  ];

  let currentAngle = -Math.PI / 2;
  data.forEach(slice => {
    const sliceAngle = slice.share * (Math.PI * 2);
    ctx.beginPath();
    ctx.arc(cx, cy, radius, currentAngle, currentAngle + sliceAngle);
    ctx.arc(cx, cy, innerRadius, currentAngle + sliceAngle, currentAngle, true);
    ctx.closePath();
    ctx.fillStyle = slice.color;
    ctx.fill();
    currentAngle += sliceAngle;
  });

  // Render legend list
  const legend = document.getElementById("category-breakdown-legend");
  if (legend) {
    legend.innerHTML = data.map(d => `
      <div class="cat-row">
        <span><span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${d.color}; margin-right:6px;"></span> ${d.label}</span>
        <strong>${(d.share * 100).toFixed(0)}%</strong>
      </div>
    `).join("");
  }
}

function renderTopSkusTable() {
  const tbody = document.getElementById("top-skus-table-body");
  if (!tbody) return;

  const sorted = [...PRODUCTS].sort((a, b) => (b.price) - (a.price));

  tbody.innerHTML = sorted.slice(0, 5).map((p, idx) => `
    <tr>
      <td><strong>#${idx + 1}</strong></td>
      <td><strong>${p.name}</strong></td>
      <td><code>${p.sku}</code></td>
      <td>${p.category_name}</td>
      <td><strong>${(180 - idx * 28)}</strong> units</td>
      <td>₹${((180 - idx * 28) * p.price).toLocaleString('en-IN')}</td>
      <td><span class="badge badge-success">HIGH VELOCITY</span></td>
    </tr>
  `).join("");
}

// ============================================================================
// TOAST NOTIFICATIONS & MODAL CONTROLLERS
// ============================================================================

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>●</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(40px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function initEventHandlers() {
  // Navigation Tabs
  document.querySelectorAll(".nav-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const target = tab.dataset.portal;

      document.querySelectorAll(".portal-view").forEach(v => v.classList.remove("active"));
      document.getElementById(`portal-${target}-view`)?.classList.add("active");

      if (target === "admin") {
        setTimeout(() => {
          drawOperationsTrendChart();
          drawCategoryDonutChart();
          renderTopSkusTable();
        }, 50);
      } else if (target === "manager") {
        renderHubInventory();
        renderKanban();
      }
    });
  });

  // Profile Selector
  document.getElementById("active-profile-select")?.addEventListener("change", e => {
    const val = e.target.value;
    if (val === "CUSTOMER") {
      document.getElementById("nav-btn-customer")?.click();
    } else if (val.startsWith("MANAGER")) {
      document.getElementById("nav-btn-manager")?.click();
    } else if (val === "ADMIN") {
      document.getElementById("nav-btn-admin")?.click();
    }
    showToast(`Swapped session profile to: ${e.target.options[e.target.selectedIndex].text}`, "info");
  });

  // Category Filter Pills
  document.querySelectorAll(".pill-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".pill-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentCategoryFilter = btn.dataset.category;
      renderProducts();
    });
  });

  // Global Search Input
  document.getElementById("global-search-input")?.addEventListener("input", () => {
    renderProducts();
  });

  // Customer Delivery City Select
  document.getElementById("customer-city-select")?.addEventListener("change", e => {
    currentCustomerCity = e.target.value;
    document.getElementById("map-customer-city-label").innerText = currentCustomerCity;
    renderProximityWidget();
    showToast(`Recalibrated geodesic route for customer destination: ${currentCustomerCity}`, "info");
  });

  // Clear Mini Cart
  document.getElementById("clear-mini-cart-btn")?.addEventListener("click", () => {
    shoppingCart = [];
    renderMiniCart();
    renderProximityWidget();
    showToast("Shopping cart cleared.", "info");
  });

  // Checkout Modal Triggers
  document.getElementById("open-cart-modal-btn")?.addEventListener("click", openCheckoutModal);
  document.getElementById("sidebar-proceed-checkout-btn")?.addEventListener("click", openCheckoutModal);
  document.getElementById("close-checkout-modal-btn")?.addEventListener("click", () => {
    document.getElementById("checkout-modal-backdrop")?.classList.remove("open");
  });

  // Confirm ACID Order Button
  document.getElementById("confirm-acid-order-btn")?.addEventListener("click", executeAcidCommit);

  // Admin Directive Modal
  document.getElementById("admin-broadcast-directive-btn")?.addEventListener("click", () => {
    document.getElementById("directive-modal-backdrop")?.classList.add("open");
  });
  document.getElementById("close-directive-modal-btn")?.addEventListener("click", () => {
    document.getElementById("directive-modal-backdrop")?.classList.remove("open");
  });
  document.getElementById("cancel-directive-btn")?.addEventListener("click", () => {
    document.getElementById("directive-modal-backdrop")?.classList.remove("open");
  });

  document.getElementById("send-directive-email-btn")?.addEventListener("click", () => {
    const to = document.getElementById("directive-recipient-select").value;
    const subj = document.getElementById("directive-subject-input").value;
    OUTBOX_LOGS.unshift({
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
      type: "ADMIN_DIRECTIVE",
      to: to,
      subject: `[ADMIN DIRECTIVE] ${subj}`,
      status: "DELIVERED"
    });
    document.getElementById("directive-modal-backdrop")?.classList.remove("open");
    showToast(`Executive directive dispatched to ${to}!`, "success");
  });

  // Restock Modal
  document.getElementById("open-restock-modal-btn")?.addEventListener("click", () => {
    const sel = document.getElementById("restock-product-select");
    if (sel) {
      sel.innerHTML = PRODUCTS.map(p => `<option value="${p.id}">${p.name} (${p.sku})</option>`).join("");
    }
    document.getElementById("restock-modal-backdrop")?.classList.add("open");
  });
  document.getElementById("close-restock-modal-btn")?.addEventListener("click", () => {
    document.getElementById("restock-modal-backdrop")?.classList.remove("open");
  });
  document.getElementById("cancel-restock-btn")?.addEventListener("click", () => {
    document.getElementById("restock-modal-backdrop")?.classList.remove("open");
  });

  document.getElementById("confirm-restock-btn")?.addEventListener("click", () => {
    const pid = parseInt(document.getElementById("restock-product-select").value);
    const qty = parseInt(document.getElementById("restock-qty-input").value) || 20;
    quickRestock(pid, qty);
    document.getElementById("restock-modal-backdrop")?.classList.remove("open");
  });

  // Outbox Telemetry Modal
  document.getElementById("open-outbox-btn")?.addEventListener("click", () => {
    const tbody = document.getElementById("outbox-manifest-table-body");
    if (tbody) {
      tbody.innerHTML = OUTBOX_LOGS.map(l => `
        <tr>
          <td><span style="font-family:var(--font-mono); font-size:11px;">${l.timestamp}</span></td>
          <td><span class="badge badge-info">${l.type}</span></td>
          <td><strong>${l.to}</strong></td>
          <td>${l.subject}</td>
          <td><span class="badge badge-success">✓ ${l.status}</span></td>
        </tr>
      `).join("");
    }
    document.getElementById("outbox-modal-backdrop")?.classList.add("open");
  });
  document.getElementById("close-outbox-modal-btn")?.addEventListener("click", () => {
    document.getElementById("outbox-modal-backdrop")?.classList.remove("open");
  });

  // Export PDF Button
  document.getElementById("admin-download-pdf-btn")?.addEventListener("click", () => {
    showToast("Generating publication-grade Monthly Audit PDF Report...", "info");
    setTimeout(() => {
      showToast("✓ Monthly Audit PDF compiled and downloaded to reports/!", "success");
    }, 1500);
  });
}

// ============================================================================
// 3D SAKURA MECHANICAL KEYBOARD ASSEMBLY ENGINE
// ============================================================================

const KEYBOARD_LAYOUT_65 = [
  // Row 0: 16 units
  [
    { code: "Escape", label: "🌸", sub: "ESC", unit: 1, type: "novelty-sakura" },
    { code: "Digit1", label: "1", sub: "!", unit: 1, type: "alpha" },
    { code: "Digit2", label: "2", sub: "@", unit: 1, type: "alpha" },
    { code: "Digit3", label: "3", sub: "#", unit: 1, type: "alpha" },
    { code: "Digit4", label: "4", sub: "$", unit: 1, type: "alpha" },
    { code: "Digit5", label: "5", sub: "%", unit: 1, type: "alpha" },
    { code: "Digit6", label: "6", sub: "^", unit: 1, type: "alpha" },
    { code: "Digit7", label: "7", sub: "&", unit: 1, type: "alpha" },
    { code: "Digit8", label: "8", sub: "*", unit: 1, type: "alpha" },
    { code: "Digit9", label: "9", sub: "(", unit: 1, type: "alpha" },
    { code: "Digit0", label: "0", sub: ")", unit: 1, type: "alpha" },
    { code: "Minus", label: "-", sub: "_", unit: 1, type: "alpha" },
    { code: "Equal", label: "=", sub: "+", unit: 1, type: "alpha" },
    { code: "Backspace", label: "⌫", sub: "BACK", unit: 2, type: "modifier" },
    { code: "Delete", label: "DEL", sub: "富士", unit: 1, type: "novelty-fuji" }
  ],
  // Row 1: 16 units
  [
    { code: "Tab", label: "TAB", sub: "↹", unit: 1.5, type: "modifier" },
    { code: "KeyQ", label: "Q", unit: 1, type: "alpha" },
    { code: "KeyW", label: "W", unit: 1, type: "alpha" },
    { code: "KeyE", label: "E", unit: 1, type: "alpha" },
    { code: "KeyR", label: "R", unit: 1, type: "alpha" },
    { code: "KeyT", label: "T", unit: 1, type: "alpha" },
    { code: "KeyY", label: "Y", unit: 1, type: "alpha" },
    { code: "KeyU", label: "U", unit: 1, type: "alpha" },
    { code: "KeyI", label: "I", unit: 1, type: "alpha" },
    { code: "KeyO", label: "O", unit: 1, type: "alpha" },
    { code: "KeyP", label: "P", unit: 1, type: "alpha" },
    { code: "BracketLeft", label: "[", sub: "{", unit: 1, type: "alpha" },
    { code: "BracketRight", label: "]", sub: "}", unit: 1, type: "alpha" },
    { code: "Backslash", label: "\\", sub: "|", unit: 1.5, type: "alpha" },
    { code: "PageUp", label: "PGUP", sub: "鳥居", unit: 1, type: "novelty-fuji" }
  ],
  // Row 2: 16 units
  [
    { code: "CapsLock", label: "CAPS", sub: "⇪", unit: 1.75, type: "modifier" },
    { code: "KeyA", label: "A", unit: 1, type: "alpha" },
    { code: "KeyS", label: "S", unit: 1, type: "alpha" },
    { code: "KeyD", label: "D", unit: 1, type: "alpha" },
    { code: "KeyF", label: "F", sub: "━", unit: 1, type: "alpha" },
    { code: "KeyG", label: "G", unit: 1, type: "alpha" },
    { code: "KeyH", label: "H", unit: 1, type: "alpha" },
    { code: "KeyJ", label: "J", sub: "━", unit: 1, type: "alpha" },
    { code: "KeyK", label: "K", unit: 1, type: "alpha" },
    { code: "KeyL", label: "L", unit: 1, type: "alpha" },
    { code: "Semicolon", label: ";", sub: ":", unit: 1, type: "alpha" },
    { code: "Quote", label: "'", sub: "\"", unit: 1, type: "alpha" },
    { code: "Enter", label: "RETURN ⏎", sub: "富士山", unit: 2.25, type: "novelty-fuji" },
    { code: "PageDown", label: "PGDN", sub: "桜", unit: 1, type: "novelty-sakura" }
  ],
  // Row 3: 16 units
  [
    { code: "ShiftLeft", label: "SHIFT ⇧", unit: 2.25, type: "modifier" },
    { code: "KeyZ", label: "Z", unit: 1, type: "alpha" },
    { code: "KeyX", label: "X", unit: 1, type: "alpha" },
    { code: "KeyC", label: "C", unit: 1, type: "alpha" },
    { code: "KeyV", label: "V", unit: 1, type: "alpha" },
    { code: "KeyB", label: "B", unit: 1, type: "alpha" },
    { code: "KeyN", label: "N", unit: 1, type: "alpha" },
    { code: "KeyM", label: "M", unit: 1, type: "alpha" },
    { code: "Comma", label: ",", sub: "<", unit: 1, type: "alpha" },
    { code: "Period", label: ".", sub: ">", unit: 1, type: "alpha" },
    { code: "Slash", label: "/", sub: "?", unit: 1, type: "alpha" },
    { code: "ShiftRight", label: "SHIFT ⇧", unit: 1.75, type: "modifier" },
    { code: "ArrowUp", label: "▲", unit: 1, type: "novelty-sakura" },
    { code: "End", label: "END", unit: 1, type: "modifier" }
  ],
  // Row 4: 16 units
  [
    { code: "ControlLeft", label: "CTRL", unit: 1.25, type: "modifier" },
    { code: "MetaLeft", label: "❖", sub: "WIN", unit: 1.25, type: "modifier" },
    { code: "AltLeft", label: "ALT", unit: 1.25, type: "modifier" },
    { code: "Space", label: "🌸 桜 S A K U R A 🌸", unit: 6.25, type: "spacebar-sakura" },
    { code: "AltRight", label: "ALT", unit: 1.25, type: "modifier" },
    { code: "ContextMenu", label: "FN", unit: 1, type: "modifier" },
    { code: "ArrowLeft", label: "◄", unit: 1, type: "novelty-sakura" },
    { code: "ArrowDown", label: "▼", unit: 1, type: "novelty-sakura" },
    { code: "ArrowRight", label: "►", unit: 1.75, type: "novelty-sakura" }
  ]
];

let assemblyAudioEnabled = true;
let assemblyAudioContext = null;
let precomputedClickBuffer = null;
let assemblyTimeouts = [];
let assemblyAutoDismissTimer = null;

function getAssemblyAudioCtx() {
  if (!assemblyAudioEnabled) return null;
  if (!assemblyAudioContext) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      assemblyAudioContext = new AudioContextClass();
    }
  }
  if (assemblyAudioContext && assemblyAudioContext.state === "suspended") {
    assemblyAudioContext.resume();
  }
  return assemblyAudioContext;
}

function getClickBuffer(ctx) {
  if (!precomputedClickBuffer && ctx) {
    const len = Math.floor(ctx.sampleRate * 0.005);
    precomputedClickBuffer = ctx.createBuffer(1, len, ctx.sampleRate);
    const data = precomputedClickBuffer.getChannelData(0);
    for (let i = 0; i < len; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (len * 0.25));
    }
  }
  return precomputedClickBuffer;
}

// Synthesize authentic mechanical switch sound ("thock" on snap & keypress)
function playMechanicalThock(isSpace = false) {
  if (!assemblyAudioEnabled) return;
  try {
    const ctx = getAssemblyAudioCtx();
    if (!ctx) return;
    const now = ctx.currentTime;
    
    // Low body oscillator (POM linear switch bottom out)
    const osc = ctx.createOscillator();
    const oscGain = ctx.createGain();
    const filter = ctx.createBiquadFilter();

    filter.type = "lowpass";
    filter.frequency.setValueAtTime(isSpace ? 520 : 880, now);
    filter.Q.setValueAtTime(2.2, now);

    osc.type = "triangle";
    const startFreq = isSpace ? 150 : 250;
    const endFreq = isSpace ? 65 : 110;
    osc.frequency.setValueAtTime(startFreq, now);
    osc.frequency.exponentialRampToValueAtTime(endFreq, now + (isSpace ? 0.08 : 0.045));

    oscGain.gain.setValueAtTime(isSpace ? 0.22 : 0.14, now);
    oscGain.gain.exponentialRampToValueAtTime(0.001, now + (isSpace ? 0.1 : 0.055));

    osc.connect(filter);
    filter.connect(oscGain);
    oscGain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + (isSpace ? 0.11 : 0.06));

    // Fast cached click transient (stem bottoming into brass housing)
    const clickBuf = getClickBuffer(ctx);
    if (clickBuf) {
      const noiseNode = ctx.createBufferSource();
      noiseNode.buffer = clickBuf;
      const noiseGain = ctx.createGain();
      noiseGain.gain.setValueAtTime(isSpace ? 0.08 : 0.05, now);
      noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.006);

      noiseNode.connect(noiseGain);
      noiseGain.connect(ctx.destination);
      noiseNode.start(now);
    }
  } catch (err) {
    // Ignore audio autoplay restrictions gracefully
  }
}

function spawnAmbientPetals() {
  const container = document.getElementById("assembly-petals-container");
  if (!container) return;
  container.innerHTML = "";
  const count = 18;
  for (let i = 0; i < count; i++) {
    const petal = document.createElement("div");
    petal.className = "ambient-petal";
    const left = Math.random() * 100;
    const sizeW = 10 + Math.random() * 12;
    const sizeH = 14 + Math.random() * 16;
    const dur = 7 + Math.random() * 7;
    const delay = Math.random() * 5;
    const opacity = 0.5 + Math.random() * 0.45;

    petal.style.left = `${left}%`;
    petal.style.width = `${sizeW}px`;
    petal.style.height = `${sizeH}px`;
    petal.style.animationDuration = `${dur}s`;
    petal.style.animationDelay = `${delay}s`;
    petal.style.opacity = opacity;
    container.appendChild(petal);
  }
}

function spawnKeyShockwave(keyEl) {
  if (!keyEl) return;
  const shock = document.createElement("div");
  shock.className = "key-shockwave";
  keyEl.appendChild(shock);
  setTimeout(() => shock.remove(), 480);
}

function initKeyboardAssembly() {
  const matrixContainer = document.getElementById("kb-matrix");
  if (!matrixContainer) return;

  spawnAmbientPetals();

  // Populate Matrix
  matrixContainer.innerHTML = "";
  KEYBOARD_LAYOUT_65.forEach((rowKeys) => {
    const rowEl = document.createElement("div");
    rowEl.className = "kb-row";

    rowKeys.forEach((key) => {
      const keyEl = document.createElement("div");
      keyEl.className = "kb-key";
      keyEl.dataset.code = key.code;
      keyEl.style.setProperty("--unit", key.unit);

      // Switch Socket & Stem
      const socketEl = document.createElement("div");
      socketEl.className = "switch-socket";
      socketEl.innerHTML = `
        <div class="switch-led"></div>
        <div class="switch-stem"></div>
      `;

      // Keycap
      const keycapEl = document.createElement("div");
      keycapEl.className = `kb-keycap key-${key.type}`;
      keycapEl.innerHTML = `
        <span class="key-legend">${key.label}</span>
        ${key.sub ? `<span class="key-sublegend">${key.sub}</span>` : ""}
      `;

      // Click / Tap listener for manual testing
      keyEl.addEventListener("mousedown", () => {
        keycapEl.classList.add("pressed");
        playMechanicalThock(key.code === "Space");
        spawnKeyShockwave(keyEl);
      });
      keyEl.addEventListener("mouseup", () => keycapEl.classList.remove("pressed"));
      keyEl.addEventListener("mouseleave", () => keycapEl.classList.remove("pressed"));

      keyEl.appendChild(socketEl);
      keyEl.appendChild(keycapEl);
      rowEl.appendChild(keyEl);
    });

    matrixContainer.appendChild(rowEl);
  });

  // Attach interactive typing handlers on window
  window.addEventListener("keydown", (e) => {
    const splash = document.getElementById("assembly-splash");
    if (!splash || splash.classList.contains("dismissed")) return;
    
    // Ignore input if typing in an actual input field
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") return;

    const keyEl = document.querySelector(`.kb-key[data-code="${e.code}"]`);
    if (keyEl) {
      const cap = keyEl.querySelector(".kb-keycap");
      if (cap && !cap.classList.contains("pressed")) {
        cap.classList.add("pressed");
        playMechanicalThock(e.code === "Space");
        spawnKeyShockwave(keyEl);
      }
    }
  });

  window.addEventListener("keyup", (e) => {
    const keyEl = document.querySelector(`.kb-key[data-code="${e.code}"]`);
    if (keyEl) {
      const cap = keyEl.querySelector(".kb-keycap");
      if (cap) cap.classList.remove("pressed");
    }
  });

  // Audio Toggle Button
  const audioBtn = document.getElementById("assembly-audio-toggle");
  if (audioBtn) {
    audioBtn.addEventListener("click", () => {
      assemblyAudioEnabled = !assemblyAudioEnabled;
      const icon = document.getElementById("audio-icon");
      const text = document.getElementById("audio-text");
      if (icon) icon.textContent = assemblyAudioEnabled ? "🔊" : "🔇";
      if (text) text.textContent = assemblyAudioEnabled ? "Audio ON" : "Muted";
      if (assemblyAudioEnabled) {
        getAssemblyAudioCtx();
        playMechanicalThock(false);
      }
    });
  }

  // Dismiss / Enter Storefront Buttons
  document.getElementById("assembly-skip-btn")?.addEventListener("click", dismissAssemblySplash);
  document.getElementById("assembly-enter-btn")?.addEventListener("click", dismissAssemblySplash);

  // Header Replay Button
  document.getElementById("replay-assembly-btn")?.addEventListener("click", () => {
    const splash = document.getElementById("assembly-splash");
    if (splash) {
      splash.classList.remove("dismissed");
      startAssemblyAnimation();
    }
  });

  // Start initial sequence
  startAssemblyAnimation();
}

function startAssemblyAnimation() {
  // Clear any existing timers
  assemblyTimeouts.forEach(t => clearTimeout(t));
  assemblyTimeouts = [];
  if (assemblyAutoDismissTimer) clearTimeout(assemblyAutoDismissTimer);

  const underglow = document.getElementById("chassis-underglow");
  if (underglow) underglow.classList.remove("active");

  const stagePill = document.getElementById("assembly-stage-pill");
  if (stagePill) stagePill.textContent = "ASSEMBLING CHASSIS & KEYCAP MATRIX...";

  const statusText = document.getElementById("assembly-hud-status");
  if (statusText) {
    statusText.textContent = "Attaching Keycaps...";
    statusText.classList.remove("text-emerald");
  }

  const allKeycaps = document.querySelectorAll(".kb-keycap");
  allKeycaps.forEach(cap => {
    cap.classList.remove("anim-attaching", "attached", "pressed");
  });

  const chassis = document.getElementById("keyboard-chassis");
  if (chassis) chassis.classList.remove("assembled");

  // Calculate organic fluid cascading wave delays
  let maxDelay = 0;
  KEYBOARD_LAYOUT_65.forEach((rowKeys, rIdx) => {
    rowKeys.forEach((key, cIdx) => {
      const keyEl = document.querySelector(`.kb-key[data-code="${key.code}"]`);
      if (!keyEl) return;
      const cap = keyEl.querySelector(".kb-keycap");
      if (!cap) return;

      // Silky smooth diagonal cascading wave
      let delay = 0.10 + (rIdx * 0.08) + (cIdx * 0.024);
      if (key.code === "Space") {
        delay = 0.10 + (4 * 0.08) + (10 * 0.024) + 0.22;
      }
      if (delay > maxDelay) maxDelay = delay;

      cap.style.setProperty("--delay", `${delay.toFixed(3)}s`);
      cap.classList.add("anim-attaching");
    });
  });

  // Scheduled rhythmic mechanical audio clicks during wave flight
  if (assemblyAudioEnabled) {
    const waveTickDelays = [0.18, 0.32, 0.46, 0.60, 0.74, 0.88, 1.02];
    waveTickDelays.forEach(sec => {
      const t = setTimeout(() => {
        playMechanicalThock(false);
      }, sec * 1000);
      assemblyTimeouts.push(t);
    });
    // Final spacebar thock
    const spaceThock = setTimeout(() => {
      playMechanicalThock(true);
    }, (maxDelay + 0.45) * 1000);
    assemblyTimeouts.push(spaceThock);
  }

  // Completion sequence when all keys have attached
  const completionTimer = setTimeout(() => {
    if (chassis) chassis.classList.add("assembled");
    if (underglow) underglow.classList.add("active");
    if (stagePill) stagePill.textContent = "🌸 ALL 68 KEYCAPS ASSEMBLED — SYSTEM READY";
    if (statusText) {
      statusText.textContent = "✓ Assembled & Firmware Active";
      statusText.classList.add("text-emerald");
    }

    // Auto dismiss after 5 seconds if left idle
    assemblyAutoDismissTimer = setTimeout(() => {
      dismissAssemblySplash();
    }, 5000);
  }, (maxDelay + 0.72) * 1000);

  assemblyTimeouts.push(completionTimer);
}

function dismissAssemblySplash() {
  if (assemblyAutoDismissTimer) clearTimeout(assemblyAutoDismissTimer);
  const splash = document.getElementById("assembly-splash");
  if (splash && !splash.classList.contains("dismissed")) {
    splash.classList.add("dismissed");
    showToast("✨ Welcome to Nexus Peripherals! Browse custom boards, switches & keycaps.", "info");
  }
}

// ============================================================================
// APP ENTRYPOINT
// ============================================================================

window.addEventListener("DOMContentLoaded", () => {
  renderProducts();
  renderMiniCart();
  renderProximityWidget();
  renderHubInventory();
  renderKanban();
  initEventHandlers();
  initKeyboardAssembly();
});

