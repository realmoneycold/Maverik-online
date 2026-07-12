import os
from semantic_router import Route
from semantic_router.encoders import HuggingFaceEncoder
from semantic_router import SemanticRouter

# Define the routes
chitchat = Route(
    name="chitchat",
    utterances=[
        "hello",
        "hi",
        "hey there",
        "good morning",
        "good evening",
        "goodnight",
        "how are you",
        "who are you",
        "thanks",
        "thank you",
        "what's up",
        "are you there",
        "wake up",
        "good morning jarvis",
        "hey maverik",
        "goodnight maverik",
        "thank you maverik",
        "thank you so much",
        "hey maverik, what's up?"
    ],
    score_threshold=0.5
)

web_search = Route(
    name="web_search",
    utterances=[
        "search the web for",
        "look up",
        "find information about",
        "what is the latest news",
        "who is",
        "what is",
        "can you google",
        "search for"
    ],
    score_threshold=0.5
)

system_command = Route(
    name="system_command",
    utterances=[
        "open firefox",
        "open chrome",
        "launch the terminal",
        "run a command",
        "create a new file",
        "delete the file",
        "check my system memory",
        "what is my ip address"
    ],
    score_threshold=0.5
)

def get_router_layer():
    print("⏳ Initializing Semantic Router (Fast Intent Matching)...")
    # Using a fast, lightweight local embedding model
    encoder = HuggingFaceEncoder(name="sentence-transformers/all-MiniLM-L6-v2", device="cpu")
    routes = [chitchat, web_search, system_command]
    rl = SemanticRouter(encoder=encoder, routes=routes, auto_sync="local")
    return rl

# Singleton instance
router_layer = None

def analyze_intent(text: str) -> str:
    """
    Analyzes the text and returns the matching route name (e.g., 'chitchat').
    Returns None if no route matches (meaning it should go to the heavy tool agent).
    """
    global router_layer
    if router_layer is None:
        try:
            router_layer = get_router_layer()
        except Exception as e:
            print(f"Failed to initialize Semantic Router: {e}")
            return None
        
    route_choice = router_layer(text)
    return route_choice.name
