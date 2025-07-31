#!/usr/bin/env python3
"""
Test connection using IPv4 pooler connection.
"""
import psycopg2
from dotenv import load_dotenv
import os
import socket

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

print("🔍 IPv4 Pooler Connection Parameters:")
print(f"   User: {USER}")
print(f"   Password: {'*' * len(PASSWORD) if PASSWORD else 'None'}")
print(f"   Host: {HOST}")
print(f"   Port: {PORT}")
print(f"   Database: {DBNAME}")
print()

# Test DNS resolution first
print("🔍 Testing DNS resolution...")
try:
    ip = socket.gethostbyname(HOST)
    print(f"✅ DNS Resolution: {HOST} -> {ip}")
    
    # Check if it's IPv4
    if '.' in ip and ':' not in ip:
        print("✅ Resolved to IPv4 address!")
    else:
        print(f"⚠️  Resolved to: {ip}")
        
except Exception as e:
    print(f"❌ DNS Resolution failed: {e}")
    print("Continuing with connection attempt...")

print()

# Test socket connection
print("🔍 Testing socket connection...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    result = sock.connect_ex((HOST, int(PORT)))
    sock.close()
    
    if result == 0:
        print("✅ Socket connection successful!")
    else:
        print(f"❌ Socket connection failed: Error code {result}")
except Exception as e:
    print(f"❌ Socket test failed: {e}")

print()

# Connect to the database
try:
    print("🔌 Attempting PostgreSQL connection...")
    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        connect_timeout=30,
        sslmode='require'
    )
    print("✅ PostgreSQL connection successful!")
    
    # Create a cursor to execute SQL queries
    cursor = connection.cursor()
    
    # Test queries
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print(f"📅 Current Time: {result[0]}")
    
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"🗄️  Database Version: {version[0][:50]}...")
    
    # Test if we can see tables
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    table_count = cursor.fetchone()
    print(f"📋 Public tables: {table_count[0]}")
    
    # Test if we can see researchers table
    cursor.execute("SELECT COUNT(*) FROM researchers LIMIT 1;")
    researcher_count = cursor.fetchone()
    print(f"👥 Researchers table accessible: {researcher_count[0]} records")
    
    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("🔒 Connection closed.")
    
    print("\n🎉 SUCCESS! IPv4 pooler connection works!")
    print("Ready to run the CADS migration!")

except Exception as e:
    print(f"❌ PostgreSQL connection failed: {e}")
    
    # Try with different SSL modes
    print("\n🔄 Trying alternative SSL modes...")
    
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
            print("   🎉 IPv4 pooler connection works!")
            break
        except Exception as e2:
            print(f"   ❌ sslmode={ssl_mode} failed: {e2}")
    else:
        print("\n💡 All connection attempts failed even with IPv4 pooler.")