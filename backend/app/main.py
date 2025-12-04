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


# KPI endpoint that reads from the materialized view `mv_ingestion_kpis`.
@app.get("/api/kpis")
def get_kpis():
    # Synchronous DB access using psycopg (psycopg3). This is a simple
    # implementation for the scaffold; in production consider async DB
    # access or connection pooling.
    from db.connection import get_database_url

    database_url = get_database_url()
    if not database_url:
        return {"error": "DATABASE_URL not configured"}

    try:
        import psycopg

        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM public.mv_ingestion_kpis LIMIT 1;")
                row = cur.fetchone()
                if row is None:
                    return {}
                cols = [desc.name for desc in cur.description]
                return dict(zip(cols, row))
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
