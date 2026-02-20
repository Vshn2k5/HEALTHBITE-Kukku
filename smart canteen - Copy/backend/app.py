"""
HealthBite Smart Canteen - Main Application Entry Point
========================================================
FastAPI backend server that powers the Smart Canteen system.
Serves both the API endpoints and the frontend static files.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from database import engine, Base
import os
import models

# Create all database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title="HealthBite Smart Canteen",
    description="AI-Powered Health-Aware Canteen System",
    version="2.0.0"
)

# CORS Middleware - Restrict origins in production
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response: Response = await call_next(request)
    # Basic Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https://images.unsplash.com; "
        "connect-src 'self';"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# --- Import and Register Routers ---
from auth import router as auth_router
from health import router as health_router
from menu import router as menu_router
from chatbot import router as chatbot_router
from analytics import router as analytics_router
from admin_analytics import router as admin_router

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(menu_router)
app.include_router(chatbot_router)
app.include_router(analytics_router)
app.include_router(admin_router)

# Print all registered routes for debugging
print("\n--- REGISTERED ROUTES ---")
for route in app.routes:
    if hasattr(route, "path"):
        print(f"{route.path} [{', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'}]")
print("------------------------\n")

# --- Serve Frontend Static Files ---
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

# Mount static files (CSS, JS, images, etc.)
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


@app.get("/")
async def serve_index():
    """Serve the main login/landing page"""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/{filename}.html")
async def serve_html(filename: str):
    """Serve any HTML page from the frontend directory"""
    filepath = os.path.join(FRONTEND_DIR, f"{filename}.html")
    if os.path.exists(filepath):
        return FileResponse(filepath)
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/{filename}.css")
async def serve_css(filename: str):
    """Serve CSS files"""
    filepath = os.path.join(FRONTEND_DIR, f"{filename}.css")
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="text/css")


@app.get("/{filename}.js")
async def serve_js(filename: str):
    """Serve JavaScript files"""
    filepath = os.path.join(FRONTEND_DIR, f"{filename}.js")
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="application/javascript")


@app.get("/images/{filename}")
async def serve_image(filename: str):
    """Serve image files"""
    filepath = os.path.join(FRONTEND_DIR, "images", filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)


# --- Start Server ---
if __name__ == "__main__":
    import uvicorn
    # Bind to 127.0.0.1 by default for security
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    print("=" * 50)
    print("  HEALTHBITE SMART CANTEEN SERVER")
    print(f"  Starting on http://{host}:{port}")
    print("=" * 50)
    uvicorn.run(app, host=host, port=port)
