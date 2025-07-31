#!/usr/bin/env python3
"""
Test database connection using IPv6 address.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_ipv6_connection():
    """Test connection using IPv6 address."""
    database_url = os.getenv('DATABASE_URL')
    
    # Parse URL
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
    if not match:
        print("Could not parse DATABASE_URL")
        return False
    
    username, password, host, port, database = match.groups()
    
    # Use the IPv6 address we found
    ipv6_address = "2600:1f16:1cd0:330a:d13:ed41:8501:1be5"
    
    print(f"Testing connection to IPv6 address: {ipv6_address}")
    
    try:
        import psycopg2
        
        # Try connecting with IPv6 address
        conn = psycopg2.connect(
            host=ipv6_address,
            port=port,
            database=database,
            user=username,
            password=password,
            connect_timeout=30,
            sslmode='require'
        )
        
        print("✅ IPv6 connection successful!")
        
        # Test a simple query
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            result = cursor.fetchone()
            print(f"Database version: {result[0][:50]}...")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ IPv6 connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_ipv6_connection()
    sys.exit(0 if success else 1)