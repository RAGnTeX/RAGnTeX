import uuid
import time
import threading
from functools import wraps
from ..telemetry.logging_utils import Logger

LOGGER = Logger.get_logger()


# Global session manager
session_data = {}

def create_session(timeout=600) -> str:
    """Create a new session and return its ID."""

    # Create new session
    session_id = str(uuid.uuid4())
    session_data[session_id] = {
        "last_active": time.time(),
    }
    LOGGER.info("🪪 Created new session with ID: %s", session_id)

    # Start clean-up watcher
    threading.Thread(target=watch_session, args=(session_id, timeout), daemon=True).start()

    return session_id

def watch_session(session_id, timeout=600):
    """Clean up if no activity for `timeout` seconds."""

    while True:
        time.sleep(30)
        session = session_data.get(session_id)
        if not session:
            break
        if time.time() - session["last_active"] > timeout:
            del session_data[session_id]
            LOGGER.info("🧹 Deleted session with ID: %s", session_id)
            # Whatever will be deleted later, we could delay it a little bit
            break

def update_session(session_id):
    if session_id in session_data:
        print(f"Updating activity for session ID: {session_id}")
        session_data[session_id]["last_active"] = time.time()

def with_update_session(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            session_id = kwargs.get("session_id")
            if session_id is None and args:
                session_id = args[-1]
            if session_id in session_data:
                update_session(session_id)
        except Exception as e:
            LOGGER.error("❌ Failed to upadate session ID: %s", session_id, exc_info=e)
        return fn(*args, **kwargs)
    return wrapper

def check_session_status(session_id: str) -> str:
    return "active" if session_id in session_data else "expired"