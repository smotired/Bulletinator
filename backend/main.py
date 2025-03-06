"""Bulletinator backend API application.

Args:
    app (FastAPI): The FastAPI application
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.dependencies import create_db_tables
from backend.exceptions import BadRequestException

# Set up the application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_tables()
    yield

# Start the application
app = FastAPI(
    title="Bulletinator API",
    summary="API for the Bulletinator App",
    lifespan=lifespan,
)

# Set up all of the routers

@app.get("/status", response_model=None, status_code=204)
def status():
    """Get current status of the API."""
    pass

@app.exception_handler(BadRequestException)
def handle_error(request: Request, exc: BadRequestException):
    """Handle BadRequestExceptions."""

    return exc.response()