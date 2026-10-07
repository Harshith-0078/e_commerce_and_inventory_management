"""
Nexus Peripherals - SMTP Email Notification Engine
Provides automated, asynchronous transactional email dispatches for:
1. Customer Order Confirmations & Line-Item Invoices
2. Customer Real-Time Shipment Tracking Status Transitions
3. Hub Manager New Order Routing Alerts
4. Hub Manager Low Stock Threshold Warnings
5. Admin -> Hub Manager Operational Directives & Broadcasts

Includes:
- HTML + Plaintext responsive email templates
- Background thread execution (zero UI blocking)
- Live SMTP dispatch with graceful fallback to Outbox Simulation Logger
- In-memory & disk outbox auditing
"""

import os
import smtplib
import ssl
import threading
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List, Tuple

# Configuration
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smtp_config.json")
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "email_notifications.log")

DEFAULT_SMTP_CONFIG = {
    "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "smtp_user": os.getenv("SMTP_USER", "notifications.nexusperipherals@gmail.com"),
    "smtp_password": os.getenv("SMTP_PASSWORD", ""),
    "sender_name": "Nexus Peripherals Automated Dispatch",
    "simulate_mode": os.getenv("SMTP_SIMULATE", "1") == "1",  # Defaults to simulation if no real credentials
}

OUTBOX_LOG: List[Dict[str, Any]] = []
_config_cache: Dict[str, Any] = DEFAULT_SMTP_CONFIG.copy()


def get_smtp_config() -> Dict[str, Any]:
    global _config_cache
    if not _config_cache.get("smtp_password"):
        _config_cache["simulate_mode"] = True
    return _config_cache.copy()


def update_smtp_config(new_config: Dict[str, Any]):
    global _config_cache
    _config_cache.update(new_config)
    if _config_cache.get("smtp_password"):
        _config_cache["simulate_mode"] = False


def _append_to_log(entry: Dict[str, Any]):
    OUTBOX_LOG.insert(0, entry)
    if len(OUTBOX_LOG) > 100:
        OUTBOX_LOG.pop()

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(
                f"[{entry['timestamp']}] "
                f"TYPE: {entry['type']} | TO: {entry['to']} | "
                f"SUBJECT: {entry['subject']} | "
                f"STATUS: {entry['status']} ({entry['mode']})\n"
            )
    except Exception:
        pass


def get_outbox_history(limit: int = 50) -> List[Dict[str, Any]]:
    return OUTBOX_LOG[:limit]


# -----------------------------------------------------------------------------
# CORE DISPATCH ROUTINE
# -----------------------------------------------------------------------------
def _dispatch_email_sync(
    recipient_email: str,
    subject: str,
    html_content: str,
    plain_content: str,
    email_type: str = "NOTIFICATION"
) -> Tuple[bool, str]:
    config = get_smtp_config()
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{config['sender_name']} <{config['smtp_user']}>"
    msg["To"] = recipient_email
    msg["Date"] = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0530")

    part1 = MIMEText(plain_content, "plain")
    part2 = MIMEText(html_content, "html")
    msg.attach(part1)
    msg.attach(part2)

    # Simulation / Dev Mode
    if config["simulate_mode"] or not config["smtp_password"]:
        log_entry = {
            "timestamp": timestamp_str,
            "type": email_type,
            "to": recipient_email,
            "subject": subject,
            "status": "DELIVERED (SIMULATED)",
            "mode": "Simulation/Sandbox Mode",
            "snippet": plain_content[:150] + "..."
        }
        _append_to_log(log_entry)
        return True, f"[Sandbox Outbox] Email successfully dispatched to {recipient_email}"

    # Live SMTP Dispatch
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(config["smtp_host"], config["smtp_port"], timeout=10) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(config["smtp_user"], config["smtp_password"])
            server.sendmail(config["smtp_user"], recipient_email, msg.as_string())

        log_entry = {
            "timestamp": timestamp_str,
            "type": email_type,
            "to": recipient_email,
            "subject": subject,
            "status": "SENT (LIVE SMTP)",
            "mode": f"Live SMTP ({config['smtp_host']})",
            "snippet": plain_content[:150] + "..."
        }
        _append_to_log(log_entry)
        return True, f"Live email successfully sent to {recipient_email}"

    except Exception as e:
        err_msg = str(e)
        # Graceful fallback to sandbox logging
        log_entry = {
            "timestamp": timestamp_str,
            "type": email_type,
            "to": recipient_email,
            "subject": subject,
            "status": f"FALLBACK_LOGGED (SMTP Error: {err_msg[:40]})",
            "mode": "Fallback Sandbox",
            "snippet": plain_content[:150] + "..."
        }
        _append_to_log(log_entry)
        return False, f"SMTP Connection Failed ({err_msg}). Dispatched to Outbox Log."


