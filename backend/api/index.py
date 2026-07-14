# Vercel Python serverless wrapper for FastAPI
from server import app

# Vercel expects a variable named 'app' or 'handler'
# Our FastAPI app is already named 'app' in server.py
handler = app
