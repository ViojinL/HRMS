import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def create_database():
    try:
        # Connect to default 'postgres' database
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="1024linux.Q",
            host="localhost",
            port="5432",
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'hrms'")
        exists = cur.fetchone()

        if not exists:
            print("Creating database 'hrms'...")
            cur.execute("CREATE DATABASE hrms")
            print("Database 'hrms' created successfully.")
        else:
            print("Database 'hrms' already exists.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")


if __name__ == "__main__":
    create_database()