def dispatch_email_async(
    recipient_email: str,
    subject: str,
    html_content: str,
    plain_content: str,
    email_type: str = "NOTIFICATION"
):
    """Executes email dispatch in a background thread so UI never freezes."""
    thread = threading.Thread(
        target=_dispatch_email_sync,
        args=(recipient_email, subject, html_content, plain_content, email_type),
        daemon=True
    )
    thread.start()


# -----------------------------------------------------------------------------
# HIGH-LEVEL TRANSACTIONAL NOTIFICATION BUILDERS
# -----------------------------------------------------------------------------

def notify_customer_order_placed(
    customer_email: str,
    customer_name: str,
    order_id: int,
    total_amount: float,
    items: List[Dict[str, Any]],
    shipping_address: str,
    warehouse_name: str,
    tracking_number: str
):
    """
    Sends customer an itemized order confirmation and proximity fulfillment invoice.
    """
    subject = f"Order #{order_id} Confirmed! Nexus Peripherals Fulfillment Notice"

    # HTML Item rows
    rows_html = "".join([
        f"<tr>"
        f"<td style='padding:8px;border-bottom:1px solid #E5E7EB;'>{it.get('product_name', 'Item')}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #E5E7EB;text-align:center;'>{it.get('quantity', 1)}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #E5E7EB;text-align:right;'>₹{it.get('unit_price', 0):,.2f}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #E5E7EB;text-align:right;font-weight:bold;'>₹{it.get('subtotal', 0):,.2f}</td>"
        f"</tr>"
        for it in items
    ])

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;margin:0;padding:20px;background-color:#F3F4F6;color:#1F2937;">
      <div style="max-width:600px;margin:0 auto;background:#FFFFFF;border-radius:8px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.05);border:1px solid #E5E7EB;">
        <div style="background:#1E3A8A;padding:24px;text-align:center;color:#FFFFFF;">
          <h1 style="margin:0;font-size:22px;letter-spacing:1px;">NEXUS PERIPHERALS</h1>
          <p style="margin:4px 0 0;font-size:13px;color:#93C5FD;">Order Confirmation & Fulfillment Dispatch</p>
        </div>
        <div style="padding:24px;">
          <h2 style="color:#1E3A8A;margin-top:0;">Thank you for your order, {customer_name}!</h2>
          <p style="font-size:14px;color:#4B5563;">Your payment has been verified, and your order <strong>#{order_id}</strong> is now being processed at our nearest regional fulfillment hub.</p>
          
          <div style="background:#EFF6FF;border-left:4px solid #3B82F6;padding:12px 16px;margin:20px 0;border-radius:4px;">
            <p style="margin:0;font-size:13px;color:#1E40AF;"><strong>Assigned Fulfillment Facility:</strong> {warehouse_name}</p>
            <p style="margin:4px 0 0;font-size:13px;color:#1E40AF;"><strong>Tracking Identification:</strong> <span style="font-family:monospace;background:#DBEAFE;padding:2px 6px;border-radius:3px;">{tracking_number}</span></p>
            <p style="margin:4px 0 0;font-size:13px;color:#1E40AF;"><strong>Status:</strong> PREPARING FOR DISPATCH</p>
          </div>

          <h3 style="font-size:15px;color:#374151;border-bottom:2px solid #E5E7EB;padding-bottom:6px;">Itemized Manifest</h3>
          <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead>
              <tr style="background:#F9FAFB;color:#6B7280;text-align:left;">
                <th style="padding:8px;">Component</th>
                <th style="padding:8px;text-align:center;">Qty</th>
                <th style="padding:8px;text-align:right;">Unit Price</th>
                <th style="padding:8px;text-align:right;">Subtotal</th>
              </tr>
            </thead>
            <tbody>
              {rows_html}
            </tbody>
            <tfoot>
              <tr>
                <td colspan="3" style="padding:12px 8px;font-weight:bold;text-align:right;font-size:14px;">Grand Total Paid:</td>
                <td style="padding:12px 8px;font-weight:bold;text-align:right;font-size:16px;color:#059669;">₹{total_amount:,.2f}</td>
              </tr>
            </tfoot>
          </table>

          <div style="margin-top:20px;padding:12px;background:#F9FAFB;border-radius:4px;font-size:13px;color:#4B5563;">
            <strong>Shipping Destination:</strong><br>
            {shipping_address}
          </div>
        </div>
        <div style="background:#F9FAFB;padding:16px;text-align:center;font-size:12px;color:#9CA3AF;border-top:1px solid #E5E7EB;">
          Nexus Peripherals • BACSE202 Database Systems Architecture • Automated Notification System
        </div>
      </div>
    </body>
    </html>
    """

    items_plain = "\n".join([f"- {it.get('product_name', 'Item')} x {it.get('quantity', 1)}: ₹{it.get('subtotal', 0):,.2f}" for it in items])
    plain_content = (
        f"NEXUS PERIPHERALS - ORDER #{order_id} CONFIRMATION\n"
        f"===================================================\n"
        f"Customer: {customer_name}\n"
        f"Assigned Fulfillment Hub: {warehouse_name}\n"
        f"Tracking Number: {tracking_number}\n\n"
        f"Items:\n{items_plain}\n\n"
        f"Grand Total Paid: ₹{total_amount:,.2f}\n"
        f"Shipping Address: {shipping_address}\n"
        f"Status: PREPARING FOR DISPATCH\n"
    )

    dispatch_email_async(customer_email, subject, html_content, plain_content, email_type="CUSTOMER_ORDER_PLACED")


def notify_customer_shipment_updated(
    customer_email: str,
    customer_name: str,
    order_id: int,
    tracking_number: str,
    new_status: str,
    warehouse_name: str
):
    """
    Alerts customer of shipment delivery transitions (IN_TRANSIT -> OUT_FOR_DELIVERY -> DELIVERED).
    """
    subject = f"Shipment Update for Order #{order_id}: {new_status.replace('_', ' ')}"

    badge_color = "#3B82F6" if new_status in ["PREPARING", "IN_TRANSIT"] else ("#D97706" if new_status == "OUT_FOR_DELIVERY" else "#059669")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;margin:0;padding:20px;background-color:#F3F4F6;color:#1F2937;">
      <div style="max-width:550px;margin:0 auto;background:#FFFFFF;border-radius:8px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.05);border:1px solid #E5E7EB;">
        <div style="background:#1E3A8A;padding:20px;text-align:center;color:#FFFFFF;">
          <h2 style="margin:0;font-size:20px;">NEXUS PERIPHERALS</h2>
          <p style="margin:4px 0 0;font-size:12px;color:#93C5FD;">Live Shipment Tracking Notification</p>
        </div>
        <div style="padding:24px;">
          <p style="font-size:14px;color:#4B5563;">Hello <strong>{customer_name}</strong>,</p>
          <p style="font-size:14px;color:#4B5563;">There is a new update regarding your shipment for <strong>Order #{order_id}</strong>:</p>
          
          <div style="text-align:center;margin:24px 0;">
            <span style="background:{badge_color};color:#FFFFFF;padding:8px 18px;border-radius:20px;font-size:15px;font-weight:bold;letter-spacing:1px;">
              {new_status.replace('_', ' ')}
            </span>
          </div>

          <div style="background:#F9FAFB;padding:14px;border-radius:6px;font-size:13px;color:#374151;border:1px solid #E5E7EB;">
            <p style="margin:0 0 6px;"><strong>Tracking ID:</strong> <span style="font-family:monospace;">{tracking_number}</span></p>
            <p style="margin:0 0 6px;"><strong>Dispatched From:</strong> {warehouse_name}</p>
            <p style="margin:0;"><strong>Updated At:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}</p>
          </div>
        </div>
        <div style="background:#F9FAFB;padding:14px;text-align:center;font-size:12px;color:#9CA3AF;border-top:1px solid #E5E7EB;">
          Nexus Peripherals Logistics • Multi-Warehouse Automated Dispatch Engine
        </div>
      </div>
    </body>
    </html>
    """

    plain_content = (
        f"NEXUS PERIPHERALS - SHIPMENT STATUS UPDATE\n"
        f"==========================================\n"
        f"Order #{order_id} has updated to: {new_status}\n"
        f"Tracking Number: {tracking_number}\n"
        f"Origin Facility: {warehouse_name}\n"
        f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n"
    )

    dispatch_email_async(customer_email, subject, html_content, plain_content, email_type="SHIPMENT_STATUS_UPDATE")


