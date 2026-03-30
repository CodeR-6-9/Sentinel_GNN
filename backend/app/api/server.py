from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import analyze as analyze_router


app = FastAPI(
    title="Sentinel-GNN API",
    description="Antimicrobial Resistance Prediction & Discovery via Graph Neural Networks",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    analyze_router.router,
    prefix="/api/analyze",
    tags=["Analysis"]
)


@app.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint to verify API is running.
    
    Returns:
        Status message indicating the API is operational.
    """
    return {"status": "Sentinel-GNN API is running"}