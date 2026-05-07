# MES Inventory API Configuration

# API Token - REQUIRED for authentication
# Set via environment variable: export MES_API_TOKEN=your-secret-token
MES_API_TOKEN = 'changeme-in-production'
DEBUG_MODE = False

# Server Configuration
PORT = 5000
HOST = '127.0.0.1'

# LLM analysis uses OpenCode built-in model (opencode-cli run)