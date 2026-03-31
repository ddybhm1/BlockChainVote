from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from web3 import Web3

from config import FRONTEND_ORIGIN
from database import Base, engine
from routers import admin, auth
from services.realtime import vote_stream_manager
from services.schema import ensure_runtime_schema
import models  # noqa: F401

app = FastAPI(
    title="BlockChainVote API",
    version="1.0.0",
    description="Blockchain voting backend API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)


@app.on_event("startup")
async def startup_create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_runtime_schema()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/elections/{election_address}/votes")
async def vote_stream(websocket: WebSocket, election_address: str):
    if not Web3.is_address(election_address):
        await websocket.close(code=1008, reason="Invalid election address")
        return

    normalized_address = Web3.to_checksum_address(election_address)

    try:
        await vote_stream_manager.connect(normalized_address, websocket)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await vote_stream_manager.disconnect(normalized_address, websocket)
