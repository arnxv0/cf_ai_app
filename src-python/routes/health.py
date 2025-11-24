from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])

# This will be set by main.py
ARROW_BACKEND_AVAILABLE = False


@router.get("/")
async def root():
    return {
        "name": "Arrow Backend",
        "version": "1.0.0",
        "status": "running",
        "arrow_backend_available": ARROW_BACKEND_AVAILABLE
    }


@router.get("/health")
async def health():
    return {"status": "healthy", "arrow_backend_available": ARROW_BACKEND_AVAILABLE}
