# 🏗️ System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     TELEGRAM BOT                            │
│                    (bot.py - Entry Point)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  AGENT MANAGER                              │
│              (agent_manager.py)                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Intent Classification Engine                       │   │
│  │  • Regex pattern matching                          │   │
│  │  • Intent: greeting, knowledge, image, calc        │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Execution Plan Builder                            │   │
│  │  • Decides which models to use                     │   │
│  │  • Optimizes resource usage                        │   │
│  │  • Creates step-by-step plan                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────┬─────────────────────┬──────────────────┬─────────┘
          │                     │                  │
          │                     │                  │
          ▼                     ▼                  ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  VECTOR STORE    │  │   LLM MANAGER    │  │ VISION MANAGER   │
│ (vector_store.py)│  │ (llm_manager.py) │  │(vision_manager.py)│
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│ • Embeddings     │  │ • Ollama Client  │  │ • BLIP Model     │
│ • ChromaDB       │  │ • Chat History   │  │ • Image Proc     │
│ • Similarity     │  │ • RAG Prompt     │  │ • Tag Extract    │
└──────────────────┘  └──────────────────┘  └──────────────────┘
          │                     │                  │
          ▼                     ▼                  ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  KNOWLEDGE BASE  │  │     OLLAMA       │  │  TRANSFORMERS    │
│(knowledge_base.py)│  │  (llama3.2:3b)  │  │   (BLIP Model)   │
│                  │  │                  │  │                  │
│ • 10 Documents   │  │ • Local LLM     │  │ • Image Caption  │
│ • Metadata       │  │ • CPU/GPU       │  │ • PyTorch        │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## Component Interaction Flow

```
┌──────────┐
│  User    │
│ (Telegram)│
└────┬─────┘
     │ 1. Send message/image
     ▼
┌────────────────────────────────┐
│  bot.py                        │
│  • Receives update             │
│  • Routes to handler           │
└────┬───────────────────────────┘
     │ 2. Process command
     ▼
┌────────────────────────────────┐
│  Command Handler               │
│  • /ask → ask_command()        │
│  • [image] → handle_image()    │
│  • /explain → explain_command()│
└────┬───────────────────────────┘
     │ 3. Check intent
     ▼
┌────────────────────────────────┐
│  agent_manager.py              │
│  classify_intent(query)        │
│  ├─ Simple? → Template         │
│  ├─ Knowledge? → RAG           │
│  └─ Image? → Vision            │
└────┬───────────────────────────┘
     │ 4. Execute plan
     ▼
┌────────────────────────────────┐
│  Model Execution               │
│  ┌──────────────────────────┐  │
│  │ IF RAG NEEDED:           │  │
│  │ vector_store.search()    │  │
│  │      ↓                   │  │
│  │ llm_manager.generate()   │  │
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │ IF IMAGE:                │  │
│  │ vision_manager.caption() │  │
│  └──────────────────────────┘  │
└────┬───────────────────────────┘
     │ 5. Return result
     ▼
┌────────────────────────────────┐
│  markdown_utils.py             │
│  sanitize_markdown()           │
│  • Fix unclosed tags           │
│  • Escape special chars        │
└────┬───────────────────────────┘
     │ 6. Send response
     ▼
┌──────────┐
│  User    │
│ (Telegram)│
└──────────┘
```

---

## Directory Structure with Purpose

```
telegram-rag-bot/
│
├── bot.py ────────────────────────┐
│   Main application entry point   │
│   • Telegram bot handlers        │ LAYER 1: Interface
│   • Command routing              │
│   • User interaction             │
│                                  │
├── agent_manager.py ──────────────┤
│   Intelligent query router       │
│   • Intent classification        │ LAYER 2: Intelligence
│   • Execution planning           │
│   • Model selection              │
│                                  │
├── vector_store.py ───────────────┤
├── llm_manager.py                 │
├── vision_manager.py              │ LAYER 3: AI Models
│   Model managers                 │
│   • Abstraction over models      │
│   • Standardized interfaces      │
│                                  │
├── knowledge_base.py ─────────────┤
├── markdown_utils.py              │ LAYER 4: Utilities
│   Helper modules                 │
│   • Data storage                 │
│   • Text processing              │
│                                  │
├── requirements.txt ──────────────┤
├── .env                           │
├── Dockerfile                     │ LAYER 5: Configuration
├── docker-compose.yml             │
└── docker-entrypoint.sh ──────────┘
```

---

## Data Flow Patterns

### Pattern 1: Simple Query (Template Response)
```
User: "hi"
  ↓
bot.py (ask_command)
  ↓
agent_manager.classify_intent() → SIMPLE_GREETING
  ↓
agent_manager.get_simple_response() → "👋 Hello!"
  ↓
Response sent (0.01s)
```

### Pattern 2: Knowledge Query (RAG)
```
User: "What is Docker?"
  ↓
bot.py (ask_command)
  ↓
agent_manager.classify_intent() → KNOWLEDGE_SEARCH
  ↓
agent_manager.create_execution_plan()
  ├─ Step 1: search_knowledge_base
  └─ Step 2: generate_response
  ↓
vector_store.search("What is Docker?", k=3)
  ├─ Embed query → [0.23, -0.45, 0.67, ...]
  ├─ Search ChromaDB
  └─ Return top 3 chunks
  ↓
llm_manager.generate_rag_response(query, chunks, history)
  ├─ Build prompt with context
  ├─ Call Ollama API
  └─ Return generated text
  ↓
markdown_utils.sanitize_markdown(response)
  ↓
Response sent (3-5s)
```

