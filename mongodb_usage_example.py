from pymongo import MongoClient

def read_only_action():
    # Connect as read-only user
    readonly_client = MongoClient("mongodb://readOnlyUser:readOnlyPassword@127.0.0.1:27017/game_db?authSource=game_db")
    
    # Access the database as read-only user
    readonly_db = readonly_client['game_db']
    
    # Access the collection as read-only user
    readonly_collection = readonly_db['user_data']
    
    # Find a document as read-only user
    result = readonly_collection.find_one({"name": "Alice"})
    print(result)
    
    # Close the connection
    readonly_client.close()

def admin_action():
    # Connect as admin user
    admin_client = MongoClient("mongodb://gameDbAdmin:gameDbAdminPassword@127.0.0.1:27017/game_db?authSource=game_db")
    
    # Access the database as admin
    admin_db = admin_client['game_db']
    
    # Access the collection as admin
    admin_collection = admin_db['user_data']
    
    # Insert a document as admin
    document = {"name": "Alice", "age": 30}
    admin_collection.insert_one(document)
    
    # Update a document as admin
    admin_collection.update_one({"name": "Alice"}, {"$set": {"age": 31}})
    
    # Delete a document as admin
    admin_collection.delete_one({"name": "Alice"})
    
    # Close the connection
    admin_client.close()

# Example usage
admin_action()

# Example usage
read_only_action()