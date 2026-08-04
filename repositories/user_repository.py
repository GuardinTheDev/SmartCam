from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from domain.models import User, UserRole, UserStatus

class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_identifier(db: Session, identifier: str) -> Optional[User]:
        """Kullanıcıyı Kullanıcı Adı, E-Posta, Telefon veya Ad Soyad ile arar."""
        clean_id = identifier.strip().lower()
        return db.query(User).filter(
            or_(
                func.lower(User.username) == clean_id,
                func.lower(User.email) == clean_id,
                func.lower(User.phone) == clean_id,
                func.lower(User.full_name) == clean_id
            )
        ).first()

    @staticmethod
    def get_pending_users(db: Session) -> List[User]:
        """Onay bekleyen tüm kullanıcıları getirir."""
        return db.query(User).filter(User.status == UserStatus.PENDING).all()

    @staticmethod
    def create_user(db: Session, user_data, password_hash: str, role: UserRole, status: UserStatus) -> User:
        db_user = User(
            username=user_data.username,
            password_hash=password_hash,
            full_name=user_data.full_name,
            email=user_data.email,
            phone=user_data.phone,
            role=role,
            status=status,
            kvkk_approved=user_data.kvkk_approved
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update_status(db: Session, user_id: int, new_status: UserStatus) -> Optional[User]:
        user = UserRepository.get_by_id(db, user_id)
        if user:
            user.status = new_status
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def seed_initial_users(db: Session):
        """Veritabanında hiç kullanıcı yoksa varsayılan admin ve user hesaplarını oluşturur."""
        if db.query(User).count() == 0:
            from core.security import hash_password
            admin_user = User(
                username="admin",
                password_hash=hash_password("adminpassword123"),
                full_name="Sistem Yöneticisi",
                email="admin@smartcam.com",
                phone="05555555555",
                role=UserRole.ADMIN,
                status=UserStatus.APPROVED,
                kvkk_approved=True
            )
            test_user = User(
                username="user",
                password_hash=hash_password("userpassword123"),
                full_name="Test Kullanıcı",
                email="user@smartcam.com",
                phone="05444444444",
                role=UserRole.USER,
                status=UserStatus.APPROVED,
                kvkk_approved=True
            )
            db.add_all([admin_user, test_user])
            db.commit()