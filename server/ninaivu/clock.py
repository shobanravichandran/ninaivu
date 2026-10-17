"""Demo clock. The UI's "+7 days" button shifts time so cross-session memory can be shown live."""
import time

DAY = 86_400


def now(offset_days: float = 0) -> int:
    """Epoch seconds, shifted by the demo offset."""
    return int(time.time() + offset_days * DAY)
