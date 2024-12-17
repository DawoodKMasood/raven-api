from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import httpx
import os
from typing import Optional

app = FastAPI()

# Configuration
MYCASE_AUTH_URL = "https://auth.mycase.com/login_sessions/new"
MYCASE_TOKEN_URL = "https://auth.mycase.com/tokens"
CLIENT_ID = os.getenv("MYCASE_CLIENT_ID")
CLIENT_SECRET = os.getenv("MYCASE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("MYCASE_REDIRECT_URI")

class Token(BaseModel):
    access_token: str
    token_type: str
    scope: str
    refresh_token: str
    expires_in: int
    firm_uuid: Optional[str]

class TokenRequest(BaseModel):
    refresh_token: str

@app.get("/auth/mycase")
async def auth_mycase():
    """Initiate MyCase OAuth flow"""
    auth_params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "state": "some-random-state"  # In production, use secure random state
    }
    
    params = "&".join(f"{key}={value}" for key, value in auth_params.items())
    redirect_url = f"{MYCASE_AUTH_URL}?{params}"
    return RedirectResponse(url=redirect_url)

@app.get("/auth/mycase/callback")
async def auth_callback(code: str, state: Optional[str] = None):
    """Handle MyCase OAuth callback"""
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    
    token_request_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(MYCASE_TOKEN_URL, json=token_request_data)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Token exchange failed: {response.text}"
            )
        
        token_data = response.json()
        return Token(**token_data)

@app.post("/auth/mycase/refresh")
async def refresh_token(token_request: TokenRequest):
    """Refresh MyCase access token"""
    refresh_request_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": token_request.refresh_token,
        "grant_type": "refresh_token"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(MYCASE_TOKEN_URL, json=refresh_request_data)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Token refresh failed: {response.text}"
            )
        
        token_data = response.json()
        return Token(**token_data)

# Middleware to verify tokens and handle authentication
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def verify_token(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

# Protected route example
@app.get("/protected")
async def protected_route(token: str = Depends(verify_token)):
    return {"message": "This is a protected route", "token": token}