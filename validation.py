"""
Validation utilities for API keys and configuration.
"""

import logging
import os
import sys

import google.genai as genai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def validate_gemini_api_key(api_key: str = None) -> bool:
    """
    Test the Gemini API key by making a small request.
    
    Args:
        api_key: API key to test. If None, loads from environment.
    
    Returns:
        True if key is valid and working, False otherwise.
    """
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logger.error("❌ GEMINI_API_KEY not found in environment. Add it to .env file.")
        return False
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents="Say 'API key validated' in one word: valid",
            config=genai.types.GenerateContentConfig(temperature=0)
        )
        if response and response.text:
            logger.debug("✅ Gemini API key validated successfully")
            return True
    except Exception as exc:
        logger.error("❌ Gemini API key validation failed: %s", exc)
        if "401" in str(exc) or "unauthorized" in str(exc).lower():
            logger.error("   → API key is invalid or expired")
        elif "429" in str(exc) or "quota" in str(exc).lower():
            logger.error("   → Rate limit or quota exceeded. Try again later.")
        return False


def validate_rapidapi_key(api_key: str = None) -> bool:
    """
    Test the RapidAPI key for JSearch API.
    
    Args:
        api_key: API key to test. If None, loads from environment.
    
    Returns:
        True if key is valid, False otherwise.
    """
    import requests
    
    if not api_key:
        api_key = os.getenv("RAPIDAPI_KEY")
    
    if not api_key:
        logger.error("❌ RAPIDAPI_KEY not found in environment. Add it to .env file.")
        return False
    
    try:
        url = "https://jsearch.p.rapidapi.com/search"
        params = {"query": "Python developer", "page": "1", "num_pages": "1"}
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            logger.debug("✅ RapidAPI key validated successfully")
            return True
        elif response.status_code == 401:
            logger.error("❌ RapidAPI key is invalid or expired")
            return False
        elif response.status_code == 429:
            logger.error("❌ RapidAPI rate limit exceeded. Try again later.")
            return False
        else:
            logger.error("❌ RapidAPI returned status %d", response.status_code)
            return False
    except requests.RequestException as exc:
        logger.error("❌ RapidAPI connection failed: %s", exc)
        return False


def validate_master_cv(path: str = "master_cv.txt") -> bool:
    """
    Check if master CV file exists and is non-empty.
    
    Args:
        path: Path to master CV file.
    
    Returns:
        True if file exists and has content, False otherwise.
    """
    if not os.path.exists(path):
        logger.error("❌ Master CV not found at: %s", path)
        return False
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    
    if not content:
        logger.error("❌ Master CV is empty: %s", path)
        return False
    
    if len(content) < 100:
        logger.warning("⚠️  Master CV seems very short (%d chars). Is it correct?", len(content))
    
    logger.debug("✅ Master CV validated: %d characters", len(content))
    return True


def validate_all_config() -> bool:
    """
    Run all validation checks and return True if everything is okay.
    
    Returns:
        True if all validations pass, False otherwise.
    """
    load_dotenv()
    logger.info("🔍 Validating configuration...")
    
    all_valid = True
    
    # Check Gemini key
    logger.info("   Checking Gemini API key...")
    if not validate_gemini_api_key():
        all_valid = False
    
    # Check RapidAPI key
    logger.info("   Checking RapidAPI key...")
    if not validate_rapidapi_key():
        all_valid = False
    
    # Check master CV
    logger.info("   Checking master CV...")
    if not validate_master_cv():
        all_valid = False
    
    if all_valid:
        logger.info("✅ All validations passed! Ready to run.")
    else:
        logger.error("❌ Some validations failed. See errors above.")
        logger.error("   → Fix the issues in .env or master_cv.txt and try again.")
    
    return all_valid


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )
    if not validate_all_config():
        sys.exit(1)
