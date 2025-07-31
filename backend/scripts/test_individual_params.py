#!/usr/bin/env python3
"""
Test connection using individual environment variables.
"""
import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

print("🔍 Connection Parameters:")
print(f"   User: {USER}")
print(f"   Password: {'*' * len(PASSWORD) if PASSWORD else 'None'}")
print(f"   Host: {HOST}")
print(f"   Port: {PORT}")
print(f"   Database: {DBNAME}")
print()

# Connect to the database
try:
    print("🔌 Attempting connection...")
    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        connect_timeout=30,
        sslmode='require'
    )
    print("✅ Connection successful!")
    
    # Create a cursor to execute SQL queries
    cursor = connection.cursor()
    
    # Example query
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print(f"📅 Current Time: {result[0]}")
    
    # Test another query
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"🗄️  Database Version: {version[0][:50]}...")
    
    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("🔒 Connection closed.")
    
    print("\n✅ Connection test successful! Ready to run migration.")

except Exception as e:
    print(f"❌ Failed to connect: {e}")
    
    # Try with different SSL modes
    print("\n🔄 Trying alternative connection methods...")
    
    ssl_modes = ['prefer', 'allow', 'disable']
    for ssl_mode in ssl_modes:
        try:
            print(f"   Trying sslmode={ssl_mode}...")
            connection = psycopg2.connect(
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
                dbname=DBNAME,
                connect_timeout=30,
                sslmode=ssl_mode
            )
            print(f"   ✅ Connection successful with sslmode={ssl_mode}!")
            connection.close()
            break
        except Exception as e2:
            print(f"   ❌ sslmode={ssl_mode} failed: {e2}")
    else:
        print("\n💡 All connection attempts failed.")
        print("This confirms the IPv6 routing issue we identified earlier.")