import os


# load config from env variables
BOOTSTRAP_SERVERS = os.environ.get("BOOTSTRAP_SERVER", "kafka:9092")
SENTRY_DSN = os.environ.get("SENTRY_DSN", False)
BEHIND_PROXY = os.environ.get("BEHIND_PROXY", False)
METRICS = os.environ.get("METRICS", False)
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_KEY = os.environ.get("JWT_KEY", "sekrit")
JWT_PREFIX = os.environ.get("JWT_PREFIX", "Bearer")
JWT_USER_FIELD = os.environ.get("JWT_USERNAME_FIELD", "username")
DEBUG = os.environ.get("DEBUG", False) == "True"

