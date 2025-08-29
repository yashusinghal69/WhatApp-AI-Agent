import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
import logging
import uvicorn

from app.config import config
from app.webhook import (
    handle_webhook_data,
    verify_webhook
)

logging.basicConfig(
    level=logging.INFO if not config.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="WhatsApp AI Bot",
    description="Production-ready WhatsApp AI Bot with OpenAI integration",
    version="1.0.0",
)

@app.get("/")
async def root():
    return {
        "status": "active",
        "message": "WhatsApp AI Bot is running!",
        "version": "1.0.0"
    }

@app.get("/webhook")
async def webhook_verification(
    request: Request,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
        
    challenge = await verify_webhook(
        hub_mode, 
        hub_verify_token,
        hub_challenge,
        config.WEBHOOK_VERIFY_TOKEN
    )
    
    if challenge:
        logger.info(f"✅ Webhook verification successful, returning challenge: {challenge}")
        return PlainTextResponse(challenge)
    else:
        logger.error("❌ Webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")



@app.post("/webhook")
async def webhook_handler(request: Request):
    
    try:
        body = await request.json()
        
        if config.DEBUG:
            logger.debug(f"📨 Received webhook: {body}")
         
        asyncio.create_task(handle_webhook_data(body))
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error in webhook handler: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
   
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=config.DEBUG,
        access_log=config.DEBUG,
        workers=1,   
        loop="asyncio"
    )
