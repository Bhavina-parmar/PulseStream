from fastapi import Request, status
from fastapi.responses import JSONResponse
from config.redis import redis_client
from config.logger import logger 

RATE_LIMIT_WINDOW=60
MAX_REQUESTS= 1000

async def rate_limit_middleware(request:Request,call_next):
    if request.url.path == "/ws" or request.headers.get("upgrade") == "websocket":
        return await call_next(request)

    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    redis_key= f"rate_limit:{client_ip}"

    try:
        current_request= await redis_client.incr(redis_key)
        if current_request==1:
            await redis_client.expire(redis_key, RATE_LIMIT_WINDOW)
        
        if current_request>MAX_REQUESTS:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error" : "Too Many Requests",
                    "detail" : "Rate limit exceeded. Try again later."
                }
            )
    except Exception as e:
        logger.warning(f"Redis rate limit error: {e}")
        pass 
    response=await call_next(request)
    return response




