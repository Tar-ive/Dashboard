#!/usr/bin/env python3
"""
Comprehensive diagnostic script to identify Supabase connection issues.
"""
import os
import sys
import socket
import subprocess
import platform
from dotenv import load_dotenv

load_dotenv()

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def run_command(cmd):
    """Run a system command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def test_basic_connectivity():
    """Test basic network connectivity."""
    print_section("Basic Network Connectivity")
    
    # Test internet connectivity
    print("1. Testing basic internet connectivity...")
    success, stdout, stderr = run_command("ping -c 3 8.8.8.8")
    if success:
        print("   ✅ Internet connectivity: OK")
    else:
        print("   ❌ Internet connectivity: FAILED")
        print(f"   Error: {stderr}")
    
    # Test DNS resolution to known good host
    print("\n2. Testing DNS resolution to google.com...")
    success, stdout, stderr = run_command("nslookup google.com")
    if success:
        print("   ✅ DNS resolution: OK")
    else:
        print("   ❌ DNS resolution: FAILED")
        print(f"   Error: {stderr}")

def test_supabase_hostname():
    """Test Supabase hostname resolution."""
    print_section("Supabase Hostname Resolution")
    
    hostname = "db.zsezliiffdcgqekwggjq.supabase.co"
    
    # Test with different DNS tools
    dns_commands = [
        ("nslookup", f"nslookup {hostname}"),
        ("dig", f"dig {hostname}"),
        ("host", f"host {hostname}"),
        ("ping", f"ping -c 1 {hostname}"),
    ]
    
    for tool, cmd in dns_commands:
        print(f"\n{tool.upper()} test:")
        success, stdout, stderr = run_command(cmd)
        if success:
            print(f"   ✅ {tool}: SUCCESS")
            if stdout:
                # Show first few lines of output
                lines = stdout.split('\n')[:3]
                for line in lines:
                    if line.strip():
                        print(f"   📋 {line}")
        else:
            print(f"   ❌ {tool}: FAILED")
            if stderr:
                print(f"   Error: {stderr}")

def test_python_dns():
    """Test Python's DNS resolution capabilities."""
    print_section("Python DNS Resolution")
    
    hostname = "db.zsezliiffdcgqekwggjq.supabase.co"
    
    # Test Python's socket.gethostbyname
    print("1. Testing Python socket.gethostbyname()...")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"   ✅ Python DNS resolution: {hostname} -> {ip}")
    except Exception as e:
        print(f"   ❌ Python DNS resolution failed: {e}")
    
    # Test Python's socket.getaddrinfo
    print("\n2. Testing Python socket.getaddrinfo()...")
    try:
        results = socket.getaddrinfo(hostname, 5432, socket.AF_UNSPEC, socket.SOCK_STREAM)
        print(f"   ✅ getaddrinfo found {len(results)} addresses:")
        for i, (family, type_, proto, canonname, sockaddr) in enumerate(results[:3]):
            family_name = "IPv4" if family == socket.AF_INET else "IPv6" if family == socket.AF_INET6 else f"Family-{family}"
            print(f"   📋 {i+1}. {family_name}: {sockaddr[0]}:{sockaddr[1]}")
    except Exception as e:
        print(f"   ❌ getaddrinfo failed: {e}")

def test_python_socket_connection():
    """Test Python socket connection."""
    print_section("Python Socket Connection")
    
    hostname = "db.zsezliiffdcgqekwggjq.supabase.co"
    port = 5432
    
    # Try to get addresses first
    try:
        addresses = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        print(f"Found {len(addresses)} addresses to try...")
        
        for i, (family, type_, proto, canonname, sockaddr) in enumerate(addresses):
            family_name = "IPv4" if family == socket.AF_INET else "IPv6" if family == socket.AF_INET6 else f"Family-{family}"
            print(f"\n{i+1}. Testing {family_name} connection to {sockaddr[0]}:{sockaddr[1]}...")
            
            try:
                sock = socket.socket(family, socket.SOCK_STREAM)
                sock.settimeout(10)
                result = sock.connect_ex(sockaddr)
                sock.close()
                
                if result == 0:
                    print(f"   ✅ {family_name} socket connection: SUCCESS")
                else:
                    print(f"   ❌ {family_name} socket connection failed: Error code {result}")
            except Exception as e:
                print(f"   ❌ {family_name} socket connection failed: {e}")
                
    except Exception as e:
        print(f"❌ Could not resolve addresses: {e}")

