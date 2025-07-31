#!/usr/bin/env python3
"""
Test connection using individual environment variables with resolved IP.
"""
import psycopg2
from dotenv import load_dotenv
import os
import subprocess

# Load environment variables from .env
load_dotenv()

def resolve_hostname_to_ip(hostname):
    """Resolve hostname using system tools."""
    try:
        # Try to get IPv4 first
        result = subprocess.run(['dig', '+short', 'A', hostname], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            ipv4 = result.stdout.strip().split('\n')[0]
            if ipv4 and not ipv4.startswith(';'):
                return ipv4, 'IPv4'
        
        # Try IPv6
        result = subprocess.run(['dig', '+short', 'AAAA', hostname], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            ipv6 = result.stdout.strip().split('\n')[0]
            if ipv6 and not ipv6.startswith(';'):
                return ipv6, 'IPv6'
        
        return None, None
    except Exception as e:
        print(f"Error resolving hostname: {e}")
        return None, None

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

print("🔍 Original Connection Parameters:")
print(f"   User: {USER}")
print(f"   Password: {'*' * len(PASSWORD) if PASSWORD else 'None'}")
print(f"   Host: {HOST}")
print(f"   Port: {PORT}")
print(f"   Database: {DBNAME}")

# Resolve hostname
print(f"\n🔍 Resolving hostname: {HOST}")
resolved_ip, ip_type = resolve_hostname_to_ip(HOST)

if resolved_ip:
    print(f"✅ Resolved to {ip_type}: {resolved_ip}")
    
    # Use resolved IP for connection
    connection_params = {
        'user': USER,
        'password': PASSWORD,
        'host': resolved_ip,
        'port': PORT,
        'dbname': DBNAME,
        'connect_timeout': 30
    }
    
    # Try different SSL modes
    ssl_modes = ['require', 'prefer', 'allow', 'disable']
    
    for ssl_mode in ssl_modes:
        try:
            print(f"\n🔌 Attempting connection with sslmode={ssl_mode}...")
            
            connection = psycopg2.connect(
                sslmode=ssl_mode,
                **connection_params
            )
            
            print(f"✅ Connection successful with {ip_type} and sslmode={ssl_mode}!")
            
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
            
            # Close the cursor and connection
            cursor.close()
            connection.close()
            print("🔒 Connection closed.")
            
            print(f"\n🎉 SUCCESS! Connection works with {ip_type} address and sslmode={ssl_mode}")
            print("Now we can run the migration script!")
            break
            
        except Exception as e:
            print(f"❌ Failed with sslmode={ssl_mode}: {e}")
            
            # Check if it's a routing issue
            if "No route to host" in str(e):
                print(f"   🔍 This is an IPv6 routing issue")
            elif "Connection refused" in str(e):
                print(f"   🔍 Connection refused - check port and firewall")
            elif "timeout" in str(e).lower():
                print(f"   🔍 Connection timeout - network issue")
    else:
        print(f"\n❌ All connection attempts failed with {ip_type} address")
        if ip_type == 'IPv6':
            print("💡 IPv6 routing issue confirmed. Your network doesn't support IPv6 connectivity to Supabase.")
        
else:
    print("❌ Could not resolve hostname")

print("\n💡 Summary:")
print("If all connections failed, manual execution via Supabase Dashboard is recommended.")
print("The database is working (as shown in your logs), but there's a network connectivity issue.")