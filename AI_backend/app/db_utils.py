from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')

# Initialize MongoDB client
try:
    client = MongoClient(MONGODB_URI)
    db = client[MONGO_DB_NAME]
    
    # Initialize collections
    chat_history = db['chat_history']
    voice_history = db['voice_history']
    
    # Create indexes for better query performance
    chat_history.create_index([("timestamp", -1)])
    voice_history.create_index([("timestamp", -1)])
    
    # Verify collections exist
    collections = db.list_collection_names()
    logger.info(f"Available collections: {collections}")
    logger.info(f"Successfully connected to MongoDB database: {MONGO_DB_NAME}")
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {e}")
    raise

def save_chat_interaction(user_message: str, bot_response: str, message_type: str = 'text'):
    """
    Save a chat interaction to MongoDB.
    
    Args:
        user_message (str): The message sent by the user
        bot_response (str): The response from the chatbot
        message_type (str): Type of message ('text' or 'voice')
    """
    try:
        # Log the attempt to save
        logger.info(f"Attempting to save {message_type} interaction to MongoDB")
        
        interaction = {
            'timestamp': datetime.utcnow(),
            'user_message': user_message,
            'bot_response': bot_response,
            'message_type': message_type
        }
        
        logger.info(f"Interaction data prepared: {interaction}")
        
        # Choose the appropriate collection based on message type
        collection = voice_history if message_type == 'voice' else chat_history
        
        result = collection.insert_one(interaction)
        logger.info(f"{message_type.capitalize()} interaction saved with ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        logger.error(f"Error saving chat interaction to MongoDB: {e}")
        raise

def get_chat_history(limit: int = 100, history_type: str = 'text'):
    """
    Retrieve history from MongoDB.
    
    Args:
        limit (int): Maximum number of records to retrieve
        history_type (str): Type of history to retrieve ('text' or 'voice')
    
    Returns:
        list: List of chat interactions
    """
    try:
        collection = voice_history if history_type == 'voice' else chat_history
        
        history = list(collection.find(
            {}, 
            {'_id': 0}  # Exclude MongoDB ID from results
        ).sort('timestamp', -1).limit(limit))
        
        return history
    except Exception as e:
        logger.error(f"Error retrieving {history_type} history from MongoDB: {e}")
        raise
