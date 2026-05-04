#!/usr/bin/env python3
"""
Simple example: Chatbot with Gemini and Kyros memory.

Setup:
1. pip install kyros-sdk google-generativeai
2. docker compose up -d
3. Create API key (see GEMINI_INTEGRATION.md)
4. Set your Gemini API key below
5. Run: python gemini_example.py
"""

import google.generativeai as genai
from kyros import KyrosClient

# ============================================================================
# CONFIGURATION - Change these values
# ============================================================================

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # Get from https://makersuite.google.com/app/apikey
KYROS_API_KEY = "my_secret_api_key_12345"    # From setup (see GEMINI_INTEGRATION.md)
KYROS_BASE_URL = "http://localhost:8000"
USER_ID = "demo-user"

# ============================================================================
# Initialize
# ============================================================================

genai.configure(api_key=GEMINI_API_KEY)
kyros = KyrosClient(api_key=KYROS_API_KEY, base_url=KYROS_BASE_URL)
model = genai.GenerativeModel('gemini-pro')

# ============================================================================
# Chat Function
# ============================================================================

def chat(message: str) -> str:
    """Chat with Gemini using Kyros for memory."""
    
    print(f"\n💬 You: {message}")
    
    # 1. Store user message in Kyros
    kyros.remember(
        agent_id=USER_ID,
        content=f"User: {message}",
        role="user",
        importance=0.7
    )
    
    # 2. Recall relevant context from Kyros
    context = kyros.recall(
        agent_id=USER_ID,
        query=message,
        k=5  # Get top 5 relevant memories
    )
    
    # 3. Build context for Gemini
    if context.results:
        context_text = "\n".join([
            f"- {m.content}" 
            for m in context.results
        ])
        context_prompt = f"\nPrevious context:\n{context_text}\n"
    else:
        context_prompt = ""
    
    # 4. Create prompt for Gemini
    prompt = f"""You are a helpful AI assistant with memory of past conversations.
{context_prompt}
User: {message}

Respond naturally, referencing past context when relevant:"""
    
    # 5. Get response from Gemini
    response = model.generate_content(prompt)
    reply = response.text
    
    # 6. Store assistant response in Kyros
    kyros.remember(
        agent_id=USER_ID,
        content=f"Assistant: {reply}",
        role="assistant",
        importance=0.7
    )
    
    print(f"🤖 Gemini: {reply}")
    
    return reply

# ============================================================================
# Main
# ============================================================================

def main():
    """Run interactive chat."""
    
    print("=" * 80)
    print("  Gemini + Kyros Memory Demo")
    print("=" * 80)
    print("\nThis chatbot remembers your conversation!")
    print("Type 'quit' to exit\n")
    
    # Check if Kyros is running
    try:
        import requests
        response = requests.get(f"{KYROS_BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Error: Kyros server is not responding")
            print("Start it with: docker compose up -d")
            return
    except:
        print("❌ Error: Cannot connect to Kyros server")
        print("Start it with: docker compose up -d")
        return
    
    print("✅ Connected to Kyros")
    
    # Check Gemini API key
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("\n❌ Error: Please set your Gemini API key in the script")
        print("Get it from: https://makersuite.google.com/app/apikey")
        return
    
    print("✅ Gemini API key configured")
    print("\n" + "=" * 80 + "\n")
    
    # Example conversation
    print("Let me show you how memory works...\n")
    
    # First message
    chat("Hi! My name is Alice and I love Python programming.")
    
    # Second message - should remember name
    chat("What's my name?")
    
    # Third message - should remember interest
    chat("What programming language do I like?")
    
    print("\n" + "=" * 80)
    print("\nSee how it remembered? Now try your own questions!")
    print("=" * 80 + "\n")
    
    # Interactive mode
    while True:
        try:
            user_input = input("💬 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Goodbye!")
                break
            
            chat(user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please check your configuration and try again.")
            break

if __name__ == "__main__":
    main()
