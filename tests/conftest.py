import os

# Ensure JWT env vars exist for imports (security.py reads env at import time)
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ALG", "HS256")
os.environ.setdefault("JWT_ISS", "auth-service")
os.environ.setdefault("JWT_AUD", "dpd-app")
