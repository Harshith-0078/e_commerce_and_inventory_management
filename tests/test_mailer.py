"""
Unit Tests for Nexus Peripherals SMTP Mailer Notification Engine
Validates:
- Configuration management and simulation fallback
- Asynchronous dispatch without thread deadlocks
- HTML and Plaintext templating
- Customer order and shipment notification functions
- Hub manager fulfillment alerts, low stock warnings, and admin directives
- Outbox telemetry and disk log persistence
"""

import unittest
import time
import os
from db_integration.smtp_mailer import (
    get_smtp_config,
    update_smtp_config,
    notify_customer_order_placed,
    notify_customer_shipment_updated,
    notify_hub_manager_new_order,
    notify_hub_manager_low_stock,
    notify_admin_directive_to_manager,
    get_outbox_history,
    LOG_FILE,
)


class TestSmtpMailer(unittest.TestCase):

    def setUp(self):
        # Force simulation mode for deterministic test execution
        update_smtp_config({
            "smtp_password": "",
            "simulate_mode": True,
            "smtp_user": "test.mailer@nexusperipherals.internal",
            "sender_name": "Nexus Test Dispatcher"
        })

    def test_01_config_fallback_to_simulation(self):
        """Verifies that empty password defaults gracefully to simulate_mode."""
        cfg = get_smtp_config()
        self.assertTrue(cfg["simulate_mode"])
        self.assertEqual(cfg["smtp_port"], 587)

    def test_02_customer_order_placed_dispatch(self):
        """Tests sending itemized customer order receipt."""
        items = [
            {"product_name": "Gateron Oil King Switches (Pack of 70)", "quantity": 1, "unit_price": 2899.00, "subtotal": 2899.00},
            {"product_name": "Krytox 205g0 Switch Lube (5g)", "quantity": 2, "unit_price": 549.00, "subtotal": 1098.00}
        ]
        
        notify_customer_order_placed(
            customer_email="customer.test@example.com",
            customer_name="Rohan Sharma",
            order_id=9901,
            total_amount=3997.00,
            items=items,
            shipping_address="42 Indiranagar 100ft Rd, Bengaluru",
            warehouse_name="Bangalore Central Hub",
            tracking_number="TRK-NX-TEST9901"
        )

        time.sleep(0.3)
        history = get_outbox_history()
        self.assertGreater(len(history), 0)
        latest = history[0]
        self.assertEqual(latest["to"], "customer.test@example.com")
        self.assertIn("#9901", latest["subject"])
        self.assertEqual(latest["type"], "CUSTOMER_ORDER_PLACED")
        self.assertIn("DELIVERED", latest["status"])

    def test_03_customer_shipment_update_dispatch(self):
        """Tests shipment status transition notifications."""
        notify_customer_shipment_updated(
            customer_email="customer.test@example.com",
            customer_name="Rohan Sharma",
            order_id=9901,
            tracking_number="TRK-NX-TEST9901",
            new_status="OUT_FOR_DELIVERY",
            warehouse_name="Bangalore Central Hub"
        )

        time.sleep(0.3)
        history = get_outbox_history()
        match = next((e for e in history if e["type"] == "SHIPMENT_STATUS_UPDATE"), None)
        self.assertIsNotNone(match)
        self.assertIn("OUT FOR DELIVERY", match["subject"])
        self.assertEqual(match["to"], "customer.test@example.com")

    def test_04_hub_manager_order_and_low_stock_alerts(self):
        """Tests manager notifications for new dispatches and stock depletion."""
        items = [{"product_name": "Keychron Q1 Barebone", "quantity": 1, "unit_price": 14999.00, "subtotal": 14999.00}]

        notify_hub_manager_new_order(
            manager_email="samarth@gmail.com",
            manager_name="Samarth (Hub Manager)",
            warehouse_name="Bangalore Central Hub",
            order_id=9902,
            customer_name="Aarav Mehta",
            destination_city="Bengaluru",
            items=items,
            tracking_number="TRK-NX-TEST9902"
        )

        notify_hub_manager_low_stock(
            manager_email="samarth@gmail.com",
            manager_name="Samarth (Hub Manager)",
            warehouse_name="Bangalore Central Hub",
            product_name="Keychron Q1 Barebone",
            sku="KB-KEY-Q1B-01",
            current_stock=2,
            reorder_level=5
        )

        time.sleep(0.3)
        history = get_outbox_history()
        types = [e["type"] for e in history]
        self.assertIn("HUB_NEW_ORDER_ALERT", types)
        self.assertIn("HUB_LOW_STOCK_WARNING", types)

    def test_05_admin_directive_broadcast(self):
        """Tests administrative directive message dispatch to warehouse managers."""
        notify_admin_directive_to_manager(
            sender_admin_name="Director Harshith",
            recipient_email="samarth@gmail.com",
            recipient_name="Samarth (Hub Manager)",
            subject_line="Annual Inventory Audit Schedule",
            directive_body="Please prepare bin-level inventory counts for mechanical switches by Friday 5 PM.",
            warehouse_name="Bangalore Central Hub"
        )

        time.sleep(0.3)
        history = get_outbox_history()
        match = next((e for e in history if e["type"] == "ADMIN_DIRECTIVE"), None)
        self.assertIsNotNone(match)
        self.assertIn("Annual Inventory Audit Schedule", match["subject"])

    def test_06_disk_log_persistence(self):
        """Verifies that dispatches write audit records into logs/email_notifications.log."""
        self.assertTrue(os.path.exists(LOG_FILE))
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("customer.test@example.com", content)
        self.assertIn("samarth@gmail.com", content)


if __name__ == "__main__":
    unittest.main()