def notify_hub_manager_new_order(
    manager_email: str,
    manager_name: str,
    warehouse_name: str,
    order_id: int,
    customer_name: str,
    destination_city: str,
    items: List[Dict[str, Any]],
    tracking_number: str
):
    """
    Notifies a Warehouse Manager that a customer cart has been routed to their hub for fulfillment.
    """
    subject = f"ACTION REQUIRED: New Order #{order_id} Routed to {warehouse_name}"

    items_list_html = "".join([f"<li><strong>{it.get('product_name', 'Item')}</strong> (Qty: {it.get('quantity', 1)})</li>" for it in items])

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;margin:0;padding:20px;background-color:#F3F4F6;color:#1F2937;">
      <div style="max-width:580px;margin:0 auto;background:#FFFFFF;border-radius:8px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.05);border:1px solid #E5E7EB;">
        <div style="background:#D97706;padding:20px;text-align:center;color:#FFFFFF;">
          <h2 style="margin:0;font-size:20px;">HUB OPERATIONS ALERT</h2>
          <p style="margin:4px 0 0;font-size:12px;color:#FEF3C7;">{warehouse_name} Incoming Dispatch Task</p>
        </div>
        <div style="padding:24px;">
          <p style="font-size:14px;color:#4B5563;">Attention Hub Manager <strong>{manager_name}</strong>,</p>
          <p style="font-size:14px;color:#4B5563;">A customer order has completed proximity evaluation and has been assigned to your warehouse for packing and dispatch:</p>
          
          <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:6px;padding:14px;margin:16px 0;">
            <p style="margin:0 0 6px;font-size:13px;color:#92400E;"><strong>Order ID:</strong> #{order_id}</p>
            <p style="margin:0 0 6px;font-size:13px;color:#92400E;"><strong>Recipient:</strong> {customer_name} ({destination_city})</p>
            <p style="margin:0;font-size:13px;color:#92400E;"><strong>Assigned Tracking Number:</strong> <span style="font-family:monospace;">{tracking_number}</span></p>
          </div>

          <h4 style="font-size:14px;margin:16px 0 8px;color:#374151;">Components to Pack:</h4>
          <ul style="font-size:13px;color:#4B5563;padding-left:20px;">
            {items_list_html}
          </ul>

          <p style="font-size:13px;color:#6B7280;margin-top:20px;">Please open the <strong>Hub Manager Operations</strong> portal in Nexus Peripherals to update the status to <code>IN_TRANSIT</code> upon carrier handover.</p>
        </div>
        <div style="background:#F9FAFB;padding:12px;text-align:center;font-size:12px;color:#9CA3AF;border-top:1px solid #E5E7EB;">
          Internal Staff Automated Message • Nexus Peripherals Inventory Network
        </div>
      </div>
    </body>
    </html>
    """

    plain_content = (
        f"HUB OPERATIONS ALERT - NEW ORDER #{order_id}\n"
        f"============================================\n"
        f"Warehouse Hub: {warehouse_name}\n"
        f"Manager: {manager_name}\n"
        f"Customer: {customer_name} ({destination_city})\n"
        f"Tracking Number: {tracking_number}\n\n"
        f"Items to Pack:\n"
        + "\n".join([f"- {it.get('product_name', 'Item')} x {it.get('quantity', 1)}" for it in items])
        + "\n\nPlease dispatch and update status in the Hub Manager portal.\n"
    )

    dispatch_email_async(manager_email, subject, html_content, plain_content, email_type="HUB_NEW_ORDER_ALERT")


def notify_hub_manager_low_stock(
    manager_email: str,
    manager_name: str,
    warehouse_name: str,
    product_name: str,
    sku: str,
    current_stock: int,
    reorder_level: int
):
    """
    Warns a Hub Manager that an inventory item has fallen below its reorder threshold.
    """
    subject = f"WARNING: Low Stock Threshold Reached at {warehouse_name} ({sku})"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;margin:0;padding:20px;background-color:#F3F4F6;color:#1F2937;">
      <div style="max-width:550px;margin:0 auto;background:#FFFFFF;border-radius:8px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.05);border:1px solid #E5E7EB;">
        <div style="background:#DC2626;padding:18px;text-align:center;color:#FFFFFF;">
          <h2 style="margin:0;font-size:19px;">INVENTORY REORDER WARNING</h2>
          <p style="margin:4px 0 0;font-size:12px;color:#FEE2E2;">{warehouse_name} Stock Depletion</p>
        </div>
        <div style="padding:22px;">
          <p style="font-size:14px;color:#4B5563;">Hello <strong>{manager_name}</strong>,</p>
          <p style="font-size:14px;color:#4B5563;">Stock for the following component has dropped below the safety replenishment threshold:</p>
          
          <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:6px;padding:14px;margin:16px 0;">
            <p style="margin:0 0 6px;font-size:13px;color:#991B1B;"><strong>Product:</strong> {product_name}</p>
            <p style="margin:0 0 6px;font-size:13px;color:#991B1B;"><strong>SKU:</strong> <span style="font-family:monospace;">{sku}</span></p>
            <p style="margin:0 0 6px;font-size:14px;color:#991B1B;"><strong>Current Units Available:</strong> <span style="font-weight:bold;font-size:16px;">{current_stock}</span></p>
            <p style="margin:0;font-size:13px;color:#991B1B;"><strong>Reorder Threshold:</strong> {reorder_level} units</p>
          </div>

          <p style="font-size:13px;color:#4B5563;">Immediate supplier intake is recommended to avoid proximity fallback routing to competing warehouses.</p>
        </div>
      </div>
    </body>
    </html>
    """

    plain_content = (
        f"INVENTORY REORDER WARNING - {warehouse_name}\n"
        f"============================================\n"
        f"Product: {product_name} ({sku})\n"
        f"Current Stock: {current_stock} units\n"
        f"Reorder Level: {reorder_level} units\n"
        f"Action: Please initiate restock batch.\n"
    )

    dispatch_email_async(manager_email, subject, html_content, plain_content, email_type="HUB_LOW_STOCK_WARNING")


