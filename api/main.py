
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi import Depends, HTTPException
from starlette.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pydantic import EmailStr
import time
import requests
import pandas as pd
from threading import Thread, Lock, Event


from datetime import datetime
from ta.momentum import (
    RSIIndicator, StochasticOscillator, WilliamsRIndicator, ROCIndicator, TSIIndicator
)
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, MACD
from ta.trend import (
    SMAIndicator, EMAIndicator, MACD, ADXIndicator, CCIIndicator, IchimokuIndicator
)
from ta.volatility import BollingerBands, AverageTrueRange, KeltnerChannel
from ta.volume import OnBalanceVolumeIndicator, ChaikinMoneyFlowIndicator

import numpy as np
import logging


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# import spacy
import os
import io
import re
from dotenv import load_dotenv
import boto3
from openai import OpenAI
from pydantic import BaseModel
# from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr

from api.database import get_db_connection
from passlib.hash import bcrypt
from passlib.context import CryptContext
import requests
import pandas as pd
from datetime import datetime, timedelta
from binance.client import Client


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if config.env exists (for local testing)
if os.path.exists("config.env"):
    load_dotenv("config.env")
    print("Loaded environment variables from config.env (local testing).")
else:
    print("Using Vercel environment variables.")

# # Load environment variables
# # load_dotenv("config.env")
# OPENAI_API_KEY = os.getenv("open_ai_key")

# if not OPENAI_API_KEY:
#     raise ValueError("OpenAI API key not found. Check your config.env file.")

# # Initialize OpenAI client
# openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize FastAPI app
app = FastAPI()

# JWT Configuration
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
import uuid

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates directory
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def serve_homepage(request: Request):
    """Serve the homepage."""
    return templates.TemplateResponse("index.html", {"request": request})
# # Add CORS Middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
allow_origins=["http://127.0.0.1:8000", "https://crypto-ai-pi.vercel.app","https://cryptoai.drofn.com"]
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")





async def send_reset_email(email: str, reset_link: str):
    try:
        # Email server configuration
        print(email)
        print(reset_link)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email =  os.getenv("MAIL_FROM")
        print(sender_email)
        sender_password = os.getenv("MAIL_PASSWORD")
        print(sender_password)

        # Create email message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Password Reset Request"
        message["From"] = sender_email
        message["To"] = email

        # Email body
        text = f"""\
        Hi,
        
        Click the link below to reset your password:
        {reset_link}
        
        If you did not request this, please ignore this email.
        """
        message.attach(MIMEText(text, "plain"))

        # Connect to the email server and send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())
        server.quit()

        print(f"Password reset email sent successfully to {email}.")
    except Exception as e:
        print(f"Failed to send password reset email: {str(e)}")
        raise


fake_users_db = {
    "test@example.com": {
        "username": "test",
        "hashed_password": "password123",  # Example hashed password
        "disabled": False,
    }
}

# Helper Functions
# def verify_password(plain_password, hashed_password):
#     return plain_password == hashed_password  # Replace with hashing logic

def get_user(username: str):
    return fake_users_db.get(username)

# def create_access_token(data: dict, expires_delta: timedelta = None):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """Hash a plain text password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)) -> str:
    """Generate a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")



@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve the login page."""
    with open("templates/login.html", "r") as file:
        return HTMLResponse(content=file.read())
    
# @app.get("/login", response_class=HTMLResponse)
# async def login_page(request: Request):
#     access_token = request.cookies.get("access_token")
#     if access_token:
#         return RedirectResponse(url="/dashboard")
#     return templates.TemplateResponse("login.html", {"request": request})    
    
# @app.post("/api/login")
# async def login(email: str = Form(...), password: str = Form(...)):
#     """
#     Handle user login.
#     """
#     # Check if the email exists in the database
#     user = users_db.get(email)
#     if not user:
#         raise HTTPException(
#             status_code=404,
#             detail="Email not found. Please register an account."
#         )
#     # Validate the password
#     if user["password"] != password:
#         raise HTTPException(
#             status_code=401,
#             detail="Incorrect password. Please try again."
#         )

