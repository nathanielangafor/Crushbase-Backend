# Standard library imports
import logging
import os

# Third-party imports
from dotenv import load_dotenv

# Local imports
from .accounts import AccountManager
from .crawler import CrawlerManager
from .subscription import SubscriptionManager
from .leads import LeadsManager
from .preferences import PreferencesManager
from .knowledge import KnowledgeManager

# Load environment variables from .env file
load_dotenv()

class DatabaseManager:
    def __init__(self, connection_string: str = os.getenv("MONGO_URI"), db_name: str = os.getenv("MONGO_DB_NAME"), collection_name: str = os.getenv("MONGO_ACCOUNTS_COLLECTION_NAME")):
        self.account_manager = AccountManager(connection_string, db_name, collection_name)
        self.crawler_manager = CrawlerManager(self.account_manager)
        self.subscription_manager = SubscriptionManager(self.account_manager)
        self.leads_manager = LeadsManager(connection_string, db_name, collection_name)
        self.preferences_manager = PreferencesManager(connection_string, db_name, collection_name)
        self.knowledge_manager = KnowledgeManager(connection_string, db_name, os.getenv("MONGO_KNOWLEDGE_COLLECTION_NAME"))

    def close(self):
        """Close all database connections."""
        self.account_manager.close()
        self.leads_manager.close()
        self.preferences_manager.close()
        self.knowledge_manager.close()

# Create a default instance
db_manager = DatabaseManager()
leads_manager = db_manager.leads_manager
preferences_manager = db_manager.preferences_manager
subscription_manager = db_manager.subscription_manager
account_manager = db_manager.account_manager
crawler_manager = db_manager.crawler_manager
knowledge_manager = db_manager.knowledge_manager