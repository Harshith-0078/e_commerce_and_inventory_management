"""
Nexus Peripherals - Backward-Compatibility Entrypoint
Redirects to frontend.app so that running `python src/app.py` works seamlessly.
"""
import os
import sys

# Add root, frontend, and db_integration to sys.path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(repo_root, "frontend")
db_integration_dir = os.path.join(repo_root, "db_integration")

for p in [repo_root, frontend_dir, db_integration_dir]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

try:
    from frontend.app import NexusPeripheralsApp
except ImportError:
    from app import NexusPeripheralsApp

if __name__ == "__main__":
    app = NexusPeripheralsApp()
    app.mainloop()
