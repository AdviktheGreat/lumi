"""Lumi API — FastAPI backend for the chat-first UI."""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import chat, sublabs

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("lumi")

app = FastAPI(title="Lumi API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(sublabs.router, prefix="/api")

PYMOL_OUTPUT = os.environ.get("LUMI_PYMOL_OUTPUT", os.path.join(os.getcwd(), "output", "pymol"))
os.makedirs(PYMOL_OUTPUT, exist_ok=True)
app.mount("/api/images", StaticFiles(directory=PYMOL_OUTPUT), name="images")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
