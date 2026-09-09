import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.overdue_worker import overdue_watch_loop
from app.routers import dashboard, tasks, users, ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    # En dev seulement : crée les tables si absentes. En prod, utiliser Alembic.
    await init_db()
    watcher = asyncio.create_task(overdue_watch_loop())
    yield
    watcher.cancel()


app = FastAPI(title="TaskBoard API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(dashboard.router)
app.include_router(ws.router)

app.mount("/dashboard", StaticFiles(directory="app/static/dashboard", html=True), name="dashboard")
app.mount("/admin", StaticFiles(directory="app/static/admin", html=True), name="admin")


@app.get("/health")
async def health():
    return {"status": "ok"}
