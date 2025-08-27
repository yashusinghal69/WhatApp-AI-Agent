import asyncio
import logging
from typing import Dict, Any, Optional
import httpx
from openai import AsyncOpenAI
from .config import Config

config = Config()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 

openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
 
http_client = httpx.AsyncClient(timeout=30.0)


async def send_typing_indicator_and_read_receipt(to: str, message_id: str) -> bool:
 
    headers = {
        "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
        "typing_indicator": {
            "type": "text"
        }
    }
    
    try:
        response = await http_client.post(
            f"https://graph.facebook.com/v22.0/{config.WHATSAPP_PHONE_NUMBER_ID}/messages",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Typing indicator and read receipt sent for {to}")
            return True
        else:
            logger.error(f"❌ Failed to send typing indicator and read receipt: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending typing indicator and read receipt: {e}")
        return False

 

async def send_whatsapp_message(to: str, message: str) -> bool:
    
    headers = {
        "Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        response = await http_client.post(
           f"https://graph.facebook.com/v22.0/{config.WHATSAPP_PHONE_NUMBER_ID}/messages",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Message sent successfully to {to}")
            return True
        else:
            logger.error(f"❌ Failed to send message: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return False


async def get_openai_response(user_message: str, user_phone: str) -> str:
 
    response = await openai_client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {
                "role": "system", 
                "content": "You are a helpful AI assistant. Keep responses concise and helpful. Respond in the same language as the user's message."
            },
            {
                "role": "user", 
                "content": user_message
            }
        ],
        max_tokens=300,    # Reduced for faster response
        temperature=0.7,
        stream=False,
        timeout=15         # Shorter timeout for faster failure handling
    )
    
    ai_response = response.choices[0].message.content.strip()
    logger.info(f"✅ OpenAI response generated for {user_phone} ({len(ai_response)} chars)")
    return ai_response
        
 

async def process_whatsapp_message(message_data: Dict[str, Any]) -> None:
    
    from_number = message_data.get("from")
    message_id = message_data.get("id")
    timestamp = message_data.get("timestamp")
    
    message_type = message_data.get("type")
    
    if message_type == "text":
        user_message = message_data.get("text", {}).get("body", "").strip()
    else:
        # Handle non-text messages
        await send_whatsapp_message(
            from_number, 
            "I can only process text messages at the moment. Please send a text message!"
        )
        return
    
    logger.info(f"📱 Received message from {from_number}: {user_message}")
    
    # Send typing indicator and mark message as read in one request
    if message_id:
        await send_typing_indicator_and_read_receipt(from_number, message_id)
 
    try:
 
        ai_response = await get_openai_response(user_message, from_number)
        
        success = await send_whatsapp_message(from_number, ai_response)
        
        if success:
            logger.info(f"✅ Complete conversation processed for {from_number}")
        else:
            logger.error(f"❌ Failed to complete conversation for {from_number}")
            
    except Exception as e:
        logger.error(f"❌ Error processing message for {from_number}: {e}")
        # Send error message if something goes wrong
        await send_whatsapp_message(
            from_number, 
            "Sorry, I encountered an error while processing your message. Please try again."
        )
            

async def handle_webhook_data(body: Dict[str, Any]) -> None:
  
    try:
        if body.get("object") != "whatsapp_business_account":
            logger.warning("Received non-WhatsApp webhook")
            return
            
        entries = body.get("entry", [])
        
        # Process all entries concurrently for better performance
        tasks = []
        
        for entry in entries:
            changes = entry.get("changes", [])
            
            for change in changes:
                if change.get("field") == "messages":
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    
                    # Process each message
                    for message in messages:
                        task = asyncio.create_task(process_whatsapp_message(message))
                        tasks.append(task)
        
       
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"✅ Processed {len(tasks)} messages")
            
    except Exception as e:
        logger.error(f"Error handling webhook data: {e}")


 

async def verify_webhook(mode: str, token: str, challenge: str, verify_token: str) -> Optional[str]:
 
    logger.info(f"Verifying webhook: mode={mode}, token_matches={token == verify_token}")
    
    if mode == "subscribe" and token == verify_token:
        logger.info("✅ Webhook verified successfully")
        return challenge
    else:
        logger.error(f"❌ Webhook verification failed - Mode: {mode}, Token match: {token == verify_token}")
        logger.error(f"Received token: '{token}', Expected token: '{verify_token}'")
        return None
