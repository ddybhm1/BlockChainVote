from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import FRONTEND_ORIGIN
from routers import auth, admin
from database import Base, engine
import models  # noqa: F401  # 确保模型被导入以注册到 metadata

app = FastAPI(title="BlockChainVote API", version="1.0.0", description="区块链电子投票系统后端")

# CORS - 仅允许前端源
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
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
