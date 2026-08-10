import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from controllers.health import router as health_router
from controllers.user_controller import router as user_router
from controllers.auth_controller import router as auth_router
from middlewares.rate_limiter import rate_limit_middleware
from controllers.event_controller import router as event_router
from controllers.analytics_controller import router as analytics_router
from controllers.websocket_controller import router as websocket_router
from prometheus_fastapi_instrumentator import Instrumentator
from kafka.producer import stop_producer
from config.init_db import init_db
from config.logger import setup_logging, logger
from config.database import SessionLocal
from services.auth_service import cleanup_expired_tokens
from websocket import redis_subscriber

setup_logging()
logger.info("Application starting up...")

CLEANUP_INTERVAL_SECONDS = 86400 

async def perodic_token_cleanup():
    while True:
        try:
            with SessionLocal() as db:
                cleanup_expired_tokens(db=db)
        except Exception as e:
            logger.warning(f"Error during scheduled token cleanup: {e}")

        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    subscriber_task = asyncio.create_task(redis_subscriber())
    cleanup_task = asyncio.create_task(perodic_token_cleanup()) 
    yield
    subscriber_task.cancel()
    cleanup_task.cancel()
    try:
        await asyncio.gather(subscriber_task, cleanup_task, return_exceptions= True)
    except Exception as e:
        logger.warning(f"Error while stopping background tasks: {e}")

    await stop_producer()



app = FastAPI(
    lifespan=lifespan,
    title="PulseStream API Gateway",
    description=("**Event-driven high-throughput API Gateway.**\n\n"
                "This service provides interfaces for user account generation, ingestion of "
                "system telemetry analytics, live data monitoring over streaming WebSockets, "
                "and granular system dependency checking. "
                ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "PulseStream Platform Engineers",
        "email": "dev-support@pulsestream.io",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

Instrumentator().instrument(app).expose(app)
app.middleware("http")(rate_limit_middleware)

app.include_router(health_router)
app.include_router(websocket_router)

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(user_router)
v1_router.include_router(auth_router)
v1_router.include_router(event_router)
v1_router.include_router(analytics_router)

app.include_router(v1_router)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled system error occurred:{str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": "error", "message": "something went wrong"}
    )
