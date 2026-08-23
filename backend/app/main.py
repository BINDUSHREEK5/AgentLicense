"""Main FastAPI application for AgentLicense."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import settings
from app.db.database import init_db, cleanup_db, SessionLocal
from app.api import health, resources, licenses, protected, purchase
from app.api.resources import _ensure_demo_resources

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AgentLicense",
    description="Machine-Readable Rights for Autonomous Commerce",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "PAYMENT-REQUIRED",
        "PAYMENT-RESPONSE",
    ],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"],
)


# Startup event
@app.on_event("startup")
def startup_event():
    """Initialize database and log startup info."""
    logger.info("Starting AgentLicense server...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug: {settings.debug}")
    logger.info(f"Database: {settings.database_url}")
    logger.info(f"Algorand Network: {settings.algorand_network}")
    logger.info(f"x402 Facilitator: {settings.x402_facilitator_url}")
    logger.info(f"AVM_ADDRESS configured: {bool(settings.avm_address)}")

    if not settings.avm_address:
        logger.warning(
            "AVM_ADDRESS is not set - real x402 purchase routes "
            "(/x402/purchase/*) will return 503 until configured. "
            "See backend/.env.example."
        )

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Seed demo resources unconditionally, regardless of which endpoint is
    # hit first (previously this only happened lazily inside /resources
    # handlers, which meant /resources/{id}/access could 404 on a fresh
    # database if it was the first request).
    seed_db = SessionLocal()
    try:
        _ensure_demo_resources(seed_db)
        logger.info("Demo resources seeded")
    finally:
        seed_db.close()


# Shutdown event
@app.on_event("shutdown")
def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down AgentLicense server...")
    cleanup_db()


# Register routers
app.include_router(health.router)
app.include_router(resources.router)
app.include_router(licenses.router)
app.include_router(protected.router)
app.include_router(purchase.router)


# Root endpoint
@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "name": "AgentLicense",
        "version": "1.0.0",
        "tagline": "Machine-Readable Rights for Autonomous Commerce",
        "status": "running",
        "environment": settings.app_env,
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "endpoints": {
            "health": "/health",
            "resources": "/resources",
            "licenses": "/licenses",
            "real_x402_purchase": "/x402/purchase/{tier}",
            "x402_status": "/x402/status",
            "protected_access": "/resources/{resource_id}/access",
        },
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc) if settings.debug else "See logs for details",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
    )