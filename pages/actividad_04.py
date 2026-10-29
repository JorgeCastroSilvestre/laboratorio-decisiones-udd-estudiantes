from importlib import reload
from pathlib import Path
import sys

PORTAL_ROOT = Path(__file__).resolve().parents[1]
if str(PORTAL_ROOT) not in sys.path:
    sys.path.insert(0, str(PORTAL_ROOT))
import portal_common

# Streamlit Cloud can keep imported modules in memory after a Git update.
# Reloading here ensures students always receive the latest public renderer.
portal_common = reload(portal_common)
portal_common.render_activity(4)