def test_psycopg2_connection():
    """Test psycopg2 connection with detailed error reporting."""
    print_section("PostgreSQL Connection (psycopg2)")
    
    try:
        import psycopg2
        print("✅ psycopg2 module available")
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return
        
        print(f"📋 DATABASE_URL: {database_url[:50]}...")
        
        # Parse URL
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
        if match:
            username, password, host, port, database = match.groups()
            print(f"📋 Parsed - Host: {host}, Port: {port}, DB: {database}, User: {username}")
            
            # Try connection with detailed error reporting
            print("\nAttempting psycopg2 connection...")
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
                print("✅ psycopg2 connection: SUCCESS!")
                
                # Test a simple query
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                    print(f"📋 Database version: {version[:50]}...")
                
                conn.close()
                
            except psycopg2.OperationalError as e:
                print(f"❌ psycopg2 OperationalError: {e}")
                # Check if it's a DNS issue specifically
                if "could not translate host name" in str(e):
                    print("🔍 This is specifically a DNS resolution issue in psycopg2")
            except Exception as e:
                print(f"❌ psycopg2 connection failed: {e}")
        else:
            print("❌ Could not parse DATABASE_URL")
            
    except ImportError:
        print("❌ psycopg2 not available")

def test_network_configuration():
    """Test network configuration."""
    print_section("Network Configuration")
    
    print("1. System information:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Python: {sys.version.split()[0]}")
    
    print("\n2. DNS configuration:")
    if platform.system() == "Darwin":  # macOS
        success, stdout, stderr = run_command("cat /etc/resolv.conf")
        if success:
            print("   📋 DNS servers:")
            for line in stdout.split('\n'):
                if line.startswith('nameserver'):
                    print(f"      {line}")
    
    print("\n3. Network interfaces:")
    success, stdout, stderr = run_command("ifconfig | grep inet")
    if success:
        lines = stdout.split('\n')[:5]  # Show first 5 lines
        for line in lines:
            if line.strip():
                print(f"   📋 {line.strip()}")

def test_alternative_connections():
    """Test alternative connection methods."""
    print_section("Alternative Connection Tests")
    
    # Test HTTPS connection to Supabase
    print("1. Testing HTTPS connection to Supabase...")
    try:
        import requests
        response = requests.get("https://supabase.com", timeout=10)
        print(f"   ✅ HTTPS to supabase.com: {response.status_code}")
    except Exception as e:
        print(f"   ❌ HTTPS to supabase.com failed: {e}")
    
    # Test if we can reach other PostgreSQL servers
    print("\n2. Testing connection to public PostgreSQL server...")
    try:
        import psycopg2
        # Try connecting to a public test database
        conn = psycopg2.connect(
            host="postgres.crcind.com",
            port=5432,
            database="crcind",
            user="postgres",
            password="",
            connect_timeout=5
        )
        print("   ✅ Connection to public PostgreSQL: SUCCESS")
        conn.close()
    except Exception as e:
        print(f"   ❌ Connection to public PostgreSQL failed: {e}")

def main():
    """Run all diagnostic tests."""
    print("🚀 Supabase Connection Diagnostic Tool")
    print("This will help identify why Python can't connect to Supabase")
    
    test_basic_connectivity()
    test_supabase_hostname()
    test_python_dns()
    test_python_socket_connection()
    test_psycopg2_connection()
    test_network_configuration()
    test_alternative_connections()
    
    print_section("Summary & Recommendations")
    print("📋 Diagnostic complete. Review the results above to identify the issue.")
    print("\n💡 Common solutions:")
    print("   1. If DNS resolution fails: Check DNS settings, try different DNS servers")
    print("   2. If socket connection fails: Check firewall, proxy settings")
    print("   3. If only psycopg2 fails: Try different connection parameters")
    print("   4. If IPv6 issues: Try forcing IPv4 or configuring IPv6 properly")

if __name__ == "__main__":
    main()