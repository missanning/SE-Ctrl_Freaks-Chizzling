from database import connect_db, insert_default_data

connect_db()
insert_default_data()

print("Database created successfully!")