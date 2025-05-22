from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import get_settings
from typing import Any

settings = get_settings()

class MongoDB:
    client: Any = None
    db: Any = None
    chat_contents: Any = None

    async def connect_to_database(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB]
        self.chat_contents = self.db.chat_contents

    async def close_database_connection(self):
        if self.client:
            self.client.close()

mongodb = MongoDB()

async def get_mongodb():
    """Get MongoDB database instance."""
    return mongodb.db 