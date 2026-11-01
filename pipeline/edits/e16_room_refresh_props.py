"""Edit #16 (integration, Sakina approved 2026-11-01): room refresh, ONLY the lamp, remote and calculator.

Not used from components/room_refresh (not approved or superseded): window (e14 wins), curtains and poster
(round3 curtains win), notebook (existing notebook stays). Wraps components/room_refresh/apply.py with PARTS limited.
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARTS = "lamp,remote,calculator"


def apply():
    here = os.path.join(ROOT, "components", "room_refresh")
    if here not in sys.path:
        sys.path.insert(0, here)
    os.environ["PARTS"] = PARTS
    import apply as room_refresh_apply            # components/room_refresh/apply.py
    room_refresh_apply.apply()
    print("e16: room refresh parts applied:", PARTS, flush=True)
