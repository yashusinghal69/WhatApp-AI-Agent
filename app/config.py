import os
from typing import Optional
from dotenv import load_dotenv
 
load_dotenv()

class Config:

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
 
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")

    META_APP_ID: str = os.getenv("META_APP_ID")
    META_APP_SECRET: str = os.getenv("META_APP_SECRET")

    ADMIN_PHONE_NUMBER: str = os.getenv("ADMIN_PHONE_NUMBER")

    WEBHOOK_VERIFY_TOKEN: str = os.getenv("WEBHOOK_VERIFY_TOKEN")

    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"


# Create a global config instance
config = Config()
