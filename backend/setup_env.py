#!/usr/bin/env python3
"""
Setup script to create .env file from env.example
"""

import os
import shutil

def setup_environment():
    """Create .env file from env.example if it doesn't exist"""
    
    # Check if .env already exists
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return
    
    # Check if env.example exists
    if not os.path.exists('env.example'):
        print("❌ env.example file not found")
        return
    
    try:
        # Copy env.example to .env
        shutil.copy('env.example', '.env')
        print("✅ Created .env file from env.example")
        print("📝 Please review and modify the .env file with your actual credentials")
        
        # Show the contents
        with open('.env', 'r') as f:
            print("\n📋 .env file contents:")
            print("-" * 40)
            for line in f:
                if line.strip() and not line.startswith('#'):
                    print(line.strip())
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")

def show_instructions():
    """Show setup instructions"""
    print("\n🚀 Environment Setup Instructions:")
    print("=" * 50)
    print("1. The .env file has been created with default values")
    print("2. Review and modify the values as needed:")
    print("   - Database credentials")
    print("   - Redis credentials") 
    print("   - Application settings")
    print("3. Start the services: docker-compose up -d")
    print("4. Install dependencies: pip install -r requirements.txt")
    print("5. Run the app: python main.py")
    print("\n⚠️  Note: Never commit .env files to version control!")

if __name__ == "__main__":
    print("🔧 Setting up environment configuration...")
    setup_environment()
    show_instructions()
