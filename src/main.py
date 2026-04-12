from fastapi import FastAPI
from src.core.database import engine, Base

app = FastAPI(title="AI 面试器", version="0.1.0")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}
