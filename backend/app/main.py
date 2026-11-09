from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.routers import preflight, mandate, delegation, audit, checkout, dispute, merchant

app = FastAPI(title="MandateGuard API", version="1.0.0")

app.include_router(preflight.router)
app.include_router(mandate.router)
app.include_router(delegation.router)
app.include_router(audit.router)
app.include_router(checkout.router)
app.include_router(dispute.router)
app.include_router(merchant.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}