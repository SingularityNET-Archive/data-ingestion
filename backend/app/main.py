from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file in project root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure structured logging
LOG_FORMAT = os.environ.get("LOG_FORMAT", "json").lower()
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

if LOG_FORMAT == "json":
    # JSON structured logging
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            if hasattr(record, "request_id"):
                log_data["request_id"] = record.request_id
            if hasattr(record, "user_id"):
                log_data["user_id"] = record.user_id
            return json.dumps(log_data)
    
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), handlers=[handler])
else:
    # Standard text logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

logger = logging.getLogger(__name__)

# Import API routers
from .api import kpis, alerts, meetings, exports, runs

app = FastAPI(title="Ingestion Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(kpis.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(meetings.router, prefix="/api")
app.include_router(exports.router, prefix="/api")
app.include_router(runs.router, prefix="/api")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/")
async def root():
    """Redirect browser requests to the interactive OpenAPI docs."""
    return RedirectResponse(url="/docs")


@app.get("/favicon.ico")
async def favicon():
    # Return empty response to avoid 404s in browser/dev logs
    return Response(status_code=204)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Application starting up")
    
    # Initialize DB pool on startup so endpoints can use it.
    # Skip initialization if DATABASE_URL is not set (common in tests)
    try:
        from .db.connection import get_database_url, init_db_pool
        
        if get_database_url():
            await init_db_pool()
            logger.info("Database connection pool initialized")
        else:
            logger.warning("DATABASE_URL not set - database features will be unavailable")
    except Exception as e:
        # Log initialization failures
        logger.error(f"Failed to initialize database pool: {str(e)}", exc_info=True)
    
    # Log available routes to assist with debugging
    try:
        routes = [getattr(r, 'path', str(r)) for r in app.routes if hasattr(r, 'path')]
        logger.info(f"Application started with {len(routes)} routes")
        logger.debug(f"Available routes: {', '.join(routes)}")
    except Exception as e:
        logger.warning(f"Failed to log routes: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Application shutting down")
    try:
        from .db.connection import close_db_pool
        await close_db_pool()
        logger.info("Database connection pool closed")
    except Exception as e:
        logger.warning(f"Error closing database pool: {str(e)}")



@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests with structured logging."""
    start_time = datetime.utcnow()
    request_id = os.urandom(8).hex()
    
    # Log request
    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
        }
    )
    
    try:
        response = await call_next(request)
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Log response
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }
        )
        
        return response
    except Exception as e:
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(
            "Request failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration_ms, 2),
                "error": str(e),
            },
            exc_info=True,
        )
        raise


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with structured error responses."""
    logger.warning(
        "HTTP exception",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "detail": exc.detail,
        }
    )
    
    # Provide a clearer 404 message to help debug missing endpoints.
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "status_code": 404,
                "detail": f"No route matches {request.url.path}. Try '/docs' for API docs or check available routes in server logs.",
            },
        )
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
