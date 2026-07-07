"""Make `backend` importable no matter which directory pytest is invoked from,
and provide a lightweight stub for the optional `cognee` SDK so the pure-logic
tests run without the full pipeline environment installed."""

import sys
import types
from pathlib import Path

# packages/ on the path so `import backend...` resolves.
_PACKAGES = Path(__file__).resolve().parents[2]
if str(_PACKAGES) not in sys.path:
    sys.path.insert(0, str(_PACKAGES))

# Stub `cognee` if it isn't installed — client.py imports it at module load.
if "cognee" not in sys.modules:
    try:
        import cognee  # noqa: F401
    except Exception:
        stub = types.ModuleType("cognee")
        stub.config = types.SimpleNamespace()
        sys.modules["cognee"] = stub
