# MES Inventory API Configuration
# Copy this file to config.py and set your actual values

# API Token - REQUIRED for authentication
# Must be set via environment variable: MES_API_TOKEN=your-secret-token
# The server will refuse to start without it.
# DO NOT hardcode a token here - use the environment variable instead.
# MES_API_TOKEN = os.environ.get('MES_API_TOKEN')  # This is handled in api.py

# Server Configuration
PORT = 5000
HOST = '127.0.0.1'  # Only binds to localhost for security