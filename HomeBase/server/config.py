# MES Inventory API Configuration
# Copy this file to config.py and set your actual values

# API Token - REQUIRED for authentication
# Set via environment variable: export MES_API_TOKEN=your-secret-token
# Or set directly here (not recommended for production):
MES_API_TOKEN = 'changeme-in-production'

# Server Configuration
PORT = 5000
HOST = '127.0.0.1'  # Only binds to localhost for security