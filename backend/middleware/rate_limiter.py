"""
Rate limiting utilities for the Blank App.

This module sets up a global rate limiter using SlowAPI.  The
``limiter`` object is attached to the FastAPI application state in
``main.py``.  Use the ``@limiter.limit`` decorator on routes to
enforce per-endpoint rate limits.  See SlowAPI documentation for
advanced configuration options.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialise a Limiter that keys off the client's IP address.  You
# can customise the key function to use API keys or user IDs instead.
limiter = Limiter(key_func=get_remote_address)