"""Bulletinator backend API application.

Args:
    app (FastAPI): The FastAPI application
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse

from backend.dependencies import create_db_tables
from backend.exceptions import BadRequestException
from backend.routers import boards, users, items, auth
from backend.config import settings

# Set up the application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_tables()
    yield

# Setup and start the application

description = """
Bulletinator is a project management and collaboration application. Users can
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
        "email": "smotired@gmail.com",
    },
    license_info={
        "name": "GPL 3.0",
        "url": "https://www.gnu.org/licenses/gpl-3.0.en.html",
    },
)

# Set up all of the routers
for router in [ users.router, boards.router, items.router, auth.router ]:
    app.include_router(router)

# Basic routes

@app.get("/status", status_code=200)
def status():
    """Get current status of the API."""
    return { "message": "Hello World!" }


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(settings.favicon_path)

@app.exception_handler(BadRequestException)
def handle_error(request: Request, exc: BadRequestException):
    """Handle BadRequestExceptions."""

    return exc.response()