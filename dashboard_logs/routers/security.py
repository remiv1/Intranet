from fastapi import APIRouter
from models.schemas import ChangeSecurity
import motor.motor_asyncio

router = APIRouter(prefix="/logs/change_security")

client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://mongodb:27017")
db = client["intranet_logs"]
collection = db["logs"]

@router.post("/")
async def log_change_security(entry: ChangeSecurity):
    await collection.insert_one(entry.model_dump())
    return {"message": "Log de changement de sécurité enregistré"}