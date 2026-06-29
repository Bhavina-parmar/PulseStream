import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from controllers.health import router as health_router
from controllers.user_controller import router as user_router
from controllers.auth_controller import router as auth_router
from middlewares.rate_limiter import rate_limit_middleware
from controllers.event_controller import router as event_router
from controllers.analytics_controller import router as analytics_router

logger = logging.getLogger(__name__)

app=FastAPI()

app.middleware("http")(rate_limit_middleware)

app.include_router(health_router)
app.include_router(user_router)
app.include_router(auth_router)

app.include_router(analytics_router)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status":"error",
            "message": exc.detail 
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled system error occurred:{str(exc)}",exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status":"error",
            "message":"something went wrong"
        }
    )

app.include_router(event_router)