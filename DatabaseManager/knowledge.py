import uuid
from typing import Dict, Any, Optional
from pymongo import MongoClient

class KnowledgeManager:
    def __init__(self, connection_string: str, db_name: str, collection_name: str):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def add_data(self, data: Dict[str, Any], custom_id: Optional[str] = None) -> str:
        """
        Add data to the knowledge collection with either a custom ID or auto-generated UUID.
        
        Args:
            data (Dict[str, Any]): The data to be stored in MongoDB
            custom_id (Optional[str]): Custom ID to use instead of auto-generated UUID
            
        Returns:
            str: The ID of the inserted document, or None if document already exists
        """
        document_id = custom_id if custom_id else str(uuid.uuid4())
        
        # Check if document with this ID already exists
        if self.collection.find_one({"_id": document_id}):
            return None
            
        document = {
            "_id": document_id,
            **data
        }
        self.collection.insert_one(document)
        return document_id

    def close(self):
        """Close the MongoDB connection."""
        self.client.close()
