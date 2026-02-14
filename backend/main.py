# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import QueryRequest
from agent import handle_query
from tools.mail import send_email, fetch_unread_emails
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmailSendRequest(BaseModel):
    recipient: str
    subject: str
    body: str

@app.get("/")
async def root():
    return {"Message": "✅MCTS Web Agent is running...🚀"}

@app.get("/health")
def health():
    return {"Status": "Running ✅"}

@app.post("/ask")
def ask(request: QueryRequest):
    return handle_query(request.query)

@app.post("/send-email")
def send_email_endpoint(request: EmailSendRequest):
    result = send_email(request.recipient, request.subject, request.body)
    return {"message": result}

@app.post("/fetch-emails")
def fetch_emails_endpoint():
    result = fetch_unread_emails()
    return {"message": result}
