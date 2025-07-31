# agents/creative_agent.py

import logging
from typing import Dict, Any

class CreativeAgent:
    """
    An agent specialized in creative writing tasks.
    """
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def run(self, prompt: str) -> Dict[str, Any]:
        """
        Takes a prompt and converts it into a creative_writing action.
        """
        self.logger.info(f"CreativeAgent is handling prompt: '{prompt}'")
        # In a real system, this might call a different LLM or use a specific template.
        # For our purposes, we just format the action.
        action = {"tool": "creative_writing", "parameters": {"task": prompt}}
        self.logger.info(f"CreativeAgent proposed action: {action}")
        return action
