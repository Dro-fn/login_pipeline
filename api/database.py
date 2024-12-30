import psycopg2
from psycopg2 import sql, Error

def get_db_connection():
    """
    Establishes and returns a connection to the PostgreSQL database.
    Ensure you update the credentials to match your database configuration.

    Returns:
        connection (psycopg2.connection): Connection object to the PostgreSQL database.
    Raises:
        psycopg2.Error: If there is an issue connecting to the database.
    """
    # Replace with your database credentials
    HOST = "127.0.0.1"       # Host address, e.g., localhost or IP
    PORT = "5432"            # Port number
    DATABASE = "postgres"    # Database name
    USER = "postgres"        # Database user
    PASSWORD = "your_new_password"  # Database password

    try:
        # Establish the connection
        connection = psycopg2.connect(
            host=HOST,
            port=PORT,
            database=DATABASE,
            user=USER,
            password=PASSWORD
        )
  
        print("Database connection established successfully!")
        return connection
    except psycopg2.Error as e:
        print("Error while connecting to PostgreSQL:", e)
        raise

def add_reset_token_column():
    """
    Adds the 'reset_token' column to the 'users' table in the database if it does not exist.

    Raises:
        psycopg2.Error: If there is an issue executing the SQL command.
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Add the 'reset_token' column if it doesn't exist
        cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'reset_token'
            ) THEN
                ALTER TABLE users
                ADD COLUMN reset_token VARCHAR(255);
            END IF;
        END $$;
        """)

        connection.commit()
        print("Column 'reset_token' added to the 'users' table successfully (if it didn't already exist).")
    except psycopg2.Error as e:
        print("Error while adding 'reset_token' column to the 'users' table:", e)
        raise
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Database connection closed.")

def fetch_all_users():
    """
    Fetches all records from the 'users' table.

    Returns:
        list: A list of dictionaries where each dictionary represents a user.
    Raises:
        psycopg2.Error: If there is an issue executing the SQL query.
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Execute the SQL query to fetch all records
        cursor.execute("SELECT * FROM users;")
        
        # Fetch all rows from the query
        rows = cursor.fetchall()
        print(rows)
        # Get column names for better representation
        column_names = [desc[0] for desc in cursor.description]
        
        # Convert rows to a list of dictionaries
        users = [dict(zip(column_names, row)) for row in rows]

        print("Fetched all users successfully!")
        return users
    except psycopg2.Error as e:
        print("Error while fetching users from the 'users' table:", e)
        raise
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Database connection closed.")

def delete_all_users():
    """
    Deletes all records from the 'users' table.

    Raises:
        psycopg2.Error: If there is an issue executing the SQL query.
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Execute the SQL query to delete all records
        cursor.execute("DELETE FROM users;")
        
        # Commit the changes to the database
        connection.commit()

        print("All users deleted successfully!")
    except psycopg2.Error as e:
        print("Error while deleting users from the 'users' table:", e)
        raise
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Database connection closed.")   

# delete_all_users()                     

# Example usage
if __name__ == "__main__":
    users = fetch_all_users()
    for user in users:
        print(user)


 


       
       
        