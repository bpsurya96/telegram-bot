"""
Telegram RAG Bot with Local Models
Main bot implementation using Ollama and local vision models
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Import our custom modules
from vector_store import VectorStore
from llm_manager import LLMManager
from vision_manager import VisionManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize components
vector_store = None
llm_manager = None
vision_manager = None

# User conversation history
user_history = {}

def initialize_components():
    """Initialize all AI components"""
    global vector_store, llm_manager, vision_manager
    
    logger.info("=" * 50)
    logger.info("Initializing Telegram RAG Bot")
    logger.info("=" * 50)
    
    # 1. Initialize Vector Store
    embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    vector_store = VectorStore(embedding_model_name=embedding_model)
    logger.info(f"Vector store stats: {vector_store.get_stats()}")
    
    # 2. Initialize LLM (Ollama)
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    llm_manager = LLMManager(model_name=ollama_model, host=ollama_host)
    
    # 3. Initialize Vision Model
    vision_model = os.getenv("VISION_MODEL", "Salesforce/blip-image-captioning-base")
    vision_manager = VisionManager(model_name=vision_model)
    
    logger.info("=" * 50)
    logger.info("✓ All components initialized successfully!")
    logger.info("=" * 50)

def get_user_history(user_id: int) -> list:
    """Get conversation history for user"""
    max_length = int(os.getenv("MAX_HISTORY_LENGTH", 5))
    return user_history.get(user_id, [])[-max_length:]

def add_to_history(user_id: int, role: str, content: str):
    """Add message to conversation history"""
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append({"role": role, "content": content})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - welcome message"""
    welcome_msg = """
🤖 **Welcome to Local GenAI Bot!**

I use fully local AI models running on this server:
• 🧠 Ollama (LLaMA 3.2) for answering questions
• 📚 Sentence-Transformers for semantic search
• 🖼️ BLIP for image descriptions

**Available Commands:**

📚 **RAG (Knowledge Base)**
`/ask <question>` - Ask about programming, ML, DevOps
Example: `/ask What is Python used for?`

🖼️ **Image Description**
Send me any image and I'll describe it!

💬 **Conversation**
`/summarize` - Summarize our chat
`/clear` - Clear conversation history
`/stats` - Show system statistics
`/help` - Show this message

**How it works:**
1. Your questions search our knowledge base
2. Relevant documents are retrieved
3. Local LLM generates answers with context
4. All processing happens locally! 🔒

Ready to start! Try `/ask What is Docker?`
"""
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    await start(update, context)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system statistics"""
    stats = vector_store.get_stats()
    
    stats_msg = f"""
📊 **System Statistics**

**Vector Store:**
• Documents: {stats['total_documents']}
• Embedding Dimensions: {stats['embedding_model']}

**Models:**
• LLM: {llm_manager.model_name}
• Vision: {vision_manager.model_name}
• Embeddings: {vector_store.embedding_model}

**User Stats:**
• Conversations tracked: {len(user_history)}
"""
    await update.message.reply_text(stats_msg, parse_mode='Markdown')

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle RAG queries"""
    user_id = update.effective_user.id
    
    # Extract query
    query = ' '.join(context.args) if context.args else ""
    
    if not query:
        await update.message.reply_text(
            "Please provide a question!\n\n"
            "Example: `/ask What is machine learning?`",
            parse_mode='Markdown'
        )
        return
    
    # Send processing message
    status_msg = await update.message.reply_text("🔍 Searching knowledge base...")
    
    try:
        # 1. Retrieve relevant context
        k = int(os.getenv("RETRIEVAL_K", 3))
        logger.info(f"Searching for: {query}")
        
        context_chunks = vector_store.search(query, k=k)
        logger.info(f"Retrieved {len(context_chunks)} chunks")
        
        # Update status
        await status_msg.edit_text("🧠 Generating answer with local LLM...")
        
        # 2. Get conversation history
        history = get_user_history(user_id)
        
        # 3. Generate response using LLM
        response = llm_manager.generate_rag_response(
            query=query,
            context_chunks=context_chunks,
            conversation_history=history
        )
        
        # 4. Format response with sources
        sources = set([chunk['source'] for chunk in context_chunks])
        sources_text = "\n".join([f"• {src}" for src in sources])
        
        full_response = f"""{response}

📚 **Sources:**
{sources_text}

_Generated by {llm_manager.model_name}_"""
        
        # 5. Update history
        add_to_history(user_id, "user", query)
        add_to_history(user_id, "assistant", response)
        
        # 6. Send response
        await status_msg.edit_text(full_response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in ask_command: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ Sorry, I encountered an error. Please check:\n"
            "• Is Ollama running? (`ollama serve`)\n"
            "• Is the model downloaded? (`ollama pull llama3.2:3b`)"
        )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image uploads"""
    user_id = update.effective_user.id
    
    if not update.message.photo:
        await update.message.reply_text("Please send an image.")
        return
    
    status_msg = await update.message.reply_text("🖼️ Analyzing image with local BLIP model...")
    
    try:
        # Get largest photo
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        
        # Download image
        image_bytes = await photo_file.download_as_bytearray()
        logger.info(f"Processing image of size {len(image_bytes)} bytes")
        
        # Update status
        await status_msg.edit_text("🎨 Generating caption and tags...")
        
        # Analyze image
        description = vision_manager.analyze_image(bytes(image_bytes))
        
        # Add to history
        add_to_history(user_id, "user", "[Uploaded an image]")
        add_to_history(user_id, "assistant", description)
        
        # Send description
        await status_msg.edit_text(description, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in handle_image: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ Failed to process image. Please ensure:\n"
            "• Image is in a supported format (JPG, PNG)\n"
            "• Image size is reasonable (<5MB)"
        )

async def summarize_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Summarize conversation"""
    user_id = update.effective_user.id
    history = get_user_history(user_id)
    
    if not history:
        await update.message.reply_text("No conversation to summarize yet!")
        return
    
    status_msg = await update.message.reply_text("📝 Generating summary...")
    
    try:
        summary = llm_manager.summarize_conversation(history)
        
        response = f"""📝 **Conversation Summary:**

{summary}

_Messages in history: {len(history)}_"""
        
        await status_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in summarize: {e}")
        await status_msg.edit_text("❌ Failed to generate summary")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear conversation history"""
    user_id = update.effective_user.id
    
    if user_id in user_history:
        msg_count = len(user_history[user_id])
        del user_history[user_id]
        await update.message.reply_text(f"🗑️ Cleared {msg_count} messages from history")
    else:
        await update.message.reply_text("No history to clear!")

def main():
    """Main function"""
    # Initialize components
    try:
        initialize_components()
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        logger.error("\nPlease ensure:")
        logger.error("1. Ollama is running: ollama serve")
        logger.error("2. Model is downloaded: ollama pull llama3.2:3b")
        logger.error("3. Python packages are installed: pip install -r requirements.txt")
        return
    
    # Get bot token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment!")
        return
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("summarize", summarize_command))
    application.add_handler(CommandHandler("clear", clear_command))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    
    # Start bot
    logger.info("🚀 Bot is now running!")
    logger.info("Press Ctrl+C to stop")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()