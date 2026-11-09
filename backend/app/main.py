from fastapi import FastAPI
from app.routers import preflight

app = FastAPI(title="MandateGuard API", version="0.1.0")

app.include_router(preflight.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}