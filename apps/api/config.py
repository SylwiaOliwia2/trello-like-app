import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://app:app@db:5432/appdb"
)

JWT_SECRET = "dev-secret-not-for-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://web:5173",
]

MFA_ISSUER_NAME = "task-manager-app"
