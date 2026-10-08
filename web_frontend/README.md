# Nexus Peripherals - Modern Web Frontend

A decoupled, zero-build web frontend for Nexus Peripherals featuring dark glassmorphic styling, real-time Haversine proximity routing, an ACID transaction simulation console, a Hub Manager Kanban fulfillment pipeline, and an interactive Executive EDA analytics suite.

## Status

**UNCOMMITTED DRAFT FOR TEAM REVIEW**: This entire directory (`web_frontend/`) has been created as an independent, uncommitted workspace to allow team review, UX testing, and architecture alignment with Vikas and Saidharan before pushing to the repository.

---

## Architecture Overview

This frontend is architected with zero external npm build dependencies. It runs directly in any modern browser without requiring `npm install`, Node.js compilation, or bundling steps:

- **HTML Structure**: `index.html` (Semantic, accessible SPA layout with role-based portal switching)
- **Styling**: `styles.css` (Custom CSS properties, glassmorphism `backdrop-filter: blur(16px)`, radial glowing gradients, responsive CSS Grid / Flexbox)
- **Logic & State Engine**: `app.js` (Reactive client state, Haversine routing engine, MySQL ACID transaction simulation, HTML5 Canvas charts, modal controllers)

---

## Directory Structure

```
web_frontend/
├── index.html        # Main SPA interface (Storefront, Hub Ops, Admin EDA, and Modals)
├── styles.css        # Obsidian/cyan/indigo design tokens, components, and animations
├── app.js            # Mock catalog, geocoordinates, cart engine, canvas EDA charts, SMTP telemetry
└── README.md         # Team onboarding and integration documentation
```

---

## Features Implemented

### 1. Customer Storefront
- Dynamic keyboard catalog with filtering by category (Flagship Mechanical, Wireless Compact, Tenkeyless, Mac / Creator).
- Customer location selector (Vellore, Bengaluru, Chennai, Mumbai, Hyderabad, Delhi, Pune, Kolkata).
- Haversine Geodesic Distance Matrix: Computes line-of-sight distance against warehouses in Bengaluru (`WH-BLR-01`), Chennai (`WH-MAA-01`), and Mumbai (`WH-BOM-01`).
- Optimal warehouse routing determination based on 100% item stock fulfillment and shortest distance.
- Reactive cart drawer with real-time tax calculation (18% GST) and live checkout trigger.

### 2. Live Proximity Checkout & ACID Transaction Console
- Full-screen checkout modal displaying geodetic radar routing details and customer delivery address.
- Interactive transaction inspector simulating MySQL row-level locks (`SELECT ... FOR UPDATE`), inventory deductions across fulfillment bins, order creation, payment gateway verification, and shipment record generation with custom tracking IDs (`TRK-NEXUS-...`).
- Live terminal feed showing exact transaction timing, isolation level (`REPEATABLE READ`), and commit confirmations.

### 3. Hub Manager Operations Portal
- Hub selector (`WH-BLR-01`, `WH-MAA-01`, `WH-BOM-01`) showing warehouse supervisor details, latitude/longitude, and active utilization.
- Real-time stock matrix with color-coded inventory health indicators and quick restock intake modal.
- 4-column fulfillment pipeline (`Preparing`, `In Transit`, `Out for Delivery`, `Delivered`).
- One-click shipment stage progression with automated trigger of SMTP notification telemetry.

### 4. System Administrator Suite & EDA Analytics
- High-level KPI metrics (Gross Revenue, Active Hubs, Pipeline Volume, Inventory Health).
- Dual-axis operational analytics chart drawn using native HTML5 Canvas (Monthly Sales Revenue vs. Intake Units).
- Category revenue distribution donut chart with interactive hover arcs.
- Top SKU velocity ranking with unit volumes, revenue contribution, and hub availability metrics.
- Admin directive composer to broadcast operational notices to hub managers.
- SMTP telemetry inspector displaying outbox history, dispatch timestamps, and message payloads.

---

## How to Run Locally

You can run this frontend using any of the following methods:

### Method A: Direct Browser Opening
Double-click `web_frontend/index.html` in your file explorer, or right-click and choose **Open with Browser** (Chrome, Edge, Firefox, Brave, Safari).

### Method B: Python Local Server (Recommended)
From the project root:
```bash
python -m http.server 3000 --directory web_frontend
```
Then navigate to `http://localhost:3000` in your web browser.

### Method C: VS Code Live Server
If using VS Code or Antigravity IDE, right-click `web_frontend/index.html` and select **Open with Live Server**.

---

## Design System Tokens

The frontend uses the exact palette and aesthetic defined in the team mockups:

| Token | Value | Purpose |
|---|---|---|
| `--bg-app` | `#080C14` | Primary deep space background |
| `--bg-surface` | `rgba(15, 23, 42, 0.75)` | Glassmorphic surface with backdrop blur |
| `--accent-cyan` | `#06B6D4` | Primary interactive glow and highlight |
| `--accent-indigo` | `#6366F1` | Secondary gradient accent |
| `--status-emerald` | `#10B981` | Success states, delivered orders, in-stock badges |
| `--status-amber` | `#F59E0B` | In-transit shipments and low stock warnings |
| `--font-main` | `'Plus Jakarta Sans', sans-serif` | Clean geometric UI typography |
| `--font-mono` | `'JetBrains Mono', monospace` | ACID terminal logs and tracking numbers |

---

## Integration with Backend (Python / MySQL)

When ready to integrate with the Python backend (`src/`):

1. **Routing Endpoint**: Connect `app.js` proximity calculation to `POST /api/v1/routing/calculate` using `src/services/routing_service.py`.
2. **Order Creation**: Map `handleCheckoutSubmit()` to `POST /api/v1/orders` handled by `src/services/order_service.py` to execute atomic DB transactions.
3. **Analytics API**: Replace client-side mock monthly data in `renderTrendChart()` with `GET /api/v1/analytics/monthly-trends` powered by `src/services/eda_service.py`.
4. **SMTP Dispatch**: Forward shipment stage transitions directly to `src/services/smtp_service.py`.
