from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from google_auth_oauthlib.flow import Flow
from app.topics import Topic, MessageType
from app.kafka import init_topics, KafkaProducerSingleton
from app.service import AuthUserService
from app.routes import router
from app.database import engine
from app.models import Base
from app.security_config import create_access_token
import requests
import json
import logging
import os
import pathlib

app = FastAPI()

origins = [
    "http://localhost:8082",  # frontend origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],    # or specify ['GET', 'POST', 'OPTIONS']
    allow_headers=["*"],    # or specify headers you expect
)

app.include_router(router)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "671569470358-rclf8o03n048o6odmiiumbme8np4e9dp.apps.googleusercontent.com"

client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "../client_secret.json")

@app.get("/")
async def root():
    return {"message": "Auth service is running"}

@app.on_event("startup")
async def on_startup():
    service = AuthUserService()
    logging.getLogger("aiokafka").setLevel(logging.WARNING)
    
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)  # Uncomment to reset database entries
        await conn.run_sync(Base.metadata.create_all)

    init_topics()
    await service.create_default_admin()

@app.get("/login")
async def login():
    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
        redirect_uri="http://127.0.0.1:8000/callback"
    )
    auth_url, state = flow.authorization_url()

    message = {
        "type": MessageType.SEND_AUTH_URL.value,
        "data": auth_url
    }

    KafkaProducerSingleton.produce_message(Topic.AUTH_LOGIN_URL.value, json.dumps(message))
    logging.warning("Sent authentication link message.")

    return RedirectResponse(auth_url, status_code=status.HTTP_303_SEE_OTHER)

@app.get("/callback")
async def callback(request: Request):
    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email",
                "openid"],
        redirect_uri="http://127.0.0.1:8000/callback"
    )

    full_url = str(request.url)
    flow.fetch_token(authorization_response=full_url)
    credentials = flow.credentials

    userinfo_response = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={'Authorization': f'Bearer {credentials.token}'}
    )

    user_info = userinfo_response.json()
    email = user_info.get("email")
    id = user_info.get("id")

    KafkaProducerSingleton.produce_message(Topic.USER_LOGIN.value, json.dumps(user_info))
    logging.warning("Sent user information message.")

    jwt_token = create_access_token(data={"sub": str(id), "email": email, "role": "customer"})

    return JSONResponse({"access_token": jwt_token, "token_type": "bearer", "role": "customer"})