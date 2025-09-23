import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from alembic import command
from alembic.config import Config

PROJECT_ABSOLUTE_PATH = Path(os.path.dirname(os.path.abspath(__file__))).parent


templates = Jinja2Templates(directory=PROJECT_ABSOLUTE_PATH / "templates")


def app_init() -> FastAPI:
    app = FastAPI()
    app.mount(
        "/static",
        StaticFiles(directory=PROJECT_ABSOLUTE_PATH / "static"),
        name="static",
    )
    app.mount(
        "/js",
        StaticFiles(directory=PROJECT_ABSOLUTE_PATH / "static/react-components/build"),
        name="static",
    )

    return app


app = app_init()


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})
