# velis/utils/file_utils.py
from loguru import logger


def save_text_to_file(text, filepath):
    """Saves text to a specific file path."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        return False
