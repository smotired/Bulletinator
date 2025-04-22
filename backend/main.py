"""Bulletinator backend API application.

Args:
    app (FastAPI): The FastAPI application
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.dependencies import create_db_tables, cleanup_db
from backend.exceptions import BadRequestException
from backend.routers import boards, accounts, items, auth, media, reports
from backend.config import settings
from backend.utils.rate_limiter import limit

from os import path

# Set up the application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_tables()
    cleanup_db()
    yield

# Setup and start the application

description = """
Bulletinator is a project management and collaboration application. Accounts can
create bulletin boards and add and rearrange notes, images, and more to plan
out their projects and brainstorm development.
"""

app = FastAPI(
    lifespan=lifespan,
    title="Bulletinator API",
    summary="API for the Bulletinator App",
    description=description,
    version="0.1.0",
    contact={
        "name": "Sam Hill",
        # "url": "http://whatinthesamhill.dev", # i need a website
        "email": "sam@bulletinator.com",
    },
    license_info={
        "name": "GPL 3.0",
        "url": "https://www.gnu.org/licenses/gpl-3.0.en.html",
    },
)

# Set up all of the routers
for router in [ accounts.router, boards.router, items.router, auth.router, media.router, reports.router ]:
    app.include_router(router)

# Basic routes

@app.get("/status", status_code=200)
@limit("main")
def status():
    """Get current status of the API."""
    return { "message": "Hello World!" }

@app.get('/favicon.ico', include_in_schema=False)
@limit("forced")
async def favicon():
    return FileResponse(path.join(settings.assets_folder_path, 'favicon.ico'))

@app.exception_handler(BadRequestException)
def handle_error(request: Request, exc: BadRequestException):
    """Handle BadRequestExceptions."""
    return exc.response()

app.mount("/static", StaticFiles(directory="static"), name="static")

# DO NOT UNDER ANY CIRCUMSTANCES LET THIS ENTER PRODUCTION!!!!!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, including null (not safe for production)
    allow_methods=["*"],
    allow_headers=["*"],
)