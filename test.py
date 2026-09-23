from app_model.db import get_connection, delete_table

conn = get_connection()
delete_table(conn, "user_profile")