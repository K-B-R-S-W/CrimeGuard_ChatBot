"""
Utility module for response formatting.
Main language routing and response generation is handled by langgraph_utils.py
This module provides helper functions for formatting responses.
"""

import logging
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup basic logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)


# Helper Functions
def clean_response(text):
    """Remove Markdown bold markers (**) and potential unwanted artifacts."""
    return text.replace("**", "").strip()


def format_response_as_list(response_text):
    """
    Analyzes response text and formats it appropriately (steps or plain text).
    Used by chat_router to format responses for the frontend.
    """
    cleaned_text = clean_response(response_text)
    step_pattern = r'^\s*(\d+\.|Step\s*\d+\s*[:-]?)\s+'
    lines = cleaned_text.split('\n')
    steps = []
    is_list_format = False

    for line in lines:
        line = line.strip()
        if re.match(step_pattern, line):
            is_list_format = True
            step_text = re.sub(step_pattern, '', line)
            if step_text:
                steps.append(step_text)
        elif is_list_format and line:
            steps.append(line)
        elif line:
            steps.append(line)

    if is_list_format and len(steps) > 1:
        steps = [s.strip() for s in steps if s.strip()]
        return {"type": "steps", "content": steps}
    else:
        final_text = "\n".join(steps).strip()
        if not final_text:
            return {"type": "text", "content": "..."}
        return {"type": "text", "content": final_text}

 