from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class WebhookPayload(BaseModel):
    event_type: str
    data: dict

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/webhook")
async def webhook(payload: WebhookPayload):
    print(f"Received webhook event: {payload.event_type}")
    print(f"Webhook data: {payload.data}")
    
    return {"status": "success", "message": "Webhook received"}