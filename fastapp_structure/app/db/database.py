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
