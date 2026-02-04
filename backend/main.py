from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from backend.middleware.rate_limiter import limiter
from backend.core.database import get_db
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os

# Import API routers
from backend.api.auth_routes import router as auth_router
from backend.api.self_coding_routes import router as self_coding_router
from backend.api.v1.chat import router as chat_v1_router
from backend.api.v1.auditor import router as auditor_v1_router
from backend.api.v1.formulas import router as formulas_v1_router
from backend.api.v1.schedule_analysis import router as schedule_v1_router
from backend.api.v1.audio_analysis import router as audio_v1_router
from backend.api.v1.archive_analysis import router as archive_v1_router
from backend.api.v1.cad_analysis import router as cad_v1_router
from backend.api.v1.pdf_analysis import router as pdf_v1_router

app = FastAPI(title="Blank App - Unified UI+API")

# Rate limiting middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(status_code=429, content={"detail": "Too Many Requests"}))

# Global error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # log exception here if desired
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
# CORS - Allow all origins for public access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for public access
    allow_credentials=False,  # Changed to False for security with public access
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(self_coding_router, prefix="/api/self-coding", tags=["Self-Coding"])
app.include_router(formulas_v1_router, prefix="/api/v1", tags=["Formulas"])
app.include_router(chat_v1_router, prefix="/api/v1", tags=["Chat"])
app.include_router(auditor_v1_router, prefix="/api/v1/auditor", tags=["Auditor"])
app.include_router(schedule_v1_router, prefix="/api/v1", tags=["Schedule"])
app.include_router(audio_v1_router, prefix="/api/v1", tags=["Audio"])
app.include_router(archive_v1_router, prefix="/api/v1", tags=["Archive"])
app.include_router(cad_v1_router, prefix="/api/v1", tags=["CAD"])
app.include_router(pdf_v1_router, prefix="/api/v1", tags=["PDF"])

# Paths: this file sits at backend/app, so climb to backend/
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST_PATH", str(FRONTEND_DIST)))

# Ensure health is always available and defined before any SPA mounting
@app.get("/health")
async def health():
    return {"status": "ok"}

# Liveness and readiness probes
@app.get("/livez", include_in_schema=False)
async def livez():
    return {"status": "live"}

@app.get("/readyz", include_in_schema=False)
async def readyz(db=Depends(get_db)):
    return {"status": "ready"}
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    # Mount only the static assets directory so it won't shadow API routes
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists() and assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Serve index.html for the root
    @app.get("/", include_in_schema=False)
    async def _index():
        return FileResponse(FRONTEND_DIST / "index.html")

    # Catch-all for SPA routes but avoid catching API or asset/health paths
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_catch_all(full_path: str):
        # Prevent catching API or asset paths
        if full_path.startswith("api") or full_path.startswith("assets") or full_path == "health":
            raise HTTPException(status_code=404)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    async def root():
        return JSONResponse(
            {"status": "backend", "message": "Frontend not found. Build the frontend and include frontend/dist in the deployment."},
            status_code=200,
        )
