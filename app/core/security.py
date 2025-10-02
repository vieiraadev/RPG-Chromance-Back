import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from fastapi import HTTPException, status
import secrets
import re
from email_validator import validate_email, EmailNotValidError

SECRET_KEY = secrets.token_urlsafe(32)  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440 
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12 
)

class SecurityService:
    """Serviço de segurança com validações avançadas"""
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """Valida força da senha"""
        if len(password) < 6: 
            raise HTTPException(
                status_code=400, 
                detail="Senha deve ter pelo menos 6 caracteres"
            )
        
        has_letters = bool(re.search(r"[a-zA-Z]", password))
        has_numbers = bool(re.search(r"\d", password))
        
        if not (has_letters or has_numbers):
            raise HTTPException(
                status_code=400, 
                detail="Senha deve conter pelo menos letras ou números"
            )
        
        return True
    
    @staticmethod
    def validate_email_format(email: str) -> str:
        """Valida e normaliza email"""
        try:
            validated_email = validate_email(email)
            return validated_email.email.lower()
        except EmailNotValidError:
            raise HTTPException(
                status_code=400, 
                detail="Formato de email inválido"
            )
    
    @staticmethod
    def validate_name(nome: str) -> str:
        """Valida nome do usuário"""
        nome = nome.strip()
        if len(nome) < 2:
            raise HTTPException(
                status_code=400, 
                detail="Nome deve ter pelo menos 2 caracteres"
            )
        if len(nome) > 100:
            raise HTTPException(
                status_code=400, 
                detail="Nome não pode ter mais de 100 caracteres"
            )
        return nome

def get_password_hash(password: str) -> str:
    """Gera hash da senha com validação"""
    SecurityService.validate_password_strength(password)
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria token JWT com expiração"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: str) -> str:
    """Cria refresh token de longa duração"""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    }
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    """Verifica e decodifica token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            return None
            
        return payload
        
    except jwt.InvalidTokenError:
        return None

def verify_refresh_token(token: str) -> Optional[str]:
    """Verifica refresh token e retorna user_id"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "refresh":
            return None
            
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            return None
            
        return payload.get("sub")
        
    except jwt.InvalidTokenError:
        return None