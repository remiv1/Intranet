from fastapi import APIRouter
from models.schemas import LogLogout
import motor.motor_asyncio

router = APIRouter(prefix="/logs/logout")

client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://mongodb:27017")
db = client["intranet_logs"]
collection = db["logs"]

@router.post("/")
async def log_logout(entry: LogLogout):
    await collection.insert_one(entry.model_dump())
    return {"message": "Log de logout enregistré"}