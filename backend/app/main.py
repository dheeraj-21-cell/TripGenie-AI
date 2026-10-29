import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.endpoints import router as api_router

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("tripgenie.main")

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TripGenie-AI Backend: High-speed personalized travel itinerary planner API.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware for local Vite frontend
logger.info(f"Configuring CORS for origins: {settings.CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/", tags=["System"])
def root():
    """Root entry point providing API metadata and documentation links."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "health_url": f"{settings.API_PREFIX}/health"
    }

# Also expose direct /health for standard probes
@app.get("/health", tags=["System"])
def direct_health():
    """Convenience alias for /api/health."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "groq_configured": settings.is_groq_available
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
