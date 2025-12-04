from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import os

# Import API routers
from api import kpis, alerts, meetings, exports, runs

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
    # Initialize DB pool on startup so endpoints can use it.
    try:
        from db.connection import init_db_pool

        await init_db_pool()
    except Exception as e:
        print(f"Warning: DB pool initialization failed on startup: {e}")
    # Print available routes to assist with debugging 404s
    try:
        print("Available routes:")
        for r in app.routes:
            print(f"  {getattr(r, 'path', str(r))}")
    except Exception:
        pass


@app.on_event("shutdown")
async def shutdown_event():
    try:
        from db.connection import close_db_pool

        await close_db_pool()
    except Exception:
        pass



@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
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
