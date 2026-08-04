from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from domain.models import UserRole, UserStatus
from domain.schemas import UserCreate, UserLogin
from repositories.user_repository import UserRepository
from core.security import hash_password, verify_password, validate_password_strength

class AuthService:
    @staticmethod
    def register(db: Session, user_data: UserCreate):
        UserRepository.seed_initial_users(db)
        # 1. Şifre Güvenlik Kontrolü
        is_valid, msg = validate_password_strength(user_data.password)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

        # 2. Kullanıcı Var Mı Kontrolü
        existing_user = UserRepository.get_by_identifier(db, user_data.username)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu kullanıcı adı zaten alınmış.")

        # 3. İlk Kullanıcı Otomatik ADMIN Olur, Sonrakiler PENDING
        user_count = db.query(UserRepository.get_by_id.__self__.User).count() if hasattr(UserRepository, 'User') else 0
        
        # Basit mantık: Eğer ilk kayıt ise admin & approved, yoksa user & pending
        role = UserRole.ADMIN if user_count == 0 else UserRole.USER
        status_val = UserStatus.APPROVED if user_count == 0 else UserStatus.PENDING

        hashed_pwd = hash_password(user_data.password)
        return UserRepository.create_user(db, user_data, hashed_pwd, role, status_val)

    @staticmethod
    def login(db: Session, login_data: UserLogin):
        UserRepository.seed_initial_users(db)
        user = UserRepository.get_by_identifier(db, login_data.username)
        if not user or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Hatalı kullanıcı bilgisi veya şifre!")

        if user.status == UserStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hesabınız henüz yönetici tarafından onaylanmamış.")
        elif user.status == UserStatus.REJECTED:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hesap başvurunuz reddedilmiştir.")

        return {"message": "Giriş başarılı", "username": user.username, "role": user.role.value}

    @staticmethod
    def process_admin_action(db: Session, user_id: int, action: str):
        new_status = UserStatus.APPROVED if action == "approve" else UserStatus.REJECTED
        updated = UserRepository.update_status(db, user_id, new_status)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı.")
        return {"message": f"Kullanıcı {action} işlemi tamamlandı.", "user_id": user_id}
