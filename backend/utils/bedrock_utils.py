import requests
import json
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Any, Dict, Optional

from langchain.llms.base import BaseLLM
from langchain.embeddings.base import Embeddings
from langchain_core.outputs import Generation, LLMResult


import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 
from backend.logger_config import logger
from backend.config import BEDROCK_LLM_LAMBDA_URL, BEDROCK_EMBEDDING_LAMBDA_URL, BEDROCK_EMBEDDING_MODEL_ID


class BedrockLLMConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), extra='allow') 
    model_id: str = Field(..., description="The Bedrock model ID")
    api_key: str = Field(..., description="The API key for Bedrock authentication")
    llm_lambda_url: str = Field(..., description="Lambda URL for LLM inference")
    model_kwargs: Dict[str, Any] = Field(default_factory=lambda: {"max_tokens": 1024, "temperature": 0.7})


class BedrockLLM(BaseLLM):
    model_config = ConfigDict(protected_namespaces=())
    config: BedrockLLMConfig

    def __init__(self, *, config: BedrockLLMConfig):
        super().__init__(config=config)

    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs: Any) -> LLMResult:
        generations = []
        for prompt in prompts:
            # Merge kwargs from config and runtime
            current_model_kwargs = {**self.config.model_kwargs, **kwargs}
            if stop: # Langchain stop sequences
                current_model_kwargs['stop_sequences'] = stop

            response_text = self._call(prompt, model_kwargs=current_model_kwargs)
            generations.append([Generation(text=response_text)])
        return LLMResult(generations=generations)

    def _call(self, prompt: str, model_kwargs: Optional[Dict[str, Any]] = None) -> str:
        payload = {
            "api_key": self.config.api_key,
            "prompt": prompt,
            "model_id": self.config.model_id,
            "model_params": model_kwargs or self.config.model_kwargs,
        }
        logger.debug(f"BedrockLLM sending payload to {self.config.llm_lambda_url}: {payload['model_id']}, prompt length: {len(prompt)}")
        
        try:
            resp = requests.post(self.config.llm_lambda_url, json=payload, headers={"Content-Type": "application/json"}, timeout=300) # Increased timeout
            resp.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)
            
            response_data = resp.json()
            if "response" in response_data:
                if isinstance(response_data["response"], dict) and "content" in response_data["response"] and \
                   isinstance(response_data["response"]["content"], list) and len(response_data["response"]["content"]) > 0 and \
                   "text" in response_data["response"]["content"][0]:
                    return response_data["response"]["content"][0]["text"]
                elif isinstance(response_data["response"], str): # Simpler Lambda response
                     return response_data["response"]
            
            logger.error(f"Unexpected BedrockLLM Lambda response format: {response_data}")
            raise ValueError("Unexpected BedrockLLM Lambda response format")

        except requests.exceptions.HTTPError as e:
            logger.error(f"{e.response.status_code} error from BedrockLLM Lambda: {e.response.text}")
            raise ValueError(f"{e.response.status_code} error from BedrockLLM Lambda: {e.response.text}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException calling BedrockLLM Lambda: {e}")
            raise RuntimeError(f"RequestException calling BedrockLLM Lambda: {e}") from e
        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e: # Catch issues with parsing response
            logger.error(f"Error processing BedrockLLM Lambda response: {e}. Response text: {resp.text if 'resp' in locals() else 'N/A'}")
            raise RuntimeError(f"Error processing BedrockLLM Lambda response: {e}") from e


    @property
    def _llm_type(self) -> str:
        return "bedrock_lambda_llm"


class AmazonEmbeddings(Embeddings):
    api_key: str
    model_id: str
    embedding_lambda_url: str

    def __init__(self, api_key: str, model_id: str = BEDROCK_EMBEDDING_MODEL_ID, embedding_lambda_url: str = BEDROCK_EMBEDDING_LAMBDA_URL):
        super().__init__()
        if not all([api_key, model_id, embedding_lambda_url]):
            raise ValueError("API key, model ID, and Lambda URL for embeddings must be provided.")
        self.api_key = api_key
        self.model_id = model_id
        self.embedding_lambda_url = embedding_lambda_url

    def _get_embedding(self, text: str) -> List[float]:
        payload = {
            "api_key": self.api_key,
            "prompt": text, # Or "inputText" depending on Bedrock model
            "model_id": self.model_id
        }
        headers = {"Content-Type": "application/json"}
        logger.debug(f"AmazonEmbeddings requesting embedding for text length: {len(text)} using {self.model_id}")

        try:
            response = requests.post(self.embedding_lambda_url, headers=headers, data=json.dumps(payload), timeout=60)
            response.raise_for_status()
            
            response_data = response.json()
            if "response" in response_data and "embedding" in response_data["response"]:
                embedding = response_data["response"]["embedding"]
            elif "embedding" in response_data: # Simpler Lambda response
                embedding = response_data["embedding"]
            else:
                logger.error(f"Unexpected AmazonEmbeddings Lambda response format: {response_data}")
                raise ValueError("Unexpected AmazonEmbeddings Lambda response format")

            if not embedding: 
                logger.warning(f"Received empty or null embedding for text: '{text[:50]}...'")
                raise ValueError("Received empty embedding from Lambda.")
            return embedding

        except requests.exceptions.HTTPError as e:
            logger.error(f"{e.response.status_code} error from AmazonEmbeddings Lambda: {e.response.text}")
            raise ValueError(f"Embedding Lambda HTTP error: {e.response.status_code} {e.response.text}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException calling AmazonEmbeddings Lambda: {e}")
            raise RuntimeError(f"Embedding Lambda request error: {e}") from e
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Error processing AmazonEmbeddings Lambda response: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}")
            raise RuntimeError(f"Error processing Embedding Lambda response: {e}") from e


    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._get_embedding(text) for text in texts if text and text.strip()]
    def embed_query(self, text: str) -> List[float]:
        if not text or not text.strip():
            raise ValueError("Cannot embed empty query text.")
        return self._get_embedding(text)