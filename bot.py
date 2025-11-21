"""
Telegram Agentic RAG Bot
Uses intelligent routing to decide which models to call
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Import components
from vector_store import VectorStore
from llm_manager import LLMManager
from vision_manager import VisionManager
from agent_manager import AgentManager, AgenticQueryProcessor
from markdown_utils import sanitize_markdown

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global components
vector_store = None
llm_manager = None
vision_manager = None
agent_processor = None
agent_manager = None

# User conversation history
user_history = {}

def initialize_components():
    """Initialize all AI components"""
    global vector_store, llm_manager, vision_manager, agent_processor, agent_manager
    
    logger.info("=" * 60)
    logger.info("🤖 Initializing Agentic Telegram RAG Bot")
    logger.info("=" * 60)
    
    # 1. Initialize Vector Store
    logger.info("\n📚 [1/5] Initializing Vector Store...")
    embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    vector_store = VectorStore(embedding_model_name=embedding_model)
    logger.info(f"✓ Vector store ready: {vector_store.get_stats()}")
    
    # 2. Initialize LLM
    logger.info("\n🧠 [2/5] Initializing LLM (Ollama)...")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    llm_manager = LLMManager(model_name=ollama_model, host=ollama_host)
    logger.info(f"✓ LLM ready: {ollama_model}")
    
    # 3. Initialize Vision Model
    logger.info("\n👁️ [3/5] Initializing Vision Model...")
    vision_model = os.getenv("VISION_MODEL", "Salesforce/blip-image-captioning-base")
    vision_manager = VisionManager(model_name=vision_model)
    logger.info(f"✓ Vision model ready")
    
    # 4. Initialize Agent Manager
    logger.info("\n🎯 [4/5] Initializing Agent Manager...")
    agent_manager = AgentManager()
    logger.info(f"✓ Agent manager ready")
    
    # 5. Initialize Agentic Processor
    logger.info("\n🚀 [5/5] Initializing Agentic Query Processor...")
    agent_processor = AgenticQueryProcessor(
        vector_store=vector_store,
        llm_manager=llm_manager,
        vision_manager=vision_manager
    )
    logger.info(f"✓ Agentic processor ready")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ All components initialized successfully!")
    logger.info("🎯 Using intelligent query routing")
    logger.info("=" * 60 + "\n")

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
    """Start command"""
    welcome_msg = """
🤖 **Agentic RAG Bot - Intelligent AI Assistant**

I use **intelligent query routing** to provide fast, efficient responses!

**🎯 How I Work:**
• **Simple questions** → Instant template response
• **Knowledge queries** → Search docs + LLM
• **Complex analysis** → Multi-step reasoning
• **Images** → Vision model analysis

**💡 Available Commands:**

📚 **Ask Questions**
`/ask <question>` - Ask anything!
Examples:
• `/ask hi` → Instant response ⚡
• `/ask What is Docker?` → RAG search 🔍
• `/ask Compare Python and Java` → Deep analysis 🧠

🖼️ **Image Analysis**
Send any image → Automatic description

🎯 **Agent Features**
`/explain <question>` - Show execution plan
`/stats` - System statistics
`/summarize` - Conversation summary
`/clear` - Clear history

**✨ Smart Features:**
✅ Automatic intent detection
✅ Optimal model selection  
✅ Fast template responses
✅ Cost-efficient processing

