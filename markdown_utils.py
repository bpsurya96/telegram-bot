"""
Markdown utilities for Telegram
Sanitizes LLM-generated text for safe Telegram markdown parsing
"""

import re
import logging

logger = logging.getLogger(__name__)

def escape_markdown_v2(text: str) -> str:
    """
    Escape text for Telegram MarkdownV2
    
    Args:
        text: Raw text
        
    Returns:
        Escaped text safe for MarkdownV2
    """
    # Characters that need escaping in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    # Escape each character
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def sanitize_markdown(text: str) -> str:
    """
    Sanitize text for safe Telegram Markdown parsing
    Fixes common LLM-generated markdown issues
    
    Args:
        text: Raw text with potentially broken markdown
        
    Returns:
        Fixed markdown safe for Telegram
    """
    if not text:
        return text
    
    # Remove or fix common problematic patterns
    
    # 1. Fix unclosed asterisks (bold/italic)
    # Count asterisks - if odd, remove the last one or add closing
    asterisk_count = text.count('*')
    if asterisk_count % 2 != 0:
        # Find and close unclosed asterisks
        # Simple fix: replace single asterisks with nothing
        # Keep double asterisks (bold) and triple (bold+italic)
        text = re.sub(r'(?<!\*)\*(?!\*)', '', text)
    
    # 2. Fix unclosed underscores (italic)
    underscore_count = text.count('_')
    if underscore_count % 2 != 0:
        text = re.sub(r'(?<!_)_(?!_)', '', text)
    
    # 3. Fix unclosed backticks (code)
    backtick_count = text.count('`')
    if backtick_count % 2 != 0:
        # Remove single backticks
        text = re.sub(r'(?<!`)` (?!`)', '', text)
    
    # 4. Remove problematic characters that break parsing
    # Telegram markdown doesn't like these in certain contexts
    text = text.replace('\r', '')
    
    # 5. Fix triple backticks (code blocks)
    # Make sure they're on their own lines
    text = re.sub(r'```(\w*)\n?', r'\n```\1\n', text)
    text = re.sub(r'\n?```\n?', r'\n```\n', text)
    
    return text

def safe_markdown(text: str, fallback_plain: bool = True) -> tuple[str, str]:
    """
    Prepare text for Telegram with fallback
    
    Args:
        text: Raw text
        fallback_plain: If True, provide plain text fallback
        
    Returns:
        (sanitized_text, parse_mode)
    """
    try:
        # Try to sanitize markdown
        sanitized = sanitize_markdown(text)
        return sanitized, 'Markdown'
    except Exception as e:
        logger.warning(f"Markdown sanitization failed: {e}")
        if fallback_plain:
            # Return plain text without markdown
            return text, None
        else:
            raise

def remove_all_markdown(text: str) -> str:
    """
    Remove all markdown formatting, return plain text
    
    Args:
        text: Text with markdown
        
    Returns:
        Plain text without formatting
    """
    # Remove bold
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    
    # Remove italic
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # Remove code
    text = re.sub(r'`(.+?)`', r'\1', text)
    
    # Remove code blocks
    text = re.sub(r'```.*?\n(.+?)\n```', r'\1', text, flags=re.DOTALL)
    
    # Remove links
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    
    return text