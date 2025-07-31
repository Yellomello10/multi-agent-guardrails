# agents/router_agent.py

import logging
from typing import Dict, Any

# Import the specialized agents
from .research_agent import ResearchAgent
from .creative_agent import CreativeAgent

class RouterAgent:
    """
    A router agent that delegates tasks to specialized agents based on the prompt.
    """
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        # The router holds instances of the agents it can delegate to.
        self.agents = {
            "research": ResearchAgent(logger),
            "creative": CreativeAgent(logger),
        }
        self.logger.info("RouterAgent initialized with specialized agents.")

    def route(self, prompt: str) -> Dict[str, Any]:
        """
        Analyzes the prompt and routes it to the appropriate specialized agent.

        Args:
            prompt (str): The user's input prompt.

        Returns:
            Dict[str, Any]: The action proposed by the chosen specialized agent.
        """
        self.logger.info(f"RouterAgent received prompt for routing: '{prompt}'")
        prompt_lower = prompt.lower()

        # Simple keyword-based routing logic
        creative_keywords = ["write", "create", "tell me a", "poem", "joke", "story"]
        
        # If any creative keyword is in the prompt, delegate to the CreativeAgent.
        if any(keyword in prompt_lower for keyword in creative_keywords):
            self.logger.info("Routing to CreativeAgent.")
            return self.agents["creative"].run(prompt)
        
        # Otherwise, delegate to the ResearchAgent by default.
        else:
            self.logger.info("Routing to ResearchAgent.")
            return self.agents["research"].run(prompt)

