from pymongo import MongoClient

# Replace the uri string with your MongoDB deployment's connection string.
client = MongoClient("mongodb://localhost:27017/")

# Access the 'test' database
db = client.test

# Access the 'example_collection' collection
collection = db.example_collection

# Insert a document into the collection
document = {"name": "John", "age": 30, "city": "New York"}
collection.insert_one(document)

# Find a document in the collection
result = collection.find_one({"name": "John"})
print(result)