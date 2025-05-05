from fastapi import APIRouter
# from app.endpoints import user
from .auth import router as auth_router
from .chatbot import router as chat_router

router = APIRouter()
# router.include_router(user.router, prefix='/users', tags=['Users'])

router.include_router(auth_router, prefix="/auth")
router.include_router(chat_router, prefix="/chat")