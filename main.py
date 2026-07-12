import asyncio
import threading
import requests
import sys

from maverik.audio.vocode_pipeline import run_vocode_pipeline

def warmup_model():
    """Silently loads the model into RAM at startup so it's instantly ready."""
    print("⏳ Warming up Ollama model in the background (preventing cold-start delays)...")
    try:
        requests.post("http://127.0.0.1:11434/api/generate", json={
            "model": "qwen3.5:2b",
            "prompt": "hi",
            "stream": False,
            "keep_alive": -1 # Keeps the model permanently loaded in memory
        }, timeout=300)
        print("⚡ Model warmup complete. MAVERIK is fully loaded.")
    except Exception as e:
        print(f"⚠️ Warmup failed: {e}")

def main():
    print("👐 Hands initialized. MAVERIK can now interact with the system.")
    print("Initializing MAVERIK Core...")
    
    # Warmup model in background while Vocode initializes
    threading.Thread(target=warmup_model, daemon=True).start()
    
    try:
        # 🚀 Launch the new Vocode Streaming Pipeline!
        # This completely replaces the old Ears, Transcriber, and TTS Queue loops.
        asyncio.run(run_vocode_pipeline())
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down MAVERIK...")
    except Exception as e:
        print(f"\n🚨 FATAL CRASH: {e}. MAVERIK Watchdog will reboot the daemon.")
        sys.exit(1) # Let systemd auto-restart it

if __name__ == "__main__":
    main()
