from fastapi import FastAPI
from app.routers import preflight, mandate, delegation, audit

app = FastAPI(title="MandateGuard API", version="0.1.0")

app.include_router(preflight.router)
app.include_router(mandate.router)
app.include_router(delegation.router)
app.include_router(audit.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}