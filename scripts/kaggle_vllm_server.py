"""Kaggle GPU Serving Script for SAGE-Indic.

Run this script inside a free Kaggle Notebook with GPU enabled (Tesla T4 x2 or P100).
It spins up an OpenAI-compatible API server using vLLM (or Ollama) and exposes it
securely to your local SAGE-Indic application via ngrok or Cloudflare tunnel.

Setup in Kaggle:
1. Create a new notebook at https://www.kaggle.com
2. Settings -> Accelerator -> GPU T4 x2 (or P100)
3. Settings -> Internet -> ON
4. Paste and run the code cells below.
"""

# ==============================================================================
# CELL 1: Install Dependencies
# ==============================================================================
# !pip install -q vllm pyngrok

# ==============================================================================
# CELL 2: Start vLLM OpenAI Server (Qwen 2.5 7B Instruct or Sarvam-1 2B)
# ==============================================================================
"""
import subprocess
import time

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
# Alternative Indic model: "sarvamai/sarvam-1"

# Launch vLLM OpenAI-compatible server in the background
proc = subprocess.Popen([
    "python", "-m", "vllm.entrypoints.openai.api_server",
    "--model", MODEL_NAME,
    "--port", "8000",
    "--gpu-memory-utilization", "0.90",
    "--max-model-len", "4096",
    "--dtype", "half",
])

print(f"Starting vLLM server with model: {MODEL_NAME}...")
time.sleep(30)  # Wait for weights to load
"""

# ==============================================================================
# CELL 3: Create Public Tunnel & Get SAGE-Indic Endpoint
# ==============================================================================
"""
from pyngrok import ngrok

# Get free auth token from https://dashboard.ngrok.com/get-started/your-authtoken
NGROK_AUTH_TOKEN = "YOUR_NGROK_TOKEN_HERE"
ngrok.set_auth_token(NGROK_AUTH_TOKEN)

tunnel = ngrok.connect(8000)
public_url = tunnel.public_url

print("=" * 60)
print("SAGE-INDIC KAGGLE GPU SERVER READY!")
print("=" * 60)
print(f"Public URL: {public_url}/v1")
print("\nAdd the following lines to your local d:\\Sage-Indic\\.env file:")
print(f"SAGE_LLM_ENABLED=true")
print(f"SAGE_LLM_BASE_URL={public_url}/v1")
print(f"SAGE_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct")
print(f"SAGE_LLM_TIMEOUT=20")
print("=" * 60)
"""
