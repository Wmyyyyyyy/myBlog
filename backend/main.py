from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.redis import close_redis
from apps.users.views import router as users_router
from apps.blogs.router import router as blogs_router
from apps.foundation.router import router as foundation_router
from apps.comments.router import router as comments_router
from apps.interactions.router import router as interactions_router
from apps.dynamics.router import router as dynamics_router
from apps.admin.router import router as admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(users_router)
app.include_router(blogs_router)
app.include_router(foundation_router)
app.include_router(comments_router)
app.include_router(interactions_router)
app.include_router(dynamics_router)
app.include_router(admin_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
