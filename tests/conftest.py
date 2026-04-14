"""Test fixtures and utilities."""

import sys
from pathlib import Path
from typing import Dict, Any

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
