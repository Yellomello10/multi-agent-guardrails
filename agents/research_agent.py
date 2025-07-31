# agents/research_agent.py

import logging
from typing import Dict, Any

class ResearchAgent:
    """
    An agent specialized in generating web search queries.
    """
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def run(self, prompt: str) -> Dict[str, Any]:
        """
        Takes a prompt and converts it into a web_search action.
        """
        self.logger.info(f"ResearchAgent is handling prompt: '{prompt}'")
        action = {"tool": "web_search", "parameters": {"query": prompt}}
        self.logger.info(f"ResearchAgent proposed action: {action}")
        return action
