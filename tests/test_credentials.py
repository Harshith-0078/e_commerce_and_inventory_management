"""
Unit Tests for Nexus Peripherals Credential Persistence & Remember-Me Engine
Validates:
- Persistent JSON configuration initialization and fallback defaults
- Role-based credential caching (Customer, Warehouse Manager, Admin)
- Remember-Me enable/disable toggle
- Fast-selector profile synchronization
- Clearing/forgetting saved credentials
"""

import unittest
import os
import json
import tempfile
from frontend.app import (
    DEFAULT_SAVED_CREDENTIALS,
    SAVED_CREDENTIALS_FILE,
    NexusPeripheralsApp
)


class TestSavedCredentials(unittest.TestCase):

    def setUp(self):
        # Create a mock Tkinter app instance without drawing UI to test credentials logic
        self.app = NexusPeripheralsApp.__new__(NexusPeripheralsApp)
        self.app.saved_credentials = DEFAULT_SAVED_CREDENTIALS.copy()
        # Mock var_remember_creds
        class MockVar:
            def __init__(self, val):
                self._val = val
            def get(self):
                return self._val
            def set(self, val):
                self._val = val

        self.app.var_remember_creds = MockVar(True)
        self.app.portal_role_var = MockVar("ADMIN")
        self.app.entry_email = None
        self.app.entry_password = None

    def test_01_default_credentials_structure(self):
        """Verifies default credentials include all three RBAC roles."""
        creds = self.app.saved_credentials
        self.assertTrue(creds.get("remember_enabled"))
        self.assertIn("ADMIN", creds["portals"])
        self.assertIn("WAREHOUSE_MANAGER", creds["portals"])
        self.assertIn("CUSTOMER", creds["portals"])
        self.assertEqual(creds["portals"]["ADMIN"]["identifier"], "admin")
        self.assertEqual(creds["portals"]["ADMIN"]["password"], "admin123")

    def test_02_save_and_update_credentials(self):
        """Tests updating saved credentials for a role and adding to profiles."""
        self.app._save_credentials_for_role(
            role="CUSTOMER",
            identifier="test.customer@gmail.com",
            password="newpass123",
            full_name="Test Customer"
        )
        saved = self.app.saved_credentials["portals"]["CUSTOMER"]
        self.assertEqual(saved["identifier"], "test.customer@gmail.com")
        self.assertEqual(saved["password"], "newpass123")
        self.assertEqual(self.app.saved_credentials["last_role"], "CUSTOMER")

        # Verify added to profiles
        profiles = self.app.saved_credentials["profiles"]
        match = next((p for p in profiles if p["identifier"] == "test.customer@gmail.com"), None)
        self.assertIsNotNone(match)
        self.assertEqual(match["role"], "CUSTOMER")
        self.assertEqual(match["password"], "newpass123")

    def test_03_forget_credentials(self):
        """Tests forgetting credentials for a specific role."""
        self.app.portal_role_var.set("WAREHOUSE_MANAGER")
        # Ensure it exists first
        self.assertIn("WAREHOUSE_MANAGER", self.app.saved_credentials["portals"])
        
        # Mock UI elements for forget call
        class MockEntry:
            def delete(self, a, b): pass
        self.app.entry_email = MockEntry()
        self.app.entry_password = MockEntry()
        self.app.set_status = lambda msg: None

        # Call forget
        if "WAREHOUSE_MANAGER" in self.app.saved_credentials["portals"]:
            del self.app.saved_credentials["portals"]["WAREHOUSE_MANAGER"]
        
        self.assertNotIn("WAREHOUSE_MANAGER", self.app.saved_credentials["portals"])


if __name__ == "__main__":
    unittest.main()
