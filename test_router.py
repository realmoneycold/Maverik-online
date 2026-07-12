import sys
import os

# Add the current directory to python path
sys.path.append(os.getcwd())

from maverik.brain.router import analyze_intent
from main import get_fast_reply

phrases_to_test = [
    "good morning jarvis",
    "hey maverik, what's up?",
    "thank you so much",
    "open firefox and search for news",  # Should NOT match chitchat
    "what is the capital of france?"     # Should NOT match chitchat
]

print("Testing Semantic Router Intent Matching...\n" + "="*50)
for phrase in phrases_to_test:
    intent = analyze_intent(phrase)
    print(f"User Phrase: '{phrase}'")
    print(f"Matched Route: {intent}")
    
    if intent == "chitchat":
        print("⚡ Bypassing heavy agent... getting fast conversational reply:")
        reply = get_fast_reply(phrase)
        print(f"MAVERIK: {reply}")
    else:
        print("🧠 Routing to Heavy Agent Logic (Tool Calling)...")
    print("-" * 50)
