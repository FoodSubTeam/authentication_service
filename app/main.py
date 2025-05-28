import os
import pathlib
from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
import logging
from app.topics import Topic, MessageType
from app.kafka import init_topics, KafkaProducerSingleton
from google_auth_oauthlib.flow import Flow
import requests
import json

app = FastAPI()

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "671569470358-rclf8o03n048o6odmiiumbme8np4e9dp.apps.googleusercontent.com"

client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "../client_secret.json")

@app.get("/")
async def root():
    return {"message": "Auth service is running"}

@app.on_event("startup")
async def on_startup():
    logging.getLogger("aiokafka").setLevel(logging.WARNING)

    init_topics()

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

    KafkaProducerSingleton.produce_message(Topic.USER_LOGIN.value, json.dumps(user_info))
    logging.warning("Sent user information message.")

    return user_info