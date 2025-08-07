from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB URI and Database Name from environment variables
MONGODB_URI = os.getenv("MONGODB_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

try:
    # Initialize MongoDB client
    client = MongoClient(MONGODB_URI)
    db = client[MONGO_DB_NAME]

    # Test connection by listing collections
    print("Successfully connected to MongoDB!")
    print("Database Name:", MONGO_DB_NAME)
    
    # Create a test document in chat_history collection
    chat_history = db['chat_history']
    test_document = {
        "user_message": "Test message",
        "bot_response": "Test response",
        "timestamp": os.path.getctime(__file__)
    }
    result = chat_history.insert_one(test_document)
    
    print("\nTest document inserted with ID:", result.inserted_id)
    print("\nCollections in Database:")
    print(db.list_collection_names())
    
    print("\nDocuments in chat_history:")
    for doc in chat_history.find():
        print(doc)

except Exception as e:
    print("Failed to connect to MongoDB. Error:", str(e))


for collection_name in db.list_collection_names():
    print(f"Fetching data from collection: {collection_name}")
    collection = db[collection_name]
    for document in collection.find().limit(5):  # Fetch the first 5 documents
        print(document)
