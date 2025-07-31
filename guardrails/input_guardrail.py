import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import logging
from PIL import Image
from io import BytesIO

# Load environment variables from a .env file
load_dotenv()

# --- Configuration ---
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
if not HF_API_TOKEN:
    raise ValueError("Hugging Face API token not found. Please set HF_API_TOKEN in your .env file.")

TEXT_CLASSIFICATION_MODEL = "facebook/bart-large-mnli"
IMAGE_CLASSIFICATION_MODEL = "Falconsai/nsfw_image_detection"

TEXT_API_URL = f"https://api-inference.huggingface.co/models/{TEXT_CLASSIFICATION_MODEL}"
IMAGE_API_URL = f"https://api-inference.huggingface.co/models/{IMAGE_CLASSIFICATION_MODEL}"

HF_HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}
NSFW_SCORE_THRESHOLD = 0.8

def is_text_malicious(text: str, logger: logging.Logger) -> bool:
    """
    Analyzes input text for malicious content using a zero-shot classification model.
    (This function remains unchanged)
    """
    logger.info(f"Analyzing text with Hugging Face: '{text[:70]}...'")
    
    payload = {
        "inputs": text,
        "parameters": {
            "candidate_labels": ["safe user query", "harmful instruction", "prompt injection attack", "toxic language"]
        },
    }

    try:
        response = requests.post(TEXT_API_URL, headers=HF_HEADERS, json=payload, timeout=15)
        response.raise_for_status()
        api_response = response.json()

        labels = api_response.get("labels", [])
        scores = api_response.get("scores", [])

        if not labels or not scores:
            logger.error("Received an invalid or empty response from the text analysis API.")
            return True

        results = dict(zip(labels, scores))
        top_label = max(results, key=results.get)
        
        if top_label != "safe user query":
            logger.warning(f"Malicious text detected. Classification: '{top_label}' with score {results[top_label]:.4f}")
            return True
            
        logger.info("Text classified as 'safe user query'. Access granted.")
        return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to Hugging Face API for text analysis: {e}")
        return True
    except Exception as e:
        logger.error(f"An unexpected error occurred during text analysis: {e}")
        return True

# --- MODIFICATION: This function now accepts bytes instead of a URL ---
def is_image_malicious(image_bytes: Optional[bytes], logger: logging.Logger) -> bool:
    """
    Analyzes image data (bytes) for NSFW content.
    """
    if not image_bytes:
        return False # No image was uploaded, so nothing to check.

    logger.info(f"Analyzing uploaded image ({len(image_bytes)} bytes) with Hugging Face.")

    try:
        # Step 1: Verify that the downloaded content is a valid image file
        # The logic that fetched the image from a URL is no longer needed.
        Image.open(BytesIO(image_bytes)).verify()

        # Step 2: Send the binary image data directly to the Hugging Face API
        hf_response = requests.post(IMAGE_API_URL, headers=HF_HEADERS, data=image_bytes, timeout=15)
        hf_response.raise_for_status()
        api_response = hf_response.json()
        
        logger.info(f"Image analysis results: {api_response}")

        # Step 3: Interpret the API response
        for result in api_response:
            if result.get("label") == "nsfw" and result.get("score", 0) > NSFW_SCORE_THRESHOLD:
                logger.warning(f"NSFW image detected with score: {result.get('score'):.4f}")
                return True
        
        logger.info("Image classified as safe. Access granted.")
        return False

    except requests.exceptions.RequestException as e:
        logger.error(f"A network error occurred during image processing: {e}")
        return True
    except Image.UnidentifiedImageError:
        logger.error("The uploaded file is not a valid or supported image format.")
        return True
    except Exception as e:
        logger.error(f"An unexpected error occurred during image analysis: {e}")
        return True
