# Using Kyros with Google Gemini

Complete guide to building AI agents with Gemini and Kyros memory.

## Quick Setup

### 1. Start Kyros

```bash
docker compose up -d
```

### 2. Create API Key

```bash
docker compose exec postgres psql -U kyros -d kyros
```

```sql
INSERT INTO tenants (tenant_id, name, api_key_hash, tier, created_at)
VALUES (
  'my-tenant',
  'My Organization',
  encode(digest('my_secret_api_key_12345', 'sha256'), 'hex'),
  'pro',
  NOW()
);
\q
```

### 3. Get Your Gemini API Key

Get your free API key from: https://makersuite.google.com/app/apikey

## Python Integration

### Install Dependencies

```bash
pip install kyros-sdk google-generativeai
```

### Basic Chatbot with Memory

```python
import google.generativeai as genai
from kyros import KyrosClient

# Configure
genai.configure(api_key="YOUR_GEMINI_API_KEY")
kyros = KyrosClient(
    api_key="my_secret_api_key_12345",
    base_url="http://localhost:8000"
)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-pro')

def chat_with_memory(user_id: str, message: str) -> str:
    """Chat with Gemini using Kyros for memory."""
    
    # 1. Store user message
    kyros.remember(
        agent_id=user_id,
        content=f"User: {message}",
        role="user",
        importance=0.7
    )
    
    # 2. Recall relevant context
    context = kyros.recall(
        agent_id=user_id,
        query=message,
        k=5
    )
    
    # 3. Build context for Gemini
    context_text = "\n".join([
        f"- {m.content}" 
        for m in context.results
    ])
    
    # 4. Create prompt with context
    prompt = f"""You are a helpful AI assistant with memory of past conversations.

Previous context:
{context_text}

User: {message}

Respond naturally, referencing past context when relevant."""
    
    # 5. Get Gemini response
    response = model.generate_content(prompt)
    reply = response.text
    
    # 6. Store assistant response
    kyros.remember(
        agent_id=user_id,
        content=f"Assistant: {reply}",
        role="assistant",
        importance=0.7
    )
    
    return reply

# Use it!
print(chat_with_memory("user-123", "Hi! My name is Alice and I love Python."))
print(chat_with_memory("user-123", "What's my name?"))
print(chat_with_memory("user-123", "What programming language do I like?"))
```

### Advanced: Streaming Responses

```python
import google.generativeai as genai
from kyros import KyrosClient

genai.configure(api_key="YOUR_GEMINI_API_KEY")
kyros = KyrosClient(
    api_key="my_secret_api_key_12345",
    base_url="http://localhost:8000"
)

model = genai.GenerativeModel('gemini-pro')

def chat_streaming(user_id: str, message: str):
    """Chat with streaming responses."""
    
    # Store user message
    kyros.remember(
        agent_id=user_id,
        content=f"User: {message}",
        role="user"
    )
    
    # Recall context
    context = kyros.recall(user_id, message, k=5)
    context_text = "\n".join([f"- {m.content}" for m in context.results])
    
    # Create prompt
    prompt = f"""Previous context:
{context_text}

User: {message}

Respond naturally:"""
    
    # Stream response
    response = model.generate_content(prompt, stream=True)
    
    full_reply = ""
    for chunk in response:
        if chunk.text:
            print(chunk.text, end="", flush=True)
            full_reply += chunk.text
    
    print()  # New line
    
    # Store complete response
    kyros.remember(
        agent_id=user_id,
        content=f"Assistant: {full_reply}",
        role="assistant"
    )
    
    return full_reply

# Use it
chat_streaming("user-123", "Tell me a story about AI")
```

### Multi-Turn Conversation

