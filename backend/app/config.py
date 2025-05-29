import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./schedule.db")
ECHO = os.environ.get("ECHO", "False").lower() == "true"

SECRET_KEY = os.environ.get("SECRET_KEY", "YOUR_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

CACHE_DIR = "cache"  # Directory for cache files
CACHE_MAX_SIZE = 256    # Maximum number of items in cache
CACHE_TTL = 300          # Cache time-to-live in seconds
USER_AGENT = "ScheduleParserBot/1.0"   # User-Agent string