from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import settings
from app.core.logging import logger
from app.db.database import engine, Base
from app.api.routes_contracts import router as contracts_router
from app.api.routes_analysis import router as analysis_router
from app.api.routes_chat import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if not present
    logger.info("Initializing Legal Contract Analysis Engine...")
    Base.metadata.create_all(bind=engine)
    logger.info(f"Connected to Database: [green]{settings.DATABASE_URL}[/green]")
    logger.info(f"AI Provider Mode: [cyan]{settings.LLM_PROVIDER}[/cyan]")
    yield
    # Shutdown
    logger.info("Shutting down Legal Contract Analysis Engine.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade AI-powered Legal Contract Analysis and Due Diligence System",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local and web integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(contracts_router)
app.include_router(analysis_router)
app.include_router(chat_router)

# Mount Static UI Dashboard (supports bundled static or sibling frontend directory)
static_dir = Path(__file__).parent / "static"
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
active_ui_dir = static_dir if static_dir.exists() else (frontend_dir if frontend_dir.exists() else None)

if active_ui_dir:
    app.mount("/static", StaticFiles(directory=str(active_ui_dir)), name="static")
    # Also mount css and js directly for standalone frontend relative paths
    if (active_ui_dir / "css").exists():
        app.mount("/css", StaticFiles(directory=str(active_ui_dir / "css")), name="css")
    if (active_ui_dir / "js").exists():
        app.mount("/js", StaticFiles(directory=str(active_ui_dir / "js")), name="js")

@app.get("/", include_in_schema=False)
def serve_dashboard():
    """Serves the main LegalTech UI workbench."""
    if active_ui_dir:
        index_file = active_ui_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
    return {"message": "Legal Contract Analysis Engine API running. Visit /docs for Swagger API documentation."}

@app.get("/health", tags=["Health"])
def health_check():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "llm_provider": settings.LLM_PROVIDER,
        "environment": settings.APP_ENV
    }
