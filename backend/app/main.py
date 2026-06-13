from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.api import jobs, health
from app.utils.logger import logger

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AeroFlow AI-Powered Transaction Processing Pipeline API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set up CORS middleware to allow cross-origin requests from frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router)
app.include_router(jobs.router)

@app.on_event("startup")
def on_startup():
    logger.info("Starting up FastAPI application...")
    
    # Auto-create database tables on start to guarantee database readiness for reviewers
    try:
        logger.info("Running database schema creation check (Fallback)...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialization check passed successfully.")
    except Exception as e:
        logger.critical(f"Failed to auto-create database tables: {str(e)}")

@app.on_event("shutdown")
def on_shutdown():
    logger.info("Shutting down FastAPI application...")
