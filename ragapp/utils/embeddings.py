import os, numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer

_client = None
EMBED_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
LOCAL_EMBED_MODEL = 'all-MiniLM-L6-v2'

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key != 'dummy_key_for_testing':
            _client = OpenAI(api_key=api_key)
    return _client

def embed_texts(texts):
    """Generate embeddings using OpenAI or fallback to local model"""
    client = get_client()
    
    if client:
        try:
            resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
            vectors = [np.array(d.embedding, dtype='float32') for d in resp.data]
            return np.vstack(vectors)
        except Exception:
            # Fallback to local model if OpenAI fails
            pass
    
    # Use local model as fallback
    model = SentenceTransformer(LOCAL_EMBED_MODEL)
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.astype('float32')




import os
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self):
        self.local_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.openai_client = None
        self.use_openai = False
        
        # Check if OpenAI API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and not api_key.startswith('your_'):
            try:
                self.openai_client = OpenAI(api_key=api_key)
                self.use_openai = True
                logger.info("Using OpenAI for embeddings")
            except Exception as e:
                logger.warning(f"OpenAI initialization failed: {e}. Using local model.")
                self.use_openai = False
    
    def generate_embedding(self, text):
        """Generate embedding for text using either OpenAI or local model"""
        if self.use_openai and self.openai_client:
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logger.warning(f"OpenAI embedding failed: {e}. Falling back to local model.")
        
        # Fallback to local model
        return self.local_model.encode(text).tolist()
    
    def generate_embeddings_batch(self, texts):
        """Generate embeddings for multiple texts"""
        if self.use_openai and self.openai_client:
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=texts
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                logger.warning(f"OpenAI batch embedding failed: {e}. Falling back to local model.")
        
        # Fallback to local model
        return self.local_model.encode(texts).tolist()