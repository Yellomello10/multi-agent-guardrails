import logging
from fastapi import FastAPI, HTTPException, Form, File, UploadFile
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# --- Import all our custom modules ---
from utils.logger import logger 
from guardrails.input_guardrail import is_text_malicious, is_image_malicious
from guardrails.action_guardrail import ActionGuardrail
from agents.router_agent import RouterAgent

# --- Application Initialization ---

app = FastAPI(
    title="Multi-Agent Guardrails System",
    description="An API that uses a two-stage guardrail system to validate user inputs and agent actions.",
    version="2.1.0" # Version up for file uploads!
)

# Initialize our core components with the shared logger
try:
    action_guardrail = ActionGuardrail(logger=logger)
    router_agent = RouterAgent(logger=logger)
    logger.info("Multi-agent application components initialized successfully.")
except Exception as e:
    logger.critical(f"Failed to initialize application components: {e}")
    action_guardrail = None
    router_agent = None

# --- Pydantic Models for Request and Response ---
# The InvokeRequest model is no longer needed as we use Form data now.
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


# --- MODIFICATION: The endpoint signature is completely changed ---
@app.post("/invoke", response_model=InvokeResponse, tags=["Agent"])
async def invoke_agent(
    prompt: str = Form(...), 
    image: Optional[UploadFile] = File(None)
):
    """
    This endpoint processes a user request through the full guardrail system.
    It now accepts multipart/form-data with a 'prompt' field and an optional 'image' file.
    """
    logger.info(f"Received new request for prompt: '{prompt}'")
    
    if not action_guardrail or not router_agent:
        raise HTTPException(status_code=503, detail="Service Unavailable: Core components failed to initialize.")

    # --- MODIFICATION: Read image bytes if an image was uploaded ---
    image_bytes = await image.read() if image else None

    # === Stage 1: Input Guardrail ===
    if is_text_malicious(prompt, logger):
        logger.warning(f"Input Guardrail blocked malicious text prompt: '{prompt}'")
        raise HTTPException(status_code=400, detail="Malicious text detected in the prompt.")

    # Pass the image bytes to the guardrail function
    if is_image_malicious(image_bytes, logger):
        logger.warning(f"Input Guardrail blocked a malicious image upload.")
        raise HTTPException(status_code=400, detail="Malicious image detected in the uploaded file.")
    
    logger.info("Input Guardrail passed.")

    # === Stage 2: Agent Routing and Action Guardrail ===
    proposed_action = router_agent.route(prompt)
    
    tool_used = proposed_action.get("tool")
    if tool_used == "web_search":
        agent_name = "ResearchAgent"
    elif tool_used == "creative_writing":
        agent_name = "CreativeAgent"
    else:
        agent_name = "Unknown"

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