### Pattern 3: Image Upload (Vision)
```
User: [Uploads image]
  ↓
bot.py (handle_image)
  ↓
vision_manager.generate_detailed_description(image_bytes)
  ├─ Load image → PIL.Image
  ├─ Preprocess → BLIP format
  ├─ Generate caption → "a brown dog..."
  └─ Extract tags → ["brown", "sitting", "grass"]
  ↓
Format response
  ↓
Response sent (2-4s)
```

---

## Component Dependencies

```
bot.py
  │
  ├──> agent_manager.py
  │      │
  │      ├──> (Uses for intent classification)
  │      └──> (Uses for execution planning)
  │
  ├──> vector_store.py
  │      │
  │      ├──> sentence_transformers (embeddings)
  │      ├──> chromadb (vector storage)
  │      └──> knowledge_base.py (document data)
  │
  ├──> llm_manager.py
  │      │
  │      └──> ollama (LLM API)
  │
  ├──> vision_manager.py
  │      │
  │      ├──> transformers (BLIP model)
  │      └──> torch (PyTorch)
  │
  └──> markdown_utils.py
         │
         └──> re (regex for sanitization)
```

---

## Technology Stack

### Programming Language
- **Python 3.11** - Modern, async-capable, great AI ecosystem

### AI/ML Frameworks
- **Ollama** - Local LLM runtime (llama3.2:3b)
- **Transformers** - Hugging Face library (BLIP vision)
- **PyTorch** - Deep learning framework
- **sentence-transformers** - Text embeddings

### Vector Database
- **ChromaDB** - Lightweight vector store
- Persistent storage in `./chroma_db/`
- Cosine similarity search

### Bot Framework
- **python-telegram-bot 21.0** - Async Telegram API wrapper
- Polling mode (no webhook needed)

### Utilities
- **python-dotenv** - Environment variables
- **Pillow** - Image processing
- **NumPy** - Numerical operations

---

## Deployment Architecture

### Docker Container Structure
```
┌─────────────────────────────────────────┐
│  Docker Container                       │
│  ┌───────────────────────────────────┐  │
│  │  Python 3.11 Runtime              │  │
│  │  ├─ bot.py (main process)         │  │
│  │  ├─ All Python modules            │  │
│  │  └─ Dependencies installed        │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Ollama Server (localhost:11434)  │  │
│  │  ├─ llama3.2:3b model             │  │
│  │  └─ API endpoint                  │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Volumes (Persistent)             │  │
│  │  ├─ /app/chroma_db (vector DB)    │  │
│  │  ├─ /root/.ollama (models)        │  │
│  │  └─ /root/.cache/huggingface      │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
         │
         │ Port 11434 (internal only)
         │ Telegram API (HTTPS)
         ↓
    Internet
```

---

## Security Architecture

### Data Privacy Layers
```
┌────────────────────────────────────┐
│  User Data                         │
│  • Messages                        │
│  • Images                          │
│  • Conversation history            │
└──────────┬─────────────────────────┘
           │
           │ Encrypted (HTTPS)
           ▼
┌────────────────────────────────────┐
│  Telegram API                      │
│  • SSL/TLS encrypted               │
└──────────┬─────────────────────────┘
           │
           ▼
┌────────────────────────────────────┐
│  Docker Container (Isolated)       │
│  • No external API calls           │
│  • All processing local            │
│  • Data in memory only             │
└──────────┬─────────────────────────┘
           │
           ▼
┌────────────────────────────────────┐
│  Persistent Storage (Volumes)      │
│  • Vector embeddings only          │
│  • No raw user data stored         │
│  • Models cached                   │
└────────────────────────────────────┘
```

### Security Features
- ✅ **No External APIs** - All AI processing local
- ✅ **Environment Variables** - Secrets not in code
- ✅ **Docker Isolation** - Sandboxed execution
- ✅ **Minimal Attack Surface** - Only Telegram API exposed
- ✅ **No Data Collection** - Messages processed in memory
- ✅ **Open Source** - Auditable code

---

## Scalability Considerations

### Current Capacity
- **Users**: Single bot handles ~100 concurrent users
- **Messages**: ~1000 messages/hour
- **Memory**: 4-8GB RAM
- **Storage**: ~5GB (models + vectors)

### Scaling Options

**Vertical Scaling** (Easier)
```
┌─────────────────────┐
│  Bigger Machine     │
│  • 16GB+ RAM        │
│  • GPU acceleration │
│  • Faster CPU       │
└─────────────────────┘
```

**Horizontal Scaling** (Advanced)
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Bot 1      │  │   Bot 2      │  │   Bot 3      │
│ @yourbot_1   │  │ @yourbot_2   │  │ @yourbot_3   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                         │
                ┌────────▼────────┐
                │  Load Balancer  │
                │  (Optional)     │
                └─────────────────┘
```

---

## Performance Characteristics

### Response Times
| Operation | Time | Bottleneck |
|-----------|------|------------|
| Template response | 0.01s | None |
| Vector search | 0.05s | CPU |
| LLM generation | 3-10s | CPU/GPU |
| Image caption | 2-5s | CPU/GPU |

### Resource Usage
| Component | CPU | RAM | Disk |
|-----------|-----|-----|------|
| Bot process | 5-10% | 200MB | - |
| Embeddings | Spike 20% | 500MB | - |
| ChromaDB | 2-5% | 100MB | 100MB |
| Ollama | 80-100% | 2GB | 2GB |
| BLIP | 50-80% | 1GB | 1GB |

### Optimization Points
1. **Caching** - Store frequent queries
2. **Batching** - Process multiple queries together
3. **Smaller Models** - Use llama3.2:1b for speed
4. **GPU** - 5-10x faster inference
5. **Quantization** - Reduce model size

---

This architecture document provides the foundation. Next, I'll document each code file in detail.