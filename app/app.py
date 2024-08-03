from uuid import uuid4
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.main import routes
from app.main.settings import Settings, settings
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI

def get_app() -> FastAPI:
  app = FastAPI(
    description="FH2024", version="0.0.1",
  )
  return app

background_tasks = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create the background task set
    yield
    # Shutdown: wait for all background tasks to complete
    if background_tasks:
        await asyncio.gather(*background_tasks)

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(routes.router)

# if we need more routes: 

# app.include_router(generator_routes.router)
# app.include_router(image_routes.router)
settings = Settings()  

@app.get("/", response_class=HTMLResponse, tags=["Usage"])
@app.get("/usage", response_class=HTMLResponse)
async def usage():
  return """<html>
  Founders hack 2024 baby
  </html>
  """
