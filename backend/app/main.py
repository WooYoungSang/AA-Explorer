from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import paymasters, smart_accounts, stats, userops

app = FastAPI(title="Base AA Explorer API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(userops.router, prefix="/api/userops", tags=["userops"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(paymasters.router, prefix="/api/paymasters", tags=["paymasters"])
app.include_router(smart_accounts.router, prefix="/api/smart-accounts", tags=["smart-accounts"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "chain": "base", "entrypoint": "v0.7"}
