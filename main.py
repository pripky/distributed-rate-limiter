import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from limiter import DistributedTokenBucket

app = FastAPI(title="Distributed Rate Limiter Service")

# Initialize the limiter module
rate_limiter = DistributedTokenBucket(redis_host="localhost", redis_port=6379)

# Simulated configuration engine values (Dynamically reloadable at runtime)
DYNAMIC_LIMITS = {
    "default_rate": 5,      # 5 tokens per second
    "default_capacity": 10  # Burst capacity of 10 tokens
}

@app.get("/v1/config/reload")
async def reload_config():
    """Engine endpoint to simulate dynamic loading without service downtime."""
    # In production, this would query a database to reload parameters
    DYNAMIC_LIMITS["default_rate"] = 10 
    return {"status": "success", "message": "Rate limits reloaded dynamically"}

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    # Track client identification based on request headers or IP
    client_id = request.client.host
    
    # Evaluate token bucket state
    rate = DYNAMIC_LIMITS["default_rate"]
    capacity = DYNAMIC_LIMITS["default_capacity"]
    
    if not rate_limiter.is_allowed(client_id, rate, capacity):
        raise HTTPException(status_code=429, detail="Too Many Requests - Throttled")
        
    response = await call_next(request)
    return response

@app.get("/api/resource")
async def protected_endpoint():
    return {"status": "success", "data": "Protected microservice content accessed"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
