from fastapi import FastAPI

from app.routers import auth, job_descriptions, profile, profile_imports

app = FastAPI(title="KnapResume API")

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(profile_imports.router)
app.include_router(job_descriptions.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
