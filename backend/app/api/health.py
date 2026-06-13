from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
from app.core.database import get_db
from app.core.config import settings
from app.utils.logger import logger

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check(response: Response, db: Session = Depends(get_db)):
    """Health check endpoint checking connection state to Postgres and Redis databases."""
    db_status = "down"
    redis_status = "down"
    
    # 1. Check PostgreSQL
    try:
        db.execute(text("SELECT 1"))
        db_status = "up"
    except Exception as e:
        logger.error(f"Health check PostgreSQL error: {str(e)}")
        
    # 2. Check Redis
    try:
        r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=1)
        r.ping()
        redis_status = "up"
    except Exception as e:
        logger.error(f"Health check Redis error: {str(e)}")
        
    # Determine status
    if db_status == "up" and redis_status == "up":
        response.status_code = status.HTTP_200_OK
        overall_status = "healthy"
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "unhealthy"
        
    return {
        "status": overall_status,
        "api": "up",
        "postgres": db_status,
        "redis": redis_status
    }
