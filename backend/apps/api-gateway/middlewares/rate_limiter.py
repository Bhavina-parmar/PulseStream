from fastapi import Request, Response, status
from config.redis import redis_client

RATE_LIMIT_WINDOW=60
MAX_REQUESTS= 60

async def rate_limit_middleware(request:Request,call_next):
    client_ip=request.client.host
    redis_key= f"rate_limit:{client_ip}"

    try:
        current_request= await redis_client.incr(redis_key)
        if current_request==1:
            await redis_client.expire(redis_key, RATE_LIMIT_WINDOW)
        
        if current_request>MAX_REQUESTS:
            return Response(
                content="Too Many Requests:Rate limit exceeded. Try again later.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS
            )
    except Exception as e:
        print(f"Redis rate limit error: {e}")
        pass 
    response=await call_next(request)
    return response




