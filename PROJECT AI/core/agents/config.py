import os
import time
import random
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Load variables
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def get_llm(temperature=0.7, json_mode=False):
    """
    Instantiates ChatGoogleGenerativeAI with automatic fallback models to prevent rate-limiting/quota exhaustion.
    """
    model_kwargs = {}
    if json_mode:
        # Request standard JSON object output format from Gemini
        model_kwargs = {"response_format": {"type": "json_object"}}
        
    # Standard models list in order of preference
    models = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.5-pro", "gemini-1.5-pro"]
    
    llms = [
        ChatGoogleGenerativeAI(
            model=m,
            temperature=temperature,
            google_api_key=GOOGLE_API_KEY,
            model_kwargs=model_kwargs
        )
        for m in models
    ]
    
    # Return the primary LLM with fallbacks
    return llms[0].with_fallbacks(llms[1:])


def get_embeddings():
    """
    Instantiates GoogleGenerativeAIEmbeddings.
    """
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=GOOGLE_API_KEY
    )


def safe_invoke(chain, inputs, max_retries=5):
    """
    Invokes a langchain chain with robust retry logic for rate limits and quota errors.
    """
    delay = 2.0
    for attempt in range(max_retries):
        try:
            return chain.invoke(inputs)
        except Exception as e:
            err_msg = str(e)
            is_rate_limit = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower()
            
            if is_rate_limit and attempt < max_retries - 1:
                sleep_time = delay + random.uniform(0.5, 1.5)
                print(f"Rate limit (429/RESOURCE_EXHAUSTED) hit. Retrying in {sleep_time:.2f}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(sleep_time)
                delay *= 2  # Exponential backoff
            else:
                raise e

