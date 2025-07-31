import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# --- Import all our custom modules ---
from utils.logger import logger 
from guardrails.input_guardrail import is_text_malicious, is_image_malicious
from guardrails.action_guardrail import ActionGuardrail

# --- MODIFICATION: Import the new RouterAgent ---
from agents.router_agent import RouterAgent

# --- Application Initialization ---

app = FastAPI(
    title="Multi-Agent Guardrails System",
    description="An API that uses a two-stage guardrail system to validate user inputs and agent actions.",
    version="2.0.0" # Version up!
)

# Initialize our core components with the shared logger
try:
    action_guardrail = ActionGuardrail(logger=logger)
    # --- MODIFICATION: Instantiate the RouterAgent instead of MockAgent ---
    router_agent = RouterAgent(logger=logger)
    logger.info("Multi-agent application components initialized successfully.")
except Exception as e:
    logger.critical(f"Failed to initialize application components: {e}")
    action_guardrail = None
    # --- MODIFICATION: router_agent instead of mock_agent ---
    router_agent = None


# --- Pydantic Models for Request and Response ---
class InvokeRequest(BaseModel):
    prompt: str = Field(..., description="The natural language prompt from the user.")
    image_url: Optional[str] = Field(None, description="An optional URL to an image for analysis.")

class InvokeResponse(BaseModel):
    status: str = Field(description="The final status of the request.")
    routed_to: Optional[str] = Field(None, description="Which specialized agent handled the request.")
    agent_action: Optional[Dict[str, Any]] = Field(None, description="The action the agent was permitted to take.")
    message: str = Field(description="A descriptive message for the user.")


# --- API Endpoints ---

@app.get("/", tags=["Status"])
def read_root():
    """A simple root endpoint to confirm that the API is running."""
    return {"status": "Multi-Agent Guardrails API is running."}


@app.post("/invoke", response_model=InvokeResponse, tags=["Agent"])
def invoke_agent(request: InvokeRequest):
    """
    This endpoint processes a user request through the full guardrail system.
    """
    logger.info(f"Received new request for prompt: '{request.prompt}'")
    
    if not action_guardrail or not router_agent:
        raise HTTPException(status_code=503, detail="Service Unavailable: Core components failed to initialize.")

    # === Stage 1: Input Guardrail ===
    if is_text_malicious(request.prompt, logger):
        logger.warning(f"Input Guardrail blocked malicious text prompt: '{request.prompt}'")
        raise HTTPException(status_code=400, detail="Malicious text detected in the prompt.")

    if request.image_url and is_image_malicious(request.image_url, logger):
        logger.warning(f"Input Guardrail blocked malicious image URL: '{request.image_url}'")
        raise HTTPException(status_code=400, detail="Malicious image detected at the provided URL.")
    
    logger.info("Input Guardrail passed.")

    # === Stage 2: Agent Routing and Action Guardrail ===
    # --- MODIFICATION: Use the router to get the proposed action ---
    proposed_action = router_agent.route(request.prompt)
    
    # Determine which agent was used for the response
    tool_used = proposed_action.get("tool")
    if tool_used == "web_search":
        agent_name = "ResearchAgent"
    elif tool_used == "creative_writing":
        agent_name = "CreativeAgent"
    else:
        agent_name = "Unknown"

    # Check the proposed action against the rules
    if action_guardrail.is_action_illegal(proposed_action):
        logger.warning(f"Action Guardrail blocked illegal action from {agent_name}: {proposed_action}")
        raise HTTPException(status_code=403, detail=f"The proposed agent action '{proposed_action.get('tool')}' is not permitted.")
        
    logger.info(f"Action Guardrail passed for action from {agent_name}: {proposed_action}")

    # --- Success ---
    return InvokeResponse(
        status="Success",
        routed_to=agent_name,
        agent_action=proposed_action,
        message="The request passed all guardrails and the agent action was approved."
    )