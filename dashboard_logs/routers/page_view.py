from fastapi import APIRouter
from models.schemas import LogPageView
import motor.motor_asyncio

router = APIRouter(prefix="/logs/page_view")

client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://mongodb:27017")
db = client["intranet_logs"]
collection = db["logs"]

@router.post("/")
async def log_page_view(entry: LogPageView):
    await collection.insert_one(entry.model_dump())
    return {"message": "Log de page view enregistré"}