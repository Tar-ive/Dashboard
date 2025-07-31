#!/usr/bin/env python3
"""
Test database connection with various approaches.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_connection_methods():
    """Test different connection approaches."""
    database_url = os.getenv('DATABASE_URL')
    print(f"DATABASE_URL: {database_url}")
    
    # Parse URL
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
    if match:
        username, password, host, port, database = match.groups()
        print(f"Parsed - Host: {host}, Port: {port}, DB: {database}, User: {username}")
    else:
        print("Could not parse DATABASE_URL")
        return
    
    # Try different connection methods
    try:
        import psycopg2
        
        # Method 1: Direct URL
        print("\n1. Testing direct URL connection...")
        try:
            conn = psycopg2.connect(database_url, connect_timeout=10)
            print("✅ Direct URL connection successful!")
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Direct URL failed: {e}")
        
        # Method 2: Individual parameters
        print("\n2. Testing individual parameters...")
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password,
                connect_timeout=10,
                sslmode='require'
            )
            print("✅ Individual parameters connection successful!")
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Individual parameters failed: {e}")
        
        # Method 3: Try with different SSL modes
        print("\n3. Testing different SSL modes...")
        for sslmode in ['require', 'prefer', 'allow']:
            try:
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    database=database,
                    user=username,
                    password=password,
                    connect_timeout=10,
                    sslmode=sslmode
                )
                print(f"✅ Connection successful with sslmode={sslmode}!")
                conn.close()
                return True
            except Exception as e:
                print(f"❌ sslmode={sslmode} failed: {e}")
        
        # Method 4: Try resolving hostname manually
        print("\n4. Testing hostname resolution...")
        try:
            import socket
            ip = socket.gethostbyname(host)
            print(f"Resolved {host} to {ip}")
            
            conn = psycopg2.connect(
                host=ip,
                port=port,
                database=database,
                user=username,
                password=password,
                connect_timeout=10,
                sslmode='require'
            )
            print("✅ IP address connection successful!")
            conn.close()
            return True
        except Exception as e:
            print(f"❌ IP address connection failed: {e}")
        
    except ImportError:
        print("psycopg2 not available")
    
    return False

if __name__ == "__main__":
    success = test_connection_methods()
    if not success:
        print("\n💡 All connection methods failed. Try manual execution in Supabase Dashboard.")
    sys.exit(0 if success else 1)