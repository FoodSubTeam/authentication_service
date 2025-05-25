import os
import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
from app.kafka import init_topics, send_to_kafka
from google_auth_oauthlib.flow import Flow

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
        scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email",
                "openid"],
        redirect_uri="http://127.0.0.1:5000/callback"
    )
    auth_url, state = flow.authorization_url()

    send_to_kafka("auth.login.urls", {"auth_url": auth_url, "state": state})

    return JSONResponse({"auth_url": auth_url})

@app.get("/callback")
async def callback(request: Request):
    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email",
                "openid"],
        redirect_uri="http://127.0.0.1:5000/callback"
    )

    full_url = str(request.url)
    flow.fetch_token(authorization_response=full_url)

    credentials = flow.credentials

    token_info = {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "expires_in": credentials.expiry.isoformat()
    }

    send_to_kafka("auth_tokens_received", token_info)

    return JSONResponse({"message": "Authentication successful"})