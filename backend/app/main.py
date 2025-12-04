from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Ingestion Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    # Initialize DB pool on startup so endpoints can use it.
    try:
        from db.connection import init_db_pool

        await init_db_pool()
    except Exception as e:
        print(f"Warning: DB pool initialization failed on startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    try:
        from db.connection import close_db_pool

        await close_db_pool()
    except Exception:
        pass


@app.get("/api/kpis")
async def get_kpis():
    """Async KPI endpoint that reads from the materialized view `mv_ingestion_kpis`.

    Returns a single-row mapping of KPI columns to values. The endpoint uses
    an asyncpg pool for efficient connections.
    """
    from db.connection import get_database_url, get_db_pool

    database_url = get_database_url()
    if not database_url:
        return {"error": "DATABASE_URL not configured"}

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM public.mv_ingestion_kpis LIMIT 1;")
            if row is None:
                return {}
            # asyncpg Record is mappable to dict
            return dict(row)
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
