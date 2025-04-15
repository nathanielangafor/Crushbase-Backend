import json
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, BulkWriteError

# --- Configuration ---
# Consider using environment variables for sensitive data like the connection string
MONGODB_URI = "mongodb+srv://talys:thenextun1corn@cluster0.dp0bdcd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "Talys"
COLLECTION_NAME = "Crushbase"
JSON_FILE_PATH = "SystemFiles/user_data.json" # Relative path from script location

# --- Main Migration Logic ---
def migrate_data():
    """Reads data from a JSON file and inserts it into a MongoDB collection."""

    # Construct absolute path for the JSON file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    absolute_json_path = os.path.join(script_dir, JSON_FILE_PATH)

    try:
        # 1. Read and parse JSON file
        with open(absolute_json_path, 'r') as f:
            data = json.load(f)
        print(f"Successfully read data from {absolute_json_path}")

        if not isinstance(data, dict):
            print("Error: JSON data is not in the expected format (expected a dictionary of users)")
            return

        # 2. Connect to MongoDB
        client = MongoClient(MONGODB_URI)
        client.admin.command('ismaster')
        print("Successfully connected to MongoDB")

        # 3. Get database and collection
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        # 4. Clear existing data
        collection.delete_many({})
        print("Cleared existing data from collection")

        # 5. Transform and insert data
        documents = []
        for user_id, user_data in data.items():
            # Set the user_id as _id
            user_data['_id'] = user_id
            documents.append(user_data)

        print(f"Preparing to insert {len(documents)} user documents")

        # 6. Insert the documents
        try:
            result = collection.insert_many(documents)
            print(f"Successfully inserted {len(result.inserted_ids)} user documents")

        except BulkWriteError as bwe:
            print(f"Error during bulk insert: {bwe.details}")
        except Exception as e:
            print(f"An unexpected error occurred during data insertion: {e}")

    except FileNotFoundError:
        print(f"Error: JSON file not found at {absolute_json_path}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {absolute_json_path}")
    except ConnectionFailure:
        print("Error: Failed to connect to MongoDB. Check your connection URI and network settings.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'client' in locals():
            client.close()
            print("MongoDB connection closed")

if __name__ == "__main__":
    print("Starting data migration...")
    migrate_data()
    print("Migration process finished.") 