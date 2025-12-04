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


# Simple example KPI endpoint for scaffold
@app.get("/api/kpis")
async def get_kpis():
    # Placeholder implementation — real implementation will query materialised views
    return {
        "total_ingested": 0,
        "sources_count": 0,
        "success_rate": 100.0,
        "duplicates_avoided": 0,
        "last_run_timestamp": None,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
