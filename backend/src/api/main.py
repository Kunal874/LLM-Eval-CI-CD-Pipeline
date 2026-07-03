"""FastAPI application entry point — wires routers and middleware."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import runs, results, cases, health

app = FastAPI(title="LLM Eval API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production if needed
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(runs.router, prefix="/api/v1")
app.include_router(results.router, prefix="/api/v1")
app.include_router(cases.router, prefix="/api/v1")
