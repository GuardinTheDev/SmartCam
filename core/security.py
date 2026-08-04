import re
import hashlib

def hash_password(password: str) -> str:
    """Şifreyi SHA-256 + Salt ile güvenli şekilde hash'ler."""
    salt = "smartcam_secure_salt_2026"
    return hashlib.sha256(f"{salt}{password}".encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Girilen düz metin şifre ile hash'lenmiş şifreyi karşılaştırır."""
    return hash_password(plain_password) == hashed_password

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Şifre Güvenlik Politikası:
    - En az 6 karakter
    - Basit/Tahmin edilebilir şifreler yasak (ad123, smartcam123 vb.)
    - Hem harf hem rakam içermeli
    """
    if len(password) < 6:
        return False, "Şifre en az 6 karakter uzunluğunda olmalıdır."

    weak_passwords = ["123456", "ad123", "password", "smartcam123", "admin123", "qwerty"]
    if password.lower() in weak_passwords:
        return False, "Şifreniz çok basit! Lütfen 'ad123' veya '123456' gibi kolay tahmin edilebilir şifreler kullanmayın."

    if not re.search(r"[a-zA-Z]", password):
        return False, "Şifre en az bir harf içermelidir."

    if not re.search(r"\d", password):
        return False, "Şifre en az bir rakam içermelidir."

    return True, "Şifre geçerli."
