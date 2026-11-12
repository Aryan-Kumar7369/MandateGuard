from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import preflight, mandate, delegation, audit, checkout, dispute, merchant, events, webauthn, red_team, demo

app = FastAPI(title="MandateGuard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(preflight.router)
app.include_router(mandate.router)
app.include_router(delegation.router)
app.include_router(audit.router)
app.include_router(checkout.router)
app.include_router(dispute.router)
app.include_router(merchant.router)
app.include_router(events.router)
app.include_router(webauthn.router)
app.include_router(red_team.router)
app.include_router(demo.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