```python
import google.generativeai as genai
from kyros import KyrosClient

genai.configure(api_key="YOUR_GEMINI_API_KEY")
kyros = KyrosClient(
    api_key="my_secret_api_key_12345",
    base_url="http://localhost:8000"
)

class GeminiWithMemory:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.model = genai.GenerativeModel('gemini-pro')
        self.chat = self.model.start_chat(history=[])
    
    def send_message(self, message: str) -> str:
        """Send message and maintain memory."""
        
        # Store user message
        kyros.remember(
            agent_id=self.user_id,
            content=f"User: {message}",
            role="user"
        )
        
        # Recall relevant context
        context = kyros.recall(
            agent_id=self.user_id,
            query=message,
            k=5
        )
        
        # Add context to message
        if context.results:
            context_text = "\n".join([
                f"- {m.content}" 
                for m in context.results
            ])
            enhanced_message = f"[Context: {context_text}]\n\n{message}"
        else:
            enhanced_message = message
        
        # Get response
        response = self.chat.send_message(enhanced_message)
        reply = response.text
        
        # Store response
        kyros.remember(
            agent_id=self.user_id,
            content=f"Assistant: {reply}",
            role="assistant"
        )
        
        return reply

# Use it
chat = GeminiWithMemory("user-123")

print(chat.send_message("Hi! I'm learning Python."))
print(chat.send_message("Can you help me with lists?"))
print(chat.send_message("What was I learning about?"))
```

### Store User Preferences

```python
import google.generativeai as genai
from kyros import KyrosClient

genai.configure(api_key="YOUR_GEMINI_API_KEY")
kyros = KyrosClient(
    api_key="my_secret_api_key_12345",
    base_url="http://localhost:8000"
)

model = genai.GenerativeModel('gemini-pro')

def extract_and_store_preferences(user_id: str, message: str):
    """Extract preferences from conversation and store them."""
    
    # Ask Gemini to extract preferences
    extraction_prompt = f"""Extract any user preferences from this message.
Return them as subject-predicate-value triples.

Message: {message}

Format: subject|predicate|value
Example: user|prefers|dark_mode

If no preferences, return "NONE"."""
    
    response = model.generate_content(extraction_prompt)
    
    # Parse and store preferences
    for line in response.text.strip().split('\n'):
        if line == "NONE" or not line:
            continue
        
        try:
            subject, predicate, value = line.split('|')
            kyros.store_fact(
                agent_id=user_id,
                subject=subject.strip(),
                predicate=predicate.strip(),
                value=value.strip(),
                confidence=0.8
            )
            print(f"Stored: {subject} {predicate} {value}")
        except:
            pass

# Use it
extract_and_store_preferences(
    "user-123",
    "I prefer Python over JavaScript and I love dark mode"
)

# Query preferences later
prefs = kyros.query_facts("user-123", "user preferences", k=10)
for fact in prefs.results:
    print(f"{fact.subject} {fact.predicate} {fact.value}")
```

## TypeScript Integration

### Install Dependencies

```bash
npm install @kyros/sdk @google/generative-ai
```

### Basic Chatbot

```typescript
import { GoogleGenerativeAI } from '@google/generative-ai';
import { KyrosClient } from '@kyros/sdk';

const genai = new GoogleGenerativeAI('YOUR_GEMINI_API_KEY');
const kyros = new KyrosClient({
  apiKey: 'my_secret_api_key_12345',
  baseUrl: 'http://localhost:8000'
});

const model = genai.getGenerativeModel({ model: 'gemini-pro' });

async function chatWithMemory(userId: string, message: string): Promise<string> {
  // Store user message
  await kyros.remember(userId, `User: ${message}`, { role: 'user' });
  
  // Recall context
  const context = await kyros.recall(userId, message, { k: 5 });
  
  // Build context
  const contextText = context.results
    .map(m => `- ${m.content}`)
    .join('\n');
  
  // Create prompt
  const prompt = `Previous context:
${contextText}

User: ${message}

Respond naturally:`;
  
  // Get response
  const result = await model.generateContent(prompt);
  const reply = result.response.text();
  
  // Store response
  await kyros.remember(userId, `Assistant: ${reply}`, { role: 'assistant' });
  
  return reply;
}

// Use it
const response = await chatWithMemory('user-123', 'Hi! I love TypeScript.');
console.log(response);
```

### Streaming Responses