#     # Successful login
#     return {"message": "Login successful!", "username": user["username"]}   
 
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/login")
async def login_user(
    email: str = Form(...),
    password: str = Form(...),
):
    """
    Log in the user and validate credentials.
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Fetch the user from the database
        cursor.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            return {"error": "Invalid email or user does not exist"}

        user_id, hashed_password = user

        # Verify the password
        if not pwd_context.verify(password, hashed_password):
            return {"error": "Invalid password"}

        # Generate an access token
        access_token = create_access_token(data={"sub": str(user_id)})

        # Include success message
        return {
            "message": "Login successful!",
            "redirect_url": "/dashboard",
            "access_token": access_token
        }

    except Exception as e:
        print(f"Error during login: {str(e)}")
        return {"error": "An unexpected error occurred. Please try again later."}

    finally:
        cursor.close()
        connection.close()


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and generate JWT token."""
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        # raise HTTPException(status_code=400, detail="Invalid username or password")
        return {"error": "Invalid username or password"}
    
    token = create_access_token(data={"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/app")
async def main_app(current_user: str = Depends(get_current_user)):
    """Main application logic, protected by login."""
    return {"message": f"Welcome to the app, {current_user}!"}

users_db={}

@app.get("/register", response_class=HTMLResponse)
async def get_register_page(request: Request):
    """
    Serve the registration page.
    """
    return templates.TemplateResponse("register.html", {"request": request})


# Handle registration form submission
# @app.post("/api/register")
# async def register_user(
#     username: str = Form(...),
#     email: EmailStr = Form(...),
#     password: str = Form(...)
# ):
#     """
#     Handle the user registration process.
#     """
#     # Check if the user already exists
#     if email in users_db:
#         raise HTTPException(status_code=400, detail="User already exists")

#     # Save the user to the "database" (in-memory for this example)
#     users_db[email] = {"username": username, "password": password}

#     return {"message": "Account created successfully!", "user": {"username": username, "email": email}}
# sessions = {}
@app.post("/api/register")
async def register_user(
    username: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...)
):
    """
    Register a new user in the PostgreSQL database.
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Check if the email already exists
        cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return {"error": "User already exists"}

        # Hash the password
        password_hash = pwd_context.hash(password)

        # Insert the user into the database
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (username, email, password_hash)
        )
        connection.commit()

        # Fetch the inserted user ID
        user_id = cursor.fetchone()[0]
        print(f"New user created with ID: {user_id}")

        return {"message": "Account created successfully!", "user_id": user_id}
    except Exception as e:
        connection.rollback()
        print(f"Database error: {e}")
        return {"error": "An unexpected error occurred. Please try again later."}
    finally:
        cursor.close()
        connection.close()

users_db = {
    "user@example.com": {"username": "user", "password": "hashed_password"},
    # Add other users as needed
}

import uuid

import uuid
from fastapi import HTTPException, Depends
from pydantic import BaseModel, EmailStr

# async def send_reset_email(email: str, reset_link: str):
#     # Your email sending logic here
#     print(f"Email sent to {email} with link: {reset_link}")

@app.get("/terms", response_class=HTMLResponse)
async def terms_of_service(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

# Define the request model
class ForgetPasswordRequest(BaseModel):
    email: EmailStr

@app.post("/api/forget-password")
async def forget_password(
    request: ForgetPasswordRequest,  # Use Pydantic model
    db=Depends(get_db_connection)
):
    try:
        cursor = db.cursor()

        # Access the email from the request model
        email = request.email

        # Check if email exists in the database
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            return {"error": "Email not found"}

        # Generate a unique reset token
        reset_token = str(uuid.uuid4())
        reset_link = f"http://127.0.0.1:8000/reset-password?token={reset_token}"
        print("Reset Link:", reset_link)

        # Save the reset token in the database
        cursor.execute(
            "UPDATE users SET reset_token = %s WHERE email = %s",
            (reset_token, email),
        )
        db.commit()
        print(email)
        print("Reset token saved in the database.")
        # Send the email with the reset link
      
        await send_reset_email(email, reset_link)

        return {"message": "Password reset link has been sent to your email."}
    except Exception as e:
        db.rollback()
        return {"error": f"Database error: {str(e)}"}
    finally:
        cursor.close()
        db.close()

# @app.get("/forget-password", response_class=HTMLResponse)
# async def get_forget_password_page():
#     with open("forget-password.html", "r") as file:
#         return HTMLResponse(content=file.read())
@app.get("/forget-password", response_class=HTMLResponse)
async def get_forget_password_page(request: Request):
    return templates.TemplateResponse("forget-password.html", {"request": request})    

@app.get("/reset-password")
async def reset_password_page(request: Request, token: str):
    # Validate the token and render the reset password page
    return templates.TemplateResponse("reset-password.html", {"request": request, "token": token})    
@app.post("/api/reset-password")
async def reset_password(new_password: str = Form(...), token: str = Form(...), db=Depends(get_db_connection)):
    try:
        cursor = db.cursor()

        # Check if the token exists and fetch the user
        cursor.execute("SELECT email FROM users WHERE reset_token = %s", (token,))
        user = cursor.fetchone()

        if not user:
            return {"error": "Invalid or expired token"}

        email = user[0]

        # Update the user's password and clear the token
        hashed_password = pwd_context.hash(new_password)
        cursor.execute(
            "UPDATE users SET password_hash = %s, reset_token = NULL WHERE email = %s",
            (hashed_password, email),
        )
        db.commit()

        return {"message": "Password reset successfully!"}
    except Exception as e:
        db.rollback()
        return {"error": f"Database error: {str(e)}"}
    finally:
        cursor.close()
        db.close()


# Routes
@app.get("/", response_class=HTMLResponse)
async def disclaimer():
    """Serve the homepage with a disclaimer modal."""
    with open("templates/index.html", "r") as file:
        return HTMLResponse(content=file.read())
# polly_client = boto3.client(
#     "polly",
#     aws_access_key_id=os.getenv("my_AWS_ACCESS_KEY_ID"),
#     aws_secret_access_key=os.getenv("my_AWS_SECRET_ACCESS_KEY"),
#     region_name="us-east-1"
# )
# API_KEY =  os.getenv("binance_api_key")
# API_SECRET = os.getenv("binance_secret_key")
# # gemini_api_key = os.getenv("gemini_api2")

# client = Client(API_KEY, API_SECRET)
# # genaiclient = genai.Client(
# #             api_key=gemini_api_key
# #         )




@app.get("/", response_class=HTMLResponse)
async def serve_homepage(request: Request):
    """Serve the homepage."""
    return templates.TemplateResponse("index.html", {"request": request})






# @app.post("/reset")
# async def reset(user_id: str = "default"):
#     """Reset conversation history for the given user ID."""
#     if user_id in sessions:
#         sessions.pop(user_id)  # Clear session data
#         return {"message": "Conversation history reset."}
#     return {"message": "No active session found to reset."}


