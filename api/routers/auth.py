from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from domain.schemas import UserCreate, UserLogin, AdminUserAction
from services.auth_service import AuthService
from repositories.user_repository import UserRepository

router = APIRouter(prefix="/api", tags=["Auth & Admin"])

@router.post("/auth/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    user = AuthService.register(db, user_data)
    return {"message": "Kayıt başarılı, yönetici onayına gönderildi.", "user_id": user.id}

@router.post("/auth/login")
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    return AuthService.login(db, login_data)

@router.get("/admin/pending-users")
def get_pending_users(db: Session = Depends(get_db)):
    return UserRepository.get_pending_users(db)

@router.post("/admin/approve-user")
def approve_or_reject_user(action_data: AdminUserAction, db: Session = Depends(get_db)):
    return AuthService.process_admin_action(db, action_data.user_id, action_data.action)
