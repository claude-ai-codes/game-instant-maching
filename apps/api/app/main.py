import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.rate_limit import limiter
from app.routers import auth, blocks, recruitments, reports, rooms
from app.services.chat_cleanup import run_periodic_cleanup

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = asyncio.Event()
    task = asyncio.create_task(run_periodic_cleanup(stop_event))
    yield
    stop_event.set()
    task.cancel()


app = FastAPI(title="Game Instant Matching API", version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(recruitments.router)
app.include_router(rooms.router)
app.include_router(reports.router)
app.include_router(blocks.router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