```typescript
import { GoogleGenerativeAI } from '@google/generative-ai';
import { KyrosClient } from '@kyros/sdk';

const genai = new GoogleGenerativeAI('YOUR_GEMINI_API_KEY');
const kyros = new KyrosClient({
  apiKey: 'my_secret_api_key_12345',
  baseUrl: 'http://localhost:8000'
});

const model = genai.getGenerativeModel({ model: 'gemini-pro' });

async function chatStreaming(userId: string, message: string) {
  // Store user message
  await kyros.remember(userId, `User: ${message}`, { role: 'user' });
  
  // Recall context
  const context = await kyros.recall(userId, message, { k: 5 });
  const contextText = context.results.map(m => `- ${m.content}`).join('\n');
  
  // Create prompt
  const prompt = `Previous context:\n${contextText}\n\nUser: ${message}\n\nRespond:`;
  
  // Stream response
  const result = await model.generateContentStream(prompt);
  
  let fullReply = '';
  for await (const chunk of result.stream) {
    const text = chunk.text();
    process.stdout.write(text);
    fullReply += text;
  }
  
  console.log(); // New line
  
  // Store response
  await kyros.remember(userId, `Assistant: ${fullReply}`, { role: 'assistant' });
  
  return fullReply;
}

// Use it
await chatStreaming('user-123', 'Tell me about AI');
```

## Real-World Examples

### 1. Personal Assistant

```python
import google.generativeai as genai
from kyros import KyrosClient
from datetime import datetime

genai.configure(api_key="YOUR_GEMINI_API_KEY")
kyros = KyrosClient(
    api_key="my_secret_api_key_12345",
    base_url="http://localhost:8000"
)

model = genai.GenerativeModel('gemini-pro')

class PersonalAssistant:
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    def process_message(self, message: str) -> str:
        """Process user message with memory."""
        
        # Store message
        kyros.remember(
            agent_id=self.user_id,
            content=f"User: {message}",
            role="user",
            metadata={"timestamp": datetime.now().isoformat()}
        )
        
        # Recall relevant memories
        context = kyros.recall(self.user_id, message, k=10)
        
        # Get user facts
        facts = kyros.query_facts(self.user_id, "user preferences", k=20)
        
        # Build comprehensive context
        memory_context = "\n".join([f"- {m.content}" for m in context.results])
        facts_context = "\n".join([
            f"- {f.subject} {f.predicate} {f.value}" 
            for f in facts.results
        ])
        
        # Create prompt
        prompt = f"""You are a personal assistant with access to the user's history.

User Facts:
{facts_context}

Recent Context:
{memory_context}

Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}

User: {message}

Respond helpfully, using context when relevant:"""
        
        # Get response
        response = model.generate_content(prompt)
        reply = response.text
        
        # Store response
        kyros.remember(
            agent_id=self.user_id,
            content=f"Assistant: {reply}",
            role="assistant"
        )
        
        return reply

# Use it
assistant = PersonalAssistant("user-123")

# Store some facts
kyros.store_fact("user-123", "user", "name", "Alice")
kyros.store_fact("user-123", "user", "timezone", "PST")
kyros.store_fact("user-123", "user", "prefers", "morning meetings")

# Chat
print(assistant.process_message("Schedule a meeting for me"))
print(assistant.process_message("What time works best for me?"))
```

### 2. Customer Support Agent

```python
import google.generativeai as genai
from kyros import KyrosClient

genai.configure(api_key="YOUR_GEMINI_API_KEY")
kyros = KyrosClient(
    api_key="my_secret_api_key_12345",
    base_url="http://localhost:8000"
)

model = genai.GenerativeModel('gemini-pro')

class SupportAgent:
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
    
    def handle_query(self, query: str) -> str:
        """Handle customer support query."""
        
        # Store query
        kyros.remember(
            agent_id=self.customer_id,
            content=f"Customer: {query}",
            role="user",
            metadata={"type": "support_query"}
        )
        
        # Get customer history
        history = kyros.recall(self.customer_id, query, k=10)
        
        # Get customer info
        customer_info = kyros.query_facts(
            self.customer_id,
            "customer information",
            k=20
        )
        
        # Build context
        history_text = "\n".join([f"- {m.content}" for m in history.results])
        info_text = "\n".join([
            f"- {f.subject} {f.predicate} {f.value}"
            for f in customer_info.results
        ])
        
        # Create prompt
        prompt = f"""You are a customer support agent.

Customer Information:
{info_text}

Support History:
{history_text}

Customer Query: {query}

Provide helpful support, referencing past issues when relevant:"""
        
        # Get response
        response = model.generate_content(prompt)
        reply = response.text
        
        # Store response
        kyros.remember(
            agent_id=self.customer_id,
            content=f"Support: {reply}",
            role="assistant",
            metadata={"type": "support_response"}
        )
        
        return reply

# Use it
support = SupportAgent("customer-456")

# Store customer info
kyros.store_fact("customer-456", "customer", "subscription", "Pro Plan")
kyros.store_fact("customer-456", "customer", "joined", "2024-01-15")

# Handle queries
print(support.handle_query("I can't log in"))
print(support.handle_query("What's my subscription level?"))
```

