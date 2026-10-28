"""RobinHood AI - shared HTTP security (rate limiting) primitives."""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# A single limiter is created here and initialised against the app in app.py so
# that both the auth blueprint and the main routes can decorate with @limiter.limit.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://",
)
