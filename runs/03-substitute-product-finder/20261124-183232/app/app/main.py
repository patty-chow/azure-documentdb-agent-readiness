"""FastAPI application entrypoint for the Product Substitute Finder sample.

This module configures the FastAPI app, connects to the database using a singleton Motor client
and Beanie ODM, and mounts routes and static assets.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from .config import settings
from .models import Product
from .routes import router


# Create FastAPI app and template/static mount points.
app = FastAPI(title="Product Substitute Finder (DocumentDB sample)")
app.include_router(router)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


async def _connect_to_db() -> None:
    """Create a singleton Motor client, verify the connection string and initialize Beanie.

    This function is awaited at startup to ensure the application fails fast with a
    helpful error message if DOCUMENTDB_URI is missing or cannot be used to connect.
    """

    # The settings loader already raised a clear error if DOCUMENTDB_URI is unset.
    mongo_uri = settings.DOCUMENTDB_URI

    # Create a single AsyncIOMotorClient for reuse across the process.
    # Motor/pymongo will manage connection pools internally.
    client = AsyncIOMotorClient(mongo_uri)

    try:
        # A lightweight ping to verify the connection works. MongoDB 'ping' command is cheap.
        await client.admin.command("ping")
    except Exception as e:
        # Convert low-level driver errors into a clearer message for the developer.
        raise RuntimeError(
            "Failed to connect to the DocumentDB cluster using DOCUMENTDB_URI. "
            "Please verify the connection string, network access, and firewall settings.\n"
            f"Underlying error: {e}"
        )

    # Initialize Beanie ODM with the Product document and the chosen database name.
    await init_beanie(database=client[settings.DB_NAME], document_models=[Product])


@app.on_event("startup")
async def startup_event() -> None:
    """FastAPI startup event handler.

    Connects to the DocumentDB cluster and prepares the Beanie models. If connection fails,
    the application will not start and the error will be raised for the user to inspect.
    """
    await _connect_to_db()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render a simple retailer-like home page that links to substitute functionality.

    The template displays a minimal product search box and example product links for demoing
    the substitute lookup.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    """A lightweight healthcheck endpoint used by deployment or test harnesses.

    Returns a simple JSON OK when the process is running. It does not probe the database.
    """
    return {"status": "ok"}