### 3. Code Assistant

```python
import google.generativeai as genai
from kyros import KyrosClient

genai.configure(api_key="YOUR_GEMINI_API_KEY")
kyros = KyrosClient(
    api_key="my_secret_api_key_12345",
    base_url="http://localhost:8000"
)

model = genai.GenerativeModel('gemini-pro')

class CodeAssistant:
    def __init__(self, developer_id: str):
        self.developer_id = developer_id
    
    def help_with_code(self, question: str) -> str:
        """Help with coding questions."""
        
        # Store question
        kyros.remember(
            agent_id=self.developer_id,
            content=f"Developer: {question}",
            role="user"
        )
        
        # Get developer preferences
        prefs = kyros.query_facts(
            self.developer_id,
            "developer preferences",
            k=20
        )
        
        # Get relevant past code discussions
        context = kyros.recall(self.developer_id, question, k=5)
        
        # Build context
        prefs_text = "\n".join([
            f"- {f.subject} {f.predicate} {f.value}"
            for f in prefs.results
        ])
        context_text = "\n".join([f"- {m.content}" for m in context.results])
        
        # Create prompt
        prompt = f"""You are a code assistant.

Developer Preferences:
{prefs_text}

Previous Discussions:
{context_text}

Question: {question}

Provide code examples in the developer's preferred language:"""
        
        # Get response
        response = model.generate_content(prompt)
        reply = response.text
        
        # Store response
        kyros.remember(
            agent_id=self.developer_id,
            content=f"Assistant: {reply}",
            role="assistant"
        )
        
        return reply

# Use it
assistant = CodeAssistant("dev-789")

# Store preferences
kyros.store_fact("dev-789", "developer", "prefers", "Python")
kyros.store_fact("dev-789", "developer", "uses", "FastAPI")
kyros.store_fact("dev-789", "developer", "style", "type hints")

# Ask questions
print(assistant.help_with_code("How do I create an API endpoint?"))
print(assistant.help_with_code("Show me the syntax again"))
```

## Environment Variables

Add to your `.env` file:

```bash
# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Kyros Configuration
KYROS_API_KEY=my_secret_api_key_12345
KYROS_BASE_URL=http://localhost:8000
```

Load in your code:

```python
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
kyros = KyrosClient(
    api_key=os.getenv("KYROS_API_KEY"),
    base_url=os.getenv("KYROS_BASE_URL")
)
```

## Tips & Best Practices

### 1. Context Management

```python
# Limit context to most relevant memories
context = kyros.recall(user_id, message, k=5, min_relevance=0.7)
```

### 2. Importance Scoring

```python
# Mark important messages
kyros.remember(
    agent_id=user_id,
    content=message,
    importance=0.9  # High importance = slower decay
)
```

### 3. Metadata for Filtering

```python
# Add metadata for better organization
kyros.remember(
    agent_id=user_id,
    content=message,
    metadata={
        "category": "support",
        "priority": "high",
        "language": "en"
    }
)
```

### 4. Session Management

```python
# Group related conversations
session_id = f"session-{datetime.now().strftime('%Y%m%d')}"
kyros.remember(
    agent_id=user_id,
    content=message,
    session_id=session_id
)
```

## Next Steps

- **Explore Gemini Models:** Try `gemini-pro-vision` for images
- **Add Function Calling:** Use Gemini's function calling with Kyros
- **Build Multi-Agent Systems:** Multiple agents sharing memory
- **Deploy to Production:** See `docs/self-hosting.md`

## Resources

- **Gemini API Docs:** https://ai.google.dev/docs
- **Kyros Python SDK:** `docs/python-sdk.md`
- **Kyros TypeScript SDK:** `docs/typescript-sdk.md`
- **Get Gemini API Key:** https://makersuite.google.com/app/apikey

---

**Start building AI agents with Gemini and persistent memory!** 🚀
