from fastapi import FastAPI
from app.routes.user_routes import router as user_router

app = FastAPI(
    title="MyCompliance API",
    description="Backend API for MyCompliance",
    version="1.0.0",
)

app.include_router(user_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "Welcome to MyCompliance API"}