def notify_admin_directive_to_manager(
    sender_admin_name: str,
    recipient_email: str,
    recipient_name: str,
    subject_line: str,
    directive_body: str,
    warehouse_name: Optional[str] = None
):
    """
    Sends an executive operational directive or broadcast from System Administrator to Hub Manager(s).
    """
    facility_tag = f" - {warehouse_name}" if warehouse_name else ""
    full_subject = f"[ADMIN DIRECTIVE{facility_tag}] {subject_line}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;margin:0;padding:20px;background-color:#F3F4F6;color:#1F2937;">
      <div style="max-width:600px;margin:0 auto;background:#FFFFFF;border-radius:8px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.05);border:1px solid #E5E7EB;">
        <div style="background:#1E3A8A;padding:20px;text-align:center;color:#FFFFFF;">
          <h2 style="margin:0;font-size:20px;">EXECUTIVE OPERATIONAL DIRECTIVE</h2>
          <p style="margin:4px 0 0;font-size:12px;color:#93C5FD;">From System Administration • Nexus Peripherals Network</p>
        </div>
        <div style="padding:24px;">
          <p style="font-size:14px;color:#374151;">To: <strong>{recipient_name}</strong> ({recipient_email})</p>
          <p style="font-size:14px;color:#374151;">From: <strong>{sender_admin_name}</strong> [System Administrator]</p>
          <hr style="border:none;border-top:1px solid #E5E7EB;margin:16px 0;">

          <h3 style="font-size:16px;color:#1E3A8A;margin-top:0;">{subject_line}</h3>
          
          <div style="background:#F9FAFB;border-left:4px solid #1E3A8A;padding:16px;border-radius:4px;font-size:14px;line-height:1.6;color:#1F2937;white-space:pre-wrap;">
{directive_body}
          </div>

          <p style="font-size:12px;color:#6B7280;margin-top:20px;">This message was dispatched directly from the Nexus Peripherals Administrator Portal with timestamp {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}.</p>
        </div>
        <div style="background:#F9FAFB;padding:12px;text-align:center;font-size:12px;color:#9CA3AF;border-top:1px solid #E5E7EB;">
          Confidential Operational Directive • System Admin Suite
        </div>
      </div>
    </body>
    </html>
    """

    plain_content = (
        f"EXECUTIVE OPERATIONAL DIRECTIVE\n"
        f"================================\n"
        f"From: {sender_admin_name} [System Administrator]\n"
        f"To: {recipient_name} ({recipient_email})\n"
        f"Subject: {subject_line}\n\n"
        f"Message:\n{directive_body}\n\n"
        f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n"
    )

    dispatch_email_async(recipient_email, full_subject, html_content, plain_content, email_type="ADMIN_DIRECTIVE")
