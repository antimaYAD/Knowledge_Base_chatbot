from pymongo import MongoClient

# Your MongoDB Atlas URI
MONGO_URL = "mongodb+srv://sachin:hHJfxxGko6BhI6Xu@cluster0.v1ude2p.mongodb.net/techjewel?retryWrites=true&w=majority&appName=Cluster0"

# Connect to the client
client = MongoClient(MONGO_URL)

# Access your database
db = client["techjewel"]

# Define collections
users_collection = db["users"]
conversations_collection = db["conversations"]


def set_journal_time(username: str, time_str: str):
    users_collection.update_one(
        {"username": username},
        {"$set": {"journal_time": time_str}},
        upsert=False  # user must already exist
    )

def get_journal_time(username: str):
    user = users_collection.find_one({"username": username})
    return user.get("journal_time", "21:00")

def get_all_users_and_times():
    return list(users_collection.find(
        {"journal_time": {"$exists": True}},
        {"username": 1, "journal_time": 1}
    ))

