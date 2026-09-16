from app.core.config import settings
from app.db.session import engine
from fastapi import FastAPI
from sqlalchemy import text
from app.api.auth import router as auth_router
from app.api.users import router as users_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

app.include_router(auth_router)
app.include_router(users_router)


@app.get("/")
async def root():
    return {
        "message": "Enterprise Compliance Intelligence Platform API",
        "version": settings.APP_VERSION,
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/health/database")
async def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }
