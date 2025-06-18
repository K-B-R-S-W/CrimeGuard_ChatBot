from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socket
import uvicorn
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.chat_router import router

# Setup basic logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)

app = FastAPI()

def get_local_ip():
    """Get the local IP address of the machine."""
    local_ip = "127.0.0.1"  # Default to localhost
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if not ip.startswith('172.'):
            local_ip = ip
    except Exception as e:
        logger.warning(f"Could not detect non-loopback IP, defaulting to 127.0.0.1: {e}")
    return local_ip

# CORS Configuration
host_ip = get_local_ip()
allowed_origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    f"http://{host_ip}:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    f"http://{host_ip}:3000"
]

logger.info(f"Allowed Origins for CORS: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router
app.include_router(router)

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    
    print(f"Server running. Access frontend at:")
    print(f"  http://localhost:{port}")
    print(f"  http://127.0.0.1:{port}")
    if host_ip != "127.0.0.1":
        print(f"  http://{host_ip}:{port}")
    print("Backend API endpoints available at /chat and /voice_chat")
    uvicorn.run(app, host=host, port=port) 