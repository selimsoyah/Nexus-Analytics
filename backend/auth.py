from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
import os

# Secret key for JWT
SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Dummy user database (in-memory) - hash passwords lazily to avoid startup issues
fake_users_db = {
    "user@example.com": {
        "username": "user@example.com",
        "full_name": "Test User",
        "hashed_password": None,  # Will be hashed on first use
        "role": "user"
    },
    "admin@nexusanalytics.com": {
        "username": "admin@nexusanalytics.com",
        "full_name": "Nexus Admin",
        "hashed_password": None,  # Will be hashed on first use
        "role": "admin"
    }
}

def get_hashed_password(user_email: str):
    """Get or create hashed password for user"""
    user = fake_users_db.get(user_email)
    if user and user["hashed_password"] is None:
        user["hashed_password"] = pwd_context.hash("password123")
    return user["hashed_password"] if user else None
from pydantic import BaseModel

# Registration request model
class RegisterRequest(BaseModel):
    username: str
    full_name: str
    password: str
    role: str = "user"

# Registration endpoint


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
router = APIRouter()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user:
        return False
    hashed_password = get_hashed_password(username)
    if not hashed_password or not verify_password(password, hashed_password):
        return False
    return user

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = fake_users_db.get(username)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Require admin role for access"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get("/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user
@router.post("/register")
def register_user(req: RegisterRequest):
    if req.username in fake_users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = pwd_context.hash(req.password)
    fake_users_db[req.username] = {
        "username": req.username,
        "full_name": req.full_name,
        "hashed_password": hashed_password,
        "role": req.role
    }
    return {"msg": "User registered successfully"}