from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select  # Required for async queries
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import timedelta
import os
from dotenv import load_dotenv
from app.core.database import get_db
from app.core.models import User
from app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

load_dotenv()

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


class GoogleAuthToken(BaseModel):
    token: str


@router.post("/google-login")
async def google_login(auth_data: GoogleAuthToken, db: AsyncSession = Depends(get_db)):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500, detail="Google Client ID not configured on server"
        )

    try:
        idinfo = id_token.verify_oauth2_token(
            auth_data.token, requests.Request(), GOOGLE_CLIENT_ID
        )

        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0]) 
        picture = idinfo.get('picture', '')
        
        result = await db.execute(select(User).where(User.email == email))
        db_user = result.scalar_one_or_none()
        
        if not db_user: 
            db_user = User(
                email=email,
                full_name=name,       
                profile_pic=picture,  
                hashed_password="oauth_google_no_password_set" 
            ) 
            db.add(db_user)
        else:
            db_user.full_name = name
            db_user.profile_pic = picture

        await db.commit()
        await db.refresh(db_user)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.email}, expires_delta=access_token_expires
        )

        # In backend/app/api/auth.py (around line 43)

        return {
            "status": "success",
            "message": "Login successful",
            "user": {
                "id": db_user.id,
                "email": db_user.email,
                "name": db_user.full_name or "ScamShield User",
                "picture": db_user.profile_pic or "",
                "is_admin": bool(db_user.is_admin) 
            },
            "access_token": access_token,
        }

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")
