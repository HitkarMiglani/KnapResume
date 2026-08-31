from fastapi import FastAPI

from app.routers import auth, profile

app = FastAPI(title="KnapResume API")

app.include_router(auth.router)
app.include_router(profile.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
