/**
 * NEXUS PERIPHERALS — NEON FRONTEND ENGINE
 * Multi-Warehouse Inventory & Proximity Routing (BACSE202 Database Systems project)
 * Data block below is unchanged from the original app.js (synced with 01_schema.sql and 02_seed_data.sql).
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


// ============================================================================
// EXTRA STATE
// ============================================================================
let currentHubId = 2;          // hub shown in the manager portal
let revenueExtra = 0;          // revenue from orders placed in this session
let paymentMethod = "UPI";
const NEON = ["#00f0ff", "#ff2bd6", "#b6ff3c", "#8b5cff"];
const STATUSES = ["PREPARING", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED"];
const RM = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const inr = (n, d = 0) => "₹" + Number(n).toLocaleString("en-IN", { minimumFractionDigits: d, maximumFractionDigits: d });
const sleep = ms => new Promise(r => setTimeout(r, RM ? 0 : ms));
const cartTotal = () => shoppingCart.reduce((s, i) => s + PRODUCTS.find(p => p.id === i.product_id).price * i.quantity, 0);
const cartCount = () => shoppingCart.reduce((s, i) => s + i.quantity, 0);
const nowStamp = () => new Date().toISOString().replace("T", " ").substring(0, 19);

const SHOWCASE_INVOICE_ITEMS = [
  { name: "Nexus mechanical keyboard, Cherry MX Brown", price: 7499, quantity: 1, image: "images/keychron_q1.jpg" },
  { name: "Keycap Set, Aura RGB", price: 1500, quantity: 1, image: "images/aura_keycaps.svg" },
  { name: "Nexus Gaming Mouse, Pulse", price: 3299, quantity: 1, image: "images/nexus_mouse.svg" }
];

// ============================================================================
// VISUAL EFFECTS (background particles, click bursts, tilt, ripple, fly-to-cart)
// ============================================================================
const bgc = $("#bg"), bgx = bgc.getContext("2d"), fxc = $("#fx"), fxx = fxc.getContext("2d");
let stars = [], bits = [];
function sizeCanvases() {
  bgc.width = fxc.width = innerWidth; bgc.height = fxc.height = innerHeight;
  stars = Array.from({ length: 70 }, () => ({ x: Math.random() * bgc.width, y: Math.random() * bgc.height, r: Math.random() * 1.8 + .4, v: Math.random() * .4 + .1, c: NEON[Math.random() * 4 | 0] }));
}
function burst(x, y, n = 16, power = 1) {
  if (RM) return;
  for (let i = 0; i < n; i++) {
    const a = Math.random() * 6.283, s = (Math.random() * 5 + 2) * power;
    bits.push({ x, y, vx: Math.cos(a) * s, vy: Math.sin(a) * s, l: 1, c: NEON[Math.random() * 4 | 0], r: Math.random() * 3 + 1.5 });
  }
}
function fxLoop() {
  bgx.clearRect(0, 0, bgc.width, bgc.height);
  stars.forEach(s => { s.y -= s.v; if (s.y < 0) s.y = bgc.height; bgx.fillStyle = s.c; bgx.globalAlpha = .55; bgx.shadowBlur = 12; bgx.shadowColor = s.c; bgx.beginPath(); bgx.arc(s.x, s.y, s.r, 0, 6.283); bgx.fill(); });
  fxx.clearRect(0, 0, fxc.width, fxc.height);
  bits = bits.filter(b => b.l > 0);
  bits.forEach(b => { b.x += b.vx; b.y += b.vy; b.vy += .12; b.vx *= .98; b.l -= .022; fxx.globalAlpha = Math.max(b.l, 0); fxx.fillStyle = b.c; fxx.shadowBlur = 14; fxx.shadowColor = b.c; fxx.beginPath(); fxx.arc(b.x, b.y, b.r, 0, 6.283); fxx.fill(); });
  requestAnimationFrame(fxLoop);
}
function attachTilt() {
  $$(".card").forEach(c => {
    c.onmousemove = e => {
      const r = c.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      c.style.transform = `rotateY(${(x - .5) * 14}deg) rotateX(${(.5 - y) * 14}deg) scale(1.03)`;
      c.firstElementChild.style.setProperty("--mx", x * 100 + "%"); c.firstElementChild.style.setProperty("--my", y * 100 + "%");
    };
    c.onmouseleave = () => { c.style.transform = ""; };
  });
}
function flyToCart(fromEl, src) {
  if (RM) return;
  const a = fromEl.getBoundingClientRect(), t = $("#open-cart-modal-btn").getBoundingClientRect(), d = document.createElement("img");
  d.src = src; d.className = "fly"; d.style.left = a.left + "px"; d.style.top = a.top + "px"; document.body.appendChild(d);
  requestAnimationFrame(() => { d.style.left = t.left + t.width / 2 + "px"; d.style.top = t.top + "px"; d.style.transform = "scale(.2) rotate(540deg)"; d.style.opacity = ".2"; });
  setTimeout(() => {
    d.remove(); burst(t.left + t.width / 2, t.top + 10, 18);
    const b = $("#open-cart-modal-btn"); b.classList.remove("bump"); void b.offsetWidth; b.classList.add("bump");
  }, 700);
}
function countUp(el, to, fmt) {
  if (RM) { el.textContent = fmt(to); return; }
  const t0 = performance.now();
  (function f(t) { const p = Math.min((t - t0) / 900, 1); el.textContent = fmt(to * (1 - Math.pow(1 - p, 3))); if (p < 1) requestAnimationFrame(f); })(t0);
}

// ============================================================================
// HAVERSINE PROXIMITY ENGINE
// ============================================================================
function evaluateCandidateHubs() {
  const c = CITIES[currentCustomerCity] || CITIES["Vellore"];
  const evaluations = WAREHOUSES.map(wh => {
    const distanceKm = calculateHaversineDistance(c.lat, c.lon, wh.lat, wh.lon);
    const okLines = shoppingCart.filter(i => (PRODUCTS.find(p => p.id === i.product_id).inventory[wh.id] || 0) >= i.quantity).length;
    const canFulfillAll = okLines === shoppingCart.length;
    const stockPct = shoppingCart.length ? Math.round(okLines / shoppingCart.length * 100) : 100;
    return { ...wh, distanceKm, canFulfillAll, stockPct };
  }).sort((a, b) => a.distanceKm - b.distanceKm);
  optimalHub = evaluations.find(h => h.canFulfillAll) || evaluations[0];
  return { evaluations, optimalHub };
}

// ============================================================================
// STOREFRONT
// ============================================================================
function renderProducts() {
  const grid = $("#product-card-grid"); if (!grid) return;
  const q = ($("#global-search-input").value || "").toLowerCase().trim();
  const list = PRODUCTS.filter(p => (currentCategoryFilter === "ALL" || String(p.category_id) === currentCategoryFilter) && (!q || p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q)));
  $("#product-count-display").textContent = `Showing ${list.length} component${list.length === 1 ? "" : "s"}`;
  grid.innerHTML = list.length ? list.map((p, i) => {
    const total = Object.values(p.inventory).reduce((a, b) => a + b, 0), low = total <= p.reorder_level * 3;
    return `<article class="card" style="--c:${NEON[i % 4]};--d:${-i * .7}s"><div class="in">
      <div class="pimg"><span class="ptag">${p.category_name}</span><span class="stk ${low ? "lo" : "ok"}">${low ? "Low stock" : "In stock"} · ${total}</span><img src="${p.image}" alt="${p.name}" loading="lazy" onerror="this.style.display='none'"></div>
      <span class="sku">${p.sku}</span><h3>${p.name}</h3><p class="desc">${p.desc}</p>
      <div class="foot"><div class="price">${inr(p.price)}</div><button class="btn sm" onclick="addToCart(${p.id}, 1, this)">Add to cart</button></div></div></article>`;
  }).join("") : `<p class="empty">No components match "${q}". Try a different search or category.</p>`;
  attachTilt();
}

function renderProximityWidget() {
  const { evaluations, optimalHub: best } = evaluateCandidateHubs();
  const max = Math.max(...evaluations.map(e => e.distanceKm));
  $("#candidate-hubs-list").innerHTML = evaluations.map(h => {
    const cls = h.id === best.id ? "best" : (h.canFulfillAll ? "" : "out");
    const note = h.id === best.id ? "Optimal" : (h.canFulfillAll ? "Full stock" : `${h.stockPct}% in stock`);
    return `<div class="lane ${cls}"><div class="top2"><span>${h.city} hub</span><span class="tagx">${h.distanceKm.toFixed(1)} km · ${note}</span></div><div class="track"><div class="fill" data-w="${Math.max(6, h.distanceKm / max * 100)}"></div></div></div>`;
  }).join("");
  requestAnimationFrame(() => requestAnimationFrame(() => $$("#candidate-hubs-list .fill").forEach(f => f.style.width = f.dataset.w + "%")));
  $("#proximity-routing-summary-badge").innerHTML = `Nearest hub: <strong>${best.name}</strong> (${best.distanceKm.toFixed(1)} km)`;
  $("#routing-decision-banner").innerHTML = shoppingCart.length
    ? (best.canFulfillAll ? `Ships from <strong>${best.name}</strong>, ${best.distanceKm.toFixed(1)} km away. Every item is in stock.` : `No single hub holds your whole cart. Lower the quantities or split the order.`)
    : `Closest hub: <strong>${best.name}</strong>. Add items to check it can fill your cart.`;
}

function renderMiniCart() {
  const el = $("#mini-cart-items-list"), total = cartTotal();
  $("#cart-item-count-badge").textContent = cartCount();
  $("#cart-subtotal-header").textContent = inr(total);
  $("#mini-cart-grand-total").textContent = inr(total, 2);
  el.innerHTML = shoppingCart.length ? shoppingCart.map(i => {
    const p = PRODUCTS.find(x => x.id === i.product_id);
    return `<div class="mini"><img src="${p.image}" alt="" onerror="this.style.visibility='hidden'"><div><b>${p.name}</b><span class="sub">${inr(p.price)} × ${i.quantity}</span></div><div class="q"><button onclick="updateCartQty(${p.id},-1)" aria-label="Less">−</button>${i.quantity}<button onclick="updateCartQty(${p.id},1)" aria-label="More">+</button></div></div>`;
  }).join("") : `<p class="empty">Your cart is empty. Add a keyboard, switches or keycaps.</p>`;
}

window.addToCart = function (id, qty = 1, btn) {
  const ex = shoppingCart.find(i => i.product_id === id);
  ex ? ex.quantity += qty : shoppingCart.push({ product_id: id, quantity: qty });
  const p = PRODUCTS.find(x => x.id === id);
  if (btn) flyToCart(btn, p.image);
  showToast(`Added ${p.name} to cart`, "success");
  renderMiniCart(); renderProximityWidget();
};
window.updateCartQty = function (id, d) {
  const i = shoppingCart.findIndex(x => x.product_id === id); if (i < 0) return;
  shoppingCart[i].quantity += d; if (shoppingCart[i].quantity <= 0) shoppingCart.splice(i, 1);
  renderMiniCart(); renderProximityWidget(); if ($("#checkout-modal-backdrop").classList.contains("open")) renderCheckout();
};

// ============================================================================
// CHECKOUT: GEODESIC MAP + INVOICE + ACID COMMIT
// ============================================================================
const proj = (lat, lon) => ({ x: 30 + (lon - 68) / 30 * 360, y: 20 + (36 - lat) / 28 * 420 });

function renderGeodesicMap() {
  const { evaluations, optimalHub: best } = evaluateCandidateHubs();
  const c = CITIES[currentCustomerCity], cp = proj(c.lat, c.lon);
  let s = "";
  for (let i = 1; i < 6; i++) s += `<line x1="${i * 70}" y1="0" x2="${i * 70}" y2="460" stroke="rgba(0,240,255,.07)"/><line x1="0" y1="${i * 77}" x2="420" y2="${i * 77}" stroke="rgba(0,240,255,.07)"/>`;
  evaluations.forEach(h => {
    const hp = proj(h.lat, h.lon), dx = hp.x - cp.x, dy = hp.y - cp.y, mx = (cp.x + hp.x) / 2 - dy * .22, my = (cp.y + hp.y) / 2 + dx * .22;
    s += `<path class="arc ${h.id === best.id ? "best" : ""}" d="M${cp.x} ${cp.y} Q${mx} ${my} ${hp.x} ${hp.y}"/>`;
  });
  evaluations.forEach(h => {
    const hp = proj(h.lat, h.lon), col = h.id === best.id ? "#b6ff3c" : "#ff2bd6";
    s += `<g><circle class="hubdot" cx="${hp.x}" cy="${hp.y}" r="13" fill="none" stroke="${col}"/><rect x="${hp.x - 5}" y="${hp.y - 5}" width="10" height="10" fill="${col}" style="filter:drop-shadow(0 0 6px ${col})"/><text class="maplab" x="${hp.x + 16}" y="${hp.y + 4}">${h.city.slice(0, 3).toUpperCase()}</text></g>`;
  });
  s += `<g transform="translate(${cp.x},${cp.y})"><circle r="16" fill="none" stroke="#00f0ff" class="hubdot"/><circle r="6" fill="#00f0ff" style="filter:drop-shadow(0 0 8px #00f0ff)"/><text class="maplab" y="-22" text-anchor="middle" fill="#00f0ff">${currentCustomerCity}</text></g>`;
  $("#geo-map").innerHTML = s;
  $("#map-floating-callouts").innerHTML = evaluations.map(h => `<div class="co ${h.id === best.id ? "best" : ""}"><span>${h.distanceKm.toFixed(1)} km to ${h.city} hub<small>${h.stockPct}% of cart in stock</small></span><b class="${h.id === best.id ? "text-emerald" : ""}">${h.id === best.id ? "Optimal" : (h.canFulfillAll ? "Eligible" : "Partial")}</b></div>`).join("");
}

function renderCheckout() {
  const items = shoppingCart.length ? shoppingCart.map(i => { const p = PRODUCTS.find(x => x.id === i.product_id); return { name: p.name, price: p.price, quantity: i.quantity, image: p.image }; }) : SHOWCASE_INVOICE_ITEMS;
  $("#invoice-items-container").innerHTML = (shoppingCart.length ? "" : `<p class="sub" style="margin-bottom:6px">Your cart is empty, so this shows a sample order.</p>`) + items.map(i => `<div class="inv"><img src="${i.image}" alt="" onerror="this.style.visibility='hidden'"><span>${i.name}</span><b>${i.quantity} × ${inr(i.price)}</b></div>`).join("");
  const sub = items.reduce((s, i) => s + i.price * i.quantity, 0), gst = sub * .18;
  $("#invoice-summary").innerHTML = `<div><span>Subtotal</span><span>${inr(sub, 2)}</span></div><div><span>GST (18%)</span><span>${inr(gst, 2)}</span></div><div class="g"><span>Total</span><span>${inr(sub + gst, 2)}</span></div>`;
  renderPaymentBody(); renderGeodesicMap();
}
function renderPaymentBody() {
  const el = $("#payment-body");
  if (paymentMethod === "UPI") {
    const cells = Array.from({ length: 81 }, (_, i) => { const r = Math.floor(i / 9), c = i % 9, corner = (r < 3 && c < 3) || (r < 3 && c > 5) || (r > 5 && c < 3); return `<i class="${corner || (i * 7 + r * 3) % 3 === 0 ? "" : "w"}"></i>`; }).join("");
    el.innerHTML = `<div class="qr">${cells}</div><div><b>Scan with any UPI app</b><br><span class="sub">Google Pay, PhonePe, Paytm, BHIM</span><br><code>nexusperipherals@icici</code></div>`;
  } else if (paymentMethod === "CARD") {
    el.innerHTML = `<div style="width:100%;display:grid;gap:8px"><input class="inp" value="4532 •••• •••• 8892" aria-label="Card number"><div style="display:flex;gap:8px"><input class="inp" value="08/29" aria-label="Expiry" style="width:50%"><input class="inp" type="password" value="123" aria-label="CVV" style="width:50%"></div></div>`;
  } else {
    el.innerHTML = `<label style="flex-direction:column;align-items:stretch;width:100%">Select bank<select class="sel"><option>HDFC Bank</option><option>State Bank of India</option><option>ICICI Bank</option><option>Axis Bank</option><option>Kotak Mahindra Bank</option></select></label>`;
  }
}
function termLine(text, cls) {
  const t = $("#acid-terminal-screen"); t.querySelector("i")?.remove();
  const d = document.createElement("div"); d.className = cls; d.textContent = text; t.appendChild(d); t.scrollTop = t.scrollHeight;
}
function openCheckoutModal() {
  renderCheckout();
  $("#acid-terminal-screen").innerHTML = `<div class="l-dim">Ready. Press confirm to run the transaction.</div>`;
  $("#checkout-modal-backdrop").classList.add("open");
}
let committing = false;
async function executeAcidCommit() {
  if (committing) return;
  const { optimalHub: hub } = evaluateCandidateHubs();
  const real = shoppingCart.length > 0;
  if (real && !hub.canFulfillAll) { showToast("No hub can fill this whole cart. Lower the quantities.", "warn"); return; }
  committing = true;
  const btn = $("#confirm-acid-order-btn"); btn.disabled = true; btn.textContent = "Committing atomic order...";
  $("#acid-terminal-screen").innerHTML = "";
  const tracking = `NX${Math.floor(1000000 + Math.random() * 9000000)}`, orderId = 8404 + SHIPMENTS.length - 4 + 1;
  const lines = [["START TRANSACTION (isolation: REPEATABLE READ)", "l-dim"], [`SELECT ... FOR UPDATE on product_inventory, ${hub.name} hub`, "l-lock"]];
  shoppingCart.forEach(i => { const p = PRODUCTS.find(x => x.id === i.product_id); lines.push([`UPDATE stock: ${p.sku} -${i.quantity} (${p.inventory[hub.id]} -> ${p.inventory[hub.id] - i.quantity})`, "l-lock"]); });
  lines.push([`INSERT order #${orderId} and order_items`, "l-dim"], [`Payment verified via ${paymentMethod}`, "l-dim"], [`Generating tracking number ${tracking}`, "l-trk"], ["COMMIT: transaction complete", "l-ok"]);
  for (const [t, c] of lines) { termLine("> " + t, c); await sleep(380); }
  if (real) {
    const n = cartCount(); revenueExtra += cartTotal() * 1.18;
    shoppingCart.forEach(i => { const p = PRODUCTS.find(x => x.id === i.product_id); p.inventory[hub.id] -= i.quantity; p.sold = (p.sold || 0) + i.quantity; });
    SHIPMENTS.push({ id: 1000 + SHIPMENTS.length + 1, tracking, order_id: orderId, customer: "Rohan Sharma", city: currentCustomerCity, items: n, status: "PREPARING", hub_id: hub.id });
    OUTBOX_LOGS.unshift({ timestamp: nowStamp(), type: "CUSTOMER_ORDER_PLACED", to: "rohan@gmail.com", subject: `Order #${orderId} Confirmed [Nexus Peripherals]`, status: "DELIVERED" },
      { timestamp: nowStamp(), type: "HUB_NEW_ORDER_ALERT", to: hub.manager.includes("@") ? hub.manager.match(/\(([^)]+)\)/)?.[1] || hub.manager : `${hub.manager}@nexus.internal`, subject: `ACTION REQUIRED: New Order #${orderId} Routed to Hub #${hub.id}`, status: "DELIVERED" });
    shoppingCart = [];
  }
  const r = btn.getBoundingClientRect(); for (let i = 0; i < 4; i++) setTimeout(() => burst(r.left + Math.random() * r.width, r.top, 60, 2), i * 150);
  btn.disabled = false; btn.textContent = "Confirm atomic order (ACID commit)"; committing = false;
  showToast(`Order committed. Tracking ${tracking}`, "success");
  renderMiniCart(); renderProximityWidget(); renderProducts(); renderHubInventory(); renderKanban(); renderCheckout();
}

// ============================================================================
// HUB MANAGER PORTAL
// ============================================================================
function renderHubInventory() {
  const wh = WAREHOUSES.find(w => w.id === currentHubId);
  $("#current-manager-hub-name").textContent = `${wh.name}, ${wh.city}`;
  $("#current-manager-meta").textContent = `Manager: ${wh.manager} · Lat ${wh.lat}, Lon ${wh.lon}`;
  let low = 0;
  $("#hub-inventory-table-body").innerHTML = PRODUCTS.map(p => {
    const s = p.inventory[currentHubId] || 0, isLow = s <= p.reorder_level; if (isLow) low++;
    return `<tr><td>${p.name}</td><td><code>${p.sku}</code></td><td><b class="${isLow ? "text-crimson" : "text-emerald"}">${s}</b> units</td><td>${p.reorder_level}</td><td><span class="pill ${isLow ? "low" : "ok"}">${isLow ? "Reorder" : "Healthy"}</span></td><td><button class="btn sm" onclick="quickRestock(${p.id},10)">+10</button></td></tr>`;
  }).join("");
  $("#low-stock-count-badge").textContent = `${low} low stock`;
}
window.quickRestock = function (id, qty) {
  const p = PRODUCTS.find(x => x.id === id); p.inventory[currentHubId] = (p.inventory[currentHubId] || 0) + qty;
  renderHubInventory(); renderProducts(); renderProximityWidget(); showToast(`Restocked ${p.name} (+${qty} units)`, "success");
};
function renderKanban() {
  const ids = { PREPARING: "preparing", IN_TRANSIT: "in-transit", OUT_FOR_DELIVERY: "out-delivery", DELIVERED: "delivered" };
  const mine = SHIPMENTS.filter(s => s.hub_id === currentHubId);
  STATUSES.forEach((st, idx) => {
    const list = mine.filter(s => s.status === st), next = STATUSES[idx + 1];
    $("#kanban-col-" + ids[st]).innerHTML = list.map(s => `<div class="ship"><code>${s.tracking}</code>${s.customer} (${s.city})<small>${s.items} line-items</small>${next ? `<button onclick="advanceShipmentStatus('${s.tracking}','${next}')">Advance to ${next.replace(/_/g, " ").toLowerCase()}</button>` : `<small class="text-emerald">Delivered</small>`}</div>`).join("");
    $("#count-col-" + ids[st]).textContent = list.length;
  });
  $("#active-dispatch-badge").textContent = `${mine.filter(s => s.status !== "DELIVERED").length} active`;
}
window.advanceShipmentStatus = function (tracking, status) {
  const s = SHIPMENTS.find(x => x.tracking === tracking); if (!s) return; s.status = status; renderKanban();
  OUTBOX_LOGS.unshift({ timestamp: nowStamp(), type: "SHIPMENT_STATUS_UPDATE", to: "rohan@gmail.com", subject: `Tracking Update: Order #${s.order_id} is now ${status.replace(/_/g, " ")}`, status: "DELIVERED" });
  burst(innerWidth / 2, innerHeight / 2, 24); showToast(`Shipment ${tracking} moved to ${status.replace(/_/g, " ").toLowerCase()}. Email sent.`, "info");
};

// ============================================================================
// ADMIN / EDA
// ============================================================================
function setupCanvas(c) {
  const dpr = window.devicePixelRatio || 1, r = c.getBoundingClientRect();
  c.width = r.width * dpr; c.height = r.height * dpr; const x = c.getContext("2d"); x.setTransform(dpr, 0, 0, dpr, 0, 0); return { x, w: r.width, h: r.height };
}
function drawOperationsTrendChart() {
  const c = $("#canvas-operations-trend"); if (!c || !c.offsetWidth) return;
  const { x, w, h } = setupCanvas(c), M = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], sales = [14.2, 19.8, 12.5, 24.1, 31.5, 38.8], intake = [18, 15, 22, 19.5, 28, 25], t0 = performance.now(), pad = 40, cw = w - pad * 2, ch = h - pad * 2, mx = 45;
  (function f(t) {
    const p = RM ? 1 : Math.min((t - t0) / 1000, 1), e = 1 - Math.pow(1 - p, 3); x.clearRect(0, 0, w, h); x.font = "12px 'Exo 2'"; x.textAlign = "center";
    for (let i = 0; i <= 4; i++) { const y = pad + ch - ch * i / 4; x.strokeStyle = "rgba(255,255,255,.07)"; x.beginPath(); x.moveTo(pad, y); x.lineTo(w - pad, y); x.stroke(); }
    sales.forEach((v, i) => { const bw = cw / 6 * .5, bx = pad + cw / 6 * i + (cw / 6 - bw) / 2, bh = ch * v / mx * e; const g = x.createLinearGradient(0, h - pad - bh, 0, h - pad); g.addColorStop(0, "#00f0ff"); g.addColorStop(1, "rgba(139,92,255,.2)"); x.shadowBlur = 16; x.shadowColor = "#00f0ff"; x.fillStyle = g; x.beginPath(); x.roundRect(bx, h - pad - bh, bw, bh, [6, 6, 0, 0]); x.fill(); x.shadowBlur = 0; x.fillStyle = "#8089b8"; x.fillText(M[i], bx + bw / 2, h - pad + 18); });
    x.strokeStyle = "#ff2bd6"; x.lineWidth = 3; x.shadowBlur = 14; x.shadowColor = "#ff2bd6"; x.beginPath();
    intake.forEach((v, i) => { const px = pad + cw / 6 * i + cw / 12, py = h - pad - ch * v / mx * e; i ? x.lineTo(px, py) : x.moveTo(px, py); }); x.stroke();
    intake.forEach((v, i) => { x.fillStyle = "#ff2bd6"; x.beginPath(); x.arc(pad + cw / 6 * i + cw / 12, h - pad - ch * v / mx * e, 4, 0, 6.283); x.fill(); }); x.shadowBlur = 0;
    if (p < 1) requestAnimationFrame(f);
  })(t0);
}
const CATEGORY_SHARE = [["Mechanical Keyboards", 46], ["Switches", 24], ["Keycaps", 18], ["Lube & Accessories", 12]];
function drawCategoryDonutChart() {
  const c = $("#canvas-category-donut"); if (!c || !c.offsetWidth) return;
  const { x, w, h } = setupCanvas(c), cx = w / 2, cy = h / 2, R = Math.min(cx, cy) - 14, t0 = performance.now();
  (function f(t) {
    const p = RM ? 1 : Math.min((t - t0) / 1000, 1), e = 1 - Math.pow(1 - p, 3); x.clearRect(0, 0, w, h); let a = -Math.PI / 2;
    CATEGORY_SHARE.forEach(([, v], i) => { const s = v / 100 * 6.283 * e; x.strokeStyle = NEON[i]; x.lineWidth = 22; x.shadowBlur = 16; x.shadowColor = NEON[i]; x.beginPath(); x.arc(cx, cy, R - 11, a + .03, a + s - .03); x.stroke(); a += s; });
    if (p < 1) requestAnimationFrame(f);
  })(t0);
  $("#category-breakdown-legend").innerHTML = CATEGORY_SHARE.map(([n, v], i) => `<div><span><i style="background:${NEON[i]};box-shadow:0 0 8px ${NEON[i]}"></i>${n}</span><b>${v}%</b></div>`).join("");
}
function renderTopSkusTable() {
  $("#top-skus-table-body").innerHTML = [...PRODUCTS].sort((a, b) => b.price - a.price).slice(0, 5).map((p, i) => { const u = 180 - i * 28 + (p.sold || 0); return `<tr><td><b>#${i + 1}</b></td><td>${p.name}</td><td><code>${p.sku}</code></td><td>${p.category_name}</td><td>${u}</td><td>${inr(u * p.price)}</td><td><span class="pill ok">High velocity</span></td></tr>`; }).join("");
}
function renderAdmin() {
  const k = [["Gross platform revenue", 14285600 + revenueExtra, inr], ["Completed orders", 1842 + SHIPMENTS.length - 4, n => Math.round(n).toLocaleString("en-IN")], ["Fulfilment hubs", 3, n => Math.round(n) + " hubs"], ["Average fulfilment time", 14.6, n => n.toFixed(1) + " hrs"]];
  $("#kpi-grid").innerHTML = k.map(i => `<div class="panel kpi"><b>0</b><span>${i[0]}</span></div>`).join("");
  $$("#kpi-grid b").forEach((el, i) => countUp(el, k[i][1], k[i][2]));
  renderTopSkusTable(); drawOperationsTrendChart(); drawCategoryDonutChart();
}

// ============================================================================
// OUTBOX, TOASTS, MODALS, PORTALS
// ============================================================================
function renderOutbox() {
  $("#outbox-manifest-table-body").innerHTML = OUTBOX_LOGS.map(l => `<tr><td><code>${l.timestamp}</code></td><td>${l.type}</td><td>${l.to}</td><td>${l.subject}</td><td><span class="pill ok">${l.status}</span></td></tr>`).join("");
}
function showToast(msg, type = "info") {
  const t = document.createElement("div"); t.className = `toast ${type}`; t.textContent = msg; $("#toast-container").appendChild(t);
  setTimeout(() => { t.style.transition = "opacity .4s"; t.style.opacity = 0; setTimeout(() => t.remove(), 400); }, 2600);
}
const openModal = id => $("#" + id).classList.add("open");
const closeModal = id => $("#" + id).classList.remove("open");

function switchPortal(name) {
  currentPortal = name;
  $$(".nav[data-portal]").forEach(b => b.classList.toggle("on", b.dataset.portal === name));
  $$(".view").forEach(v => v.classList.toggle("on", v.id === `portal-${name}-view`));
  if (name === "manager") { renderHubInventory(); renderKanban(); }
  if (name === "admin") renderAdmin();
}

function initEventHandlers() {
  $("#customer-city-select").innerHTML = Object.keys(CITIES).map(c => `<option>${c}</option>`).join("");
  $("#customer-city-select").value = currentCustomerCity;
  $("#customer-city-select").onchange = e => { currentCustomerCity = e.target.value; renderProximityWidget(); if ($("#checkout-modal-backdrop").classList.contains("open")) renderGeodesicMap(); };
  $("#global-search-input").oninput = renderProducts;
  $$("#category-filter-pills .chip").forEach(b => b.onclick = () => { $$("#category-filter-pills .chip").forEach(x => x.classList.toggle("on", x === b)); currentCategoryFilter = b.dataset.category; renderProducts(); });
  $$(".nav[data-portal]").forEach(b => b.onclick = () => switchPortal(b.dataset.portal));
  $("#active-profile-select").onchange = e => {
    activeRole = e.target.value;
    const hubs = { MANAGER_BLR: 2, MANAGER_MAA: 1, MANAGER_BOM: 3 };
    if (hubs[activeRole]) { currentHubId = hubs[activeRole]; switchPortal("manager"); } else switchPortal(activeRole === "ADMIN" ? "admin" : "customer");
    showToast(`Profile switched: ${e.target.selectedOptions[0].text}`, "info");
  };
  ["open-cart-modal-btn", "sidebar-proceed-checkout-btn", "open-proximity-analytics-btn", "proximity-routing-summary-badge"].forEach(id => $("#" + id).onclick = openCheckoutModal);
  $("#close-checkout-modal-btn").onclick = () => closeModal("checkout-modal-backdrop");
  $("#clear-mini-cart-btn").onclick = () => { shoppingCart = []; renderMiniCart(); renderProximityWidget(); };
  $("#confirm-acid-order-btn").onclick = executeAcidCommit;
  $("#clear-telemetry-btn").onclick = () => { $("#acid-terminal-screen").innerHTML = ""; };
  $$("#payment-tabs .chip").forEach(b => b.onclick = () => { $$("#payment-tabs .chip").forEach(x => x.classList.toggle("on", x === b)); paymentMethod = b.dataset.m; renderPaymentBody(); });
  $("#open-outbox-btn").onclick = () => { renderOutbox(); openModal("outbox-modal-backdrop"); };
  $("#close-outbox-modal-btn").onclick = () => closeModal("outbox-modal-backdrop");
  $("#admin-broadcast-directive-btn").onclick = () => openModal("directive-modal-backdrop");
  ["close-directive-modal-btn", "cancel-directive-btn"].forEach(id => $("#" + id).onclick = () => closeModal("directive-modal-backdrop"));
  $("#send-directive-email-btn").onclick = () => {
    const to = $("#directive-recipient-select").value, pr = $("#directive-priority-select").value;
    OUTBOX_LOGS.unshift({ timestamp: nowStamp(), type: "ADMIN_DIRECTIVE", to: to === "ALL" ? "all hub managers" : to, subject: `[${pr}] ${$("#directive-subject-input").value}`, status: "DELIVERED" });
    closeModal("directive-modal-backdrop"); burst(innerWidth / 2, innerHeight / 2, 40, 1.4); showToast("Directive sent", "success");
  };
  $("#admin-download-pdf-btn").onclick = () => { showToast("Opening print dialog. Choose Save as PDF.", "info"); setTimeout(() => window.print(), 600); };
  $("#refresh-hub-inventory-btn").onclick = () => { renderHubInventory(); renderKanban(); showToast("Inventory synced", "success"); };
  $("#open-restock-modal-btn").onclick = () => { $("#restock-product-select").innerHTML = PRODUCTS.map(p => `<option value="${p.id}">${p.name} (${p.sku})</option>`).join(""); openModal("restock-modal-backdrop"); };
  ["close-restock-modal-btn", "cancel-restock-btn"].forEach(id => $("#" + id).onclick = () => closeModal("restock-modal-backdrop"));
  $("#confirm-restock-btn").onclick = () => {
    const p = PRODUCTS.find(x => x.id === +$("#restock-product-select").value), q = Math.max(1, +$("#restock-qty-input").value || 0);
    p.inventory[currentHubId] = (p.inventory[currentHubId] || 0) + q;
    OUTBOX_LOGS.unshift({ timestamp: nowStamp(), type: "HUB_RESTOCK_INTAKE", to: "admin@nexus.internal", subject: `Restock: +${q} × ${p.sku} (${$("#restock-supplier-input").value})`, status: "DELIVERED" });
    closeModal("restock-modal-backdrop"); renderHubInventory(); renderProducts(); renderProximityWidget(); showToast(`Restocked ${p.name} (+${q})`, "success");
  };
  $$(".modal-backdrop").forEach(m => m.addEventListener("mousedown", e => { if (e.target === m) m.classList.remove("open"); }));
  document.addEventListener("keydown", e => { if (e.key === "Escape") $$(".modal-backdrop.open").forEach(m => m.classList.remove("open")); });
  $("#title").onmouseenter = () => { $("#title").style.animation = "glitch .5s steps(2)"; setTimeout(() => $("#title").style.animation = "", 500); };
  document.addEventListener("click", e => {
    burst(e.clientX, e.clientY, 14);
    const b = e.target.closest(".btn,.chip,.cartbtn"); if (!b || RM) return;
    const r = b.getBoundingClientRect(), d = document.createElement("span"), m = Math.max(r.width, r.height);
    d.className = "rip"; d.style.cssText = `width:${m}px;height:${m}px;left:${e.clientX - r.left - m / 2}px;top:${e.clientY - r.top - m / 2}px`; b.appendChild(d); setTimeout(() => d.remove(), 600);
  });
  addEventListener("resize", () => { sizeCanvases(); if (currentPortal === "admin") { drawOperationsTrendChart(); drawCategoryDonutChart(); } });
}

window.addEventListener("DOMContentLoaded", () => {
  sizeCanvases(); if (!RM) fxLoop();
  initEventHandlers();
  renderProducts(); renderMiniCart(); renderProximityWidget(); renderHubInventory(); renderKanban();
  const enter = () => { if ($("#boot").classList.contains("off")) return; $("#boot").classList.add("off"); burst(innerWidth / 2, innerHeight / 2, 70, 1.8); };
  buildBootKeyboard(enter);
  $("#boot").onclick = enter; $("#boot-enter").onclick = enter; setTimeout(enter, 12000);
});


// ============================================================================
// BOOT SCREEN: 65% KEYBOARD ASSEMBLY WITH TYPING + CLICK SOUND
// ============================================================================
let audioCtx = null;
function thock(big) {
  try {
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    const o = audioCtx.createOscillator(), g = audioCtx.createGain(), t = audioCtx.currentTime;
    o.type = "triangle"; o.frequency.setValueAtTime(big ? 120 : 220, t); o.frequency.exponentialRampToValueAtTime(60, t + .08);
    g.gain.setValueAtTime(.25, t); g.gain.exponentialRampToValueAtTime(.001, t + .1);
    o.connect(g); g.connect(audioCtx.destination); o.start(t); o.stop(t + .12);
  } catch (e) { /* audio unavailable */ }
}
function buildBootKeyboard(enter) {
  const rows = [
    ["`","1","2","3","4","5","6","7","8","9","0","-","=","BKSP:2"],
    ["TAB:1.5","Q","W","E","R","T","Y","U","I","O","P","[","]","\\:1.5"],
    ["CAPS:1.75","A","S","D","F","G","H","J","K","L",";","'","ENTER:2.25"],
    ["SHIFT:2.25","Z","X","C","V","B","N","M",",",".","/","SHIFT:1.75","UP"],
    ["CTRL:1.25","WIN:1.25","ALT:1.25","SPACE:6.25","ALT","FN","LEFT","DOWN","RIGHT"]
  ];
  const kb = $("#kb"); let n = 0;
  kb.innerHTML = rows.map(r => `<div class="kr">${r.map(k => {
    const [label, w] = k.split(":"), special = label.length > 1 || label === "\\";
    return `<div class="k ${special ? "sp" : ""}" data-k="${label === "\\" ? "\\" : label}" style="--w:${w || 1};--dl:${(n++ * .035).toFixed(2)}s">${label.length > 2 ? "" : label}</div>`;
  }).join("")}</div>`).join("");
  const hit = el => { el.classList.add("hit"); setTimeout(() => el.classList.remove("hit"), 130); thock(el.dataset.k === "SPACE"); burst(el.getBoundingClientRect().left + 15, el.getBoundingClientRect().top, 8); };
  kb.addEventListener("click", e => { e.stopPropagation(); const k = e.target.closest(".k"); if (k) hit(k); });
  const map = { " ": "SPACE", Enter: "ENTER", Backspace: "BKSP", Tab: "TAB", Shift: "SHIFT", Control: "CTRL", Alt: "ALT", ArrowUp: "UP", ArrowDown: "DOWN", ArrowLeft: "LEFT", ArrowRight: "RIGHT", CapsLock: "CAPS" };
  document.addEventListener("keydown", e => {
    if ($("#boot").classList.contains("off")) return;
    if (e.key === "Enter") { enter(); return; }
    const key = map[e.key] || e.key.toUpperCase(), el = kb.querySelector(`.k[data-k="${CSS.escape(key)}"]`);
    if (el) { e.preventDefault(); hit(el); }
  });
}
