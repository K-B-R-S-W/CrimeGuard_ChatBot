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
    emergency_calls = db['emergency_calls']  # Emergency call records
    
    # Create indexes for better query performance
    chat_history.create_index([("timestamp", -1)])
    
    # Emergency call indexes for efficient querying
    emergency_calls.create_index([("timestamp", -1)])  # Sort by time
    emergency_calls.create_index([("emergency_type", 1)])  # Filter by service (police/fire/ambulance)
    emergency_calls.create_index([("language", 1)])  # Filter by language
    emergency_calls.create_index([("call_status", 1)])  # Filter by status
    emergency_calls.create_index([("confidence", -1)])  # Sort by confidence
    
    # Compound indexes for complex queries
    emergency_calls.create_index([("emergency_type", 1), ("timestamp", -1)])  # Service + time
    emergency_calls.create_index([("language", 1), ("emergency_type", 1)])  # Language + service
    
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
        
        # Save all interactions to chat_history collection
        result = chat_history.insert_one(interaction)
        logger.info(f"{message_type.capitalize()} interaction saved with ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        logger.error(f"Error saving chat interaction to MongoDB: {e}")
        raise

def get_chat_history(limit: int = 100, history_type: str = 'text'):
    """
    Retrieve chat history from MongoDB.
    
    Args:
        limit (int): Maximum number of records to retrieve
        history_type (str): Type of history to retrieve ('text' or 'voice') - for backward compatibility
    
    Returns:
        list: List of chat interactions
    """
    try:
        # All history now stored in chat_history collection
        history = list(chat_history.find(
            {}, 
            {'_id': 0}  # Exclude MongoDB ID from results
        ).sort('timestamp', -1).limit(limit))
        
        return history
    except Exception as e:
        logger.error(f"Error retrieving chat history from MongoDB: {e}")
        raise


def save_emergency_call(
    user_message: str,
    emergency_type: str,
    phone_number: str,
    call_sid: str,
    language: str,
    confidence: float,
    reasoning: str,
    severity: str = 'severe',
    audio_url: str = None,
    user_phone: str = None,
    call_status: str = 'initiated'
):
    """
    Save emergency call record to MongoDB with multi-language support.
    
    Args:
        user_message (str): The user's emergency message
        emergency_type (str): Type of emergency ('police', 'fire', 'ambulance')
        phone_number (str): Emergency service phone number called
        call_sid (str): Twilio call SID for tracking
        language (str): Language of the message ('en', 'si', 'ta')
        confidence (float): AI confidence score (0.0 to 1.0)
        reasoning (str): AI reasoning for emergency detection
        severity (str): Severity level ('minor', 'moderate', 'severe')
        audio_url (str, optional): URL of user message audio file
        user_phone (str, optional): User's phone number
        call_status (str): Initial call status (default: 'initiated')
    
    Returns:
        ObjectId: MongoDB document ID
    """
    try:
        logger.info(f"Saving emergency call record: {emergency_type} ({language})")
        
        # Map language codes to full names for better readability
        language_map = {
            'en': 'English',
            'si': 'Sinhala',
            'ta': 'Tamil'
        }
        
        # Map emergency types to service names in multiple languages
        service_names = {
            'police': {
                'en': 'Police',
                'si': 'පොලිසිය',
                'ta': 'காவல்துறை'
            },
            'fire': {
                'en': 'Fire Department',
                'si': 'ගිනි නිවීම',
                'ta': 'தீயணைப்பு'
            },
            'ambulance': {
                'en': 'Ambulance',
                'si': 'ගිලන් රථය',
                'ta': 'ஆம்புலன்ஸ்'
            }
        }
        
        emergency_record = {
            'timestamp': datetime.utcnow(),
            'user_message': user_message,
            'emergency_type': emergency_type,  # 'police', 'fire', 'ambulance'
            'service_name_en': service_names.get(emergency_type, {}).get('en', emergency_type.title()),
            'service_name_si': service_names.get(emergency_type, {}).get('si', ''),
            'service_name_ta': service_names.get(emergency_type, {}).get('ta', ''),
            'phone_number': phone_number,
            'call_sid': call_sid,
            'language': language,
            'language_name': language_map.get(language, language),
            'confidence': confidence,
            'severity': severity,  # 'minor', 'moderate', 'severe'
            'ai_reasoning': reasoning,
            'audio_url': audio_url,
            'user_phone': user_phone,
            'call_status': call_status,  # 'initiated', 'ringing', 'in-progress', 'completed', 'failed', 'canceled'
            'call_duration': None,  # Will be updated when call completes
            'updated_at': datetime.utcnow()
        }
        
        logger.info(f"Emergency record prepared: {emergency_record}")
        
        result = emergency_calls.insert_one(emergency_record)
        logger.info(f"Emergency call saved with ID: {result.inserted_id}")
        logger.info(f"Service: {emergency_type} | Language: {language} | Confidence: {confidence:.2f}")
        
        return result.inserted_id
    except Exception as e:
        logger.error(f"Error saving emergency call to MongoDB: {e}")
        raise


def update_call_status(call_sid: str, status: str, duration: int = None):
    """
    Update the status of an emergency call.
    
    Args:
        call_sid (str): Twilio call SID
        status (str): New call status
        duration (int, optional): Call duration in seconds
    
    Returns:
        bool: True if updated successfully
    """
    try:
        logger.info(f"Updating call status for {call_sid}: {status}")
        
        update_data = {
            'call_status': status,
            'updated_at': datetime.utcnow()
        }
        
        if duration is not None:
            update_data['call_duration'] = duration
        
        result = emergency_calls.update_one(
            {'call_sid': call_sid},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Call status updated successfully: {call_sid} -> {status}")
            return True
        else:
            logger.warning(f"No call found with SID: {call_sid}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating call status: {e}")
        raise


def get_emergency_calls(
    limit: int = 100,
    emergency_type: str = None,
    language: str = None,
    status: str = None,
    min_confidence: float = None
):
    """
    Retrieve emergency call history with optional filters.
    
    Args:
        limit (int): Maximum number of records to retrieve
        emergency_type (str, optional): Filter by service ('police', 'fire', 'ambulance')
        language (str, optional): Filter by language ('en', 'si', 'ta')
        status (str, optional): Filter by call status
        min_confidence (float, optional): Minimum confidence threshold
    
    Returns:
        list: List of emergency call records
    """
    try:
        # Build filter query
        query = {}
        
        if emergency_type:
            query['emergency_type'] = emergency_type
            
        if language:
            query['language'] = language
            
        if status:
            query['call_status'] = status
            
        if min_confidence is not None:
            query['confidence'] = {'$gte': min_confidence}
        
        logger.info(f"Retrieving emergency calls with filters: {query}")
        
        calls = list(emergency_calls.find(
            query,
            {'_id': 0}  # Exclude MongoDB ID from results
        ).sort('timestamp', -1).limit(limit))
        
        logger.info(f"Retrieved {len(calls)} emergency call records")
        
        return calls
    except Exception as e:
        logger.error(f"Error retrieving emergency calls from MongoDB: {e}")
        raise


def get_emergency_statistics():
    """
    Get statistics about emergency calls.
    
    Returns:
        dict: Statistics including counts by type, language, and status
    """
    try:
        logger.info("Calculating emergency call statistics")
        
        # Count by emergency type
        type_counts = emergency_calls.aggregate([
            {'$group': {'_id': '$emergency_type', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        # Count by language
        language_counts = emergency_calls.aggregate([
            {'$group': {'_id': '$language', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        # Count by status
        status_counts = emergency_calls.aggregate([
            {'$group': {'_id': '$call_status', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        # Average confidence by type
        avg_confidence = emergency_calls.aggregate([
            {'$group': {
                '_id': '$emergency_type',
                'avg_confidence': {'$avg': '$confidence'},
                'min_confidence': {'$min': '$confidence'},
                'max_confidence': {'$max': '$confidence'}
            }},
            {'$sort': {'avg_confidence': -1}}
        ])
        
        # Total calls
        total_calls = emergency_calls.count_documents({})
        
        statistics = {
            'total_calls': total_calls,
            'by_type': list(type_counts),
            'by_language': list(language_counts),
            'by_status': list(status_counts),
            'confidence_stats': list(avg_confidence)
        }
        
        logger.info(f"Statistics calculated: {total_calls} total emergency calls")
        
        return statistics
    except Exception as e:
        logger.error(f"Error calculating emergency statistics: {e}")
        raise
