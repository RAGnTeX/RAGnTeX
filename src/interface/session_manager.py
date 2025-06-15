"""Session Manager Module"""

import threading
import time
import uuid
from functools import wraps
from typing import Any, Callable

from ..database import clean_db
from ..telemetry.logging_utils import Logger
from .manage_files import delete_files

LOGGER = Logger.get_logger()


# Global session manager
session_data = {}


def create_session(timeout=600) -> str:
    """Create a new session and return its ID.
    This function generates a unique session ID, initializes the session data
    with the current timestamp, and starts a background thread to monitor
    the session for inactivity. If the session is inactive for a specified
    timeout period, it will be automatically cleaned up.

    Returns:
        str: The unique session ID.
    """

    # Create new session
    session_id = str(uuid.uuid4())
    session_data[session_id] = {
        "last_active": time.time(),
    }
    LOGGER.info("🪪 Created new session with ID: %s", session_id)

    # Start clean-up watcher
    threading.Thread(
        target=watch_session, args=(session_id, timeout), daemon=True
    ).start()

    return session_id


def watch_session(session_id, timeout=600) -> None:
    """Clean up if no activity for `timeout` seconds.
    This function runs in a separate thread and checks if the session
    is still active. If the session has not been active for the specified
    timeout period, it deletes the session data.

    Args:
        session_id (str): The ID of the session to watch.
        timeout (int): The time in seconds after which the session is considered inactive.
    """

    while True:
        time.sleep(30)
        session = session_data.get(session_id)
        if not session:
            break
        if time.time() - session["last_active"] > timeout:
            LOGGER.info("🕒 Session expired, ID: %s", session_id)
            del session_data[session_id]
            time.sleep(10)
            delete_files(session_id)
            clean_db(session_id)
            LOGGER.info("🧹 Deleted session with ID: %s", session_id)
            break


def update_session(session_id) -> None:
    """Update the last active time for a session.
    This function checks if the session ID exists in the session data
    and updates its last active timestamp.

    Args:
        session_id (str): The ID of the session to update.
    """

    if session_id in session_data:
        session_data[session_id]["last_active"] = time.time()


def with_update_session(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to update session activity.
    This decorator checks if the session ID is provided in the arguments
    and updates the session's last active time.

    Args:
        fn (callable): The function to wrap.

    Returns:
        callable: The wrapped function that updates the session activity.
    """

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
    """Check if a session is active or expired.
    This function checks if the provided session ID exists in the session data.
    If it exists, the session is considered active; otherwise, it is expired.

    Args:
        session_id (str): The ID of the session to check.

    Returns:
        str: "active" if the session is active, "expired" if it is not.
    """
    return "active" if session_id in session_data else "expired"