Try: `/explain What is machine learning?`
"""
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def explain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explain execution plan for a query"""
    query = ' '.join(context.args) if context.args else ""
    
    if not query:
        await update.message.reply_text(
            "Usage: `/explain <your question>`\n\n"
            "Example: `/explain What is Docker?`\n\n"
            "I'll show you how I would process this query!",
            parse_mode='Markdown'
        )
        return
    
    # Create execution plan
    plan = agent_manager.create_execution_plan(query)
    plan = agent_manager.optimize_plan(plan)
    
    # Get explanation
    explanation = agent_manager.explain_plan(plan)
    
    # Format response
    response = f"""🎯 **Execution Plan Analysis**

**Query:** {query}

{explanation}

**Cost Optimization:**
{'✅ Using fast template response' if plan['simple_response'] else '🔍 Using AI models for best accuracy'}
"""
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle queries with agentic routing"""
    user_id = update.effective_user.id
    query = ' '.join(context.args) if context.args else ""
    
    if not query:
        await update.message.reply_text(
            "Please provide a question!\n\n"
            "Example: `/ask What is Python?`",
            parse_mode='Markdown'
        )
        return
    
    # Show processing indicator
    status_msg = await update.message.reply_text("🤖 Analyzing query...")
    
    try:
        # Get conversation history
        history = get_user_history(user_id)
        
        # Process with agent
        logger.info(f"Processing query: {query}")
        result = agent_processor.process_query(
            query=query,
            conversation_history=history,
            explain_plan=False
        )
        
        # Validate result
        if not result or not isinstance(result, dict):
            logger.error(f"Invalid result from agent_processor: {result}")
            await status_msg.edit_text("❌ Internal error. Please try again.")
            return
        
        # Add to history
        add_to_history(user_id, "user", query)
        add_to_history(user_id, "assistant", result.get('answer', ''))
        
        # Format response
        response = result.get('answer', 'No response generated')
        
        # Add sources if available
        if result.get('sources'):
            sources_text = "\n".join([f"• {src}" for src in set(result['sources'])])
            response += f"\n\n📚 **Sources:**\n{sources_text}"
        
        # Add routing info
        plan = result.get('plan', {})
        intent = plan.get('intent', 'unknown') if plan else 'unknown'
        if intent == 'simple_greeting':
            response += "\n\n⚡ *Fast response (no AI models used)*"
        elif result.get('sources'):
            response += f"\n\n🧠 *Powered by {llm_manager.model_name} with RAG*"
        else:
            response += f"\n\n🤖 *Powered by {llm_manager.model_name}*"
        
        # Try Markdown first, fallback to plain text if it fails
        try:
            await status_msg.edit_text(response, parse_mode='Markdown')
        except Exception as markdown_error:
            logger.warning(f"Markdown parsing failed, sending as plain text: {markdown_error}")
            # Remove problematic markdown and send as plain text
            await status_msg.edit_text(response, parse_mode=None)
        
    except Exception as e:
        logger.error(f"Error in ask_command: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ Sorry, I encountered an error. Please check:\n"
            "• Is Ollama running? (`ollama serve`)\n"
            "• Is the model downloaded? (`ollama pull llama3.2:3b`)"
        )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image uploads - DIRECT vision processing only"""
    user_id = update.effective_user.id
    
    if not update.message.photo:
        await update.message.reply_text("Please send an image.")
        return
    
    status_msg = await update.message.reply_text("🖼️ Analyzing image with BLIP model...")
    
    try:
        # Get image
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        logger.info(f"Processing image ({len(image_bytes)} bytes) - DIRECT vision call")
        
        # CRITICAL: Call vision manager DIRECTLY
        # DO NOT use agent_processor or LLM for images
        result = vision_manager.generate_detailed_description(bytes(image_bytes))
        
        # Format response
        caption = result.get('caption', 'Unable to analyze image')
        tags = result.get('tags', [])
        tags_str = ", ".join(tags) if tags else "N/A"
        
        response = f"""**Caption:** {caption}

**Tags:** {tags_str}

👁️ *Analyzed by {vision_manager.model_name.split('/')[-1]}*"""
        
        # Add to history
        add_to_history(user_id, "user", "[Uploaded an image]")
        add_to_history(user_id, "assistant", caption)
        
        logger.info(f"Image processed successfully: {caption[:50]}...")
        
        await status_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in handle_image: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ Failed to process image.\n\n"
            "Please ensure:\n"
            "• Image is JPG or PNG\n"
            "• File size < 5MB\n"
            "• Vision model is loaded"
        )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system statistics"""
    stats = vector_store.get_stats()
    
    stats_msg = f"""
📊 **System Statistics**

**🎯 Agent Status:** Active
**📚 Documents:** {stats['total_documents']}
**🔢 Embeddings:** {stats['embedding_model']} dimensions

**🤖 Models:**
• LLM: `{llm_manager.model_name}`
• Vision: `{vision_manager.model_name.split('/')[-1]}`
• Embeddings: `{vector_store.embedding_model}`

**👥 Users:** {len(user_history)} active conversations

**💡 Agent Features:**
✅ Intent classification
✅ Smart model routing
✅ Template responses for speed
✅ RAG for knowledge queries
"""
    await update.message.reply_text(stats_msg, parse_mode='Markdown')

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

_Messages: {len(history)}_
_Generated by {llm_manager.model_name}_"""
        
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
        await update.message.reply_text(f"🗑️ Cleared {msg_count} messages")
    else:
        await update.message.reply_text("No history to clear!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    await start(update, context)

def main():
    """Main function"""
    try:
        initialize_components()
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        logger.error("\nPlease ensure:")
        logger.error("1. Ollama is running: ollama serve")
        logger.error("2. Model is downloaded: ollama pull llama3.2:3b")
        return
    
    # Get token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found!")
        return
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("explain", explain_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("summarize", summarize_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    
    # Start bot
    logger.info("🚀 Agentic Bot is running!")
    logger.info("Press Ctrl+C to stop\n")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()