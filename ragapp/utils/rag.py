import os
import numpy as np
import faiss
import json
import re
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Configuration
CHAT_MODEL = os.getenv('CHAT_MODEL', 'gpt-3.5-turbo')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

class FaissStore:
    def __init__(self, dim=384, index_path=None):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.payloads = []  # Store metadata for each vector
        self.index_path = index_path
    
    def add(self, vectors, payloads):
        """Add vectors and their metadata to the index"""
        if len(vectors) != len(payloads):
            raise ValueError("Vectors and payloads must have the same length")
        
        vectors_np = np.array(vectors).astype('float32')
        self.index.add(vectors_np)
        self.payloads.extend(payloads)
    
    def search(self, query_vec, k=5):
        """Search for similar vectors"""
        query_vec_np = np.array([query_vec]).astype('float32')
        distances, indices = self.index.search(query_vec_np, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.payloads) and idx >= 0:
                results.append({
                    'page': self.payloads[idx]['page'],
                    'chunk': self.payloads[idx]['text'],
                    'distance': float(distances[0][i])
                })
        return results
    
    def save(self, path):
        """Save index to file"""
        faiss.write_index(self.index, path)
        # Save payloads separately
        payloads_path = path.replace('.index', '_payloads.json')
        with open(payloads_path, 'w') as f:
            json.dump(self.payloads, f)
    
    def load(self, path):
        """Load index from file"""
        if os.path.exists(path):
            self.index = faiss.read_index(path)
            payloads_path = path.replace('.index', '_payloads.json')
            if os.path.exists(payloads_path):
                with open(payloads_path, 'r') as f:
                    self.payloads = json.load(f)

def get_embedding_model():
    """Get embedding model (OpenAI or local fallback)"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if api_key and not api_key.startswith(('your_', 'dummy_')):
        try:
            client = OpenAI(api_key=api_key)
            logger.info("Using OpenAI for embeddings")
            return client, 'openai'
        except Exception as e:
            logger.warning(f"OpenAI failed: {e}. Using local model.")
    
    # Fallback to local model
    model = SentenceTransformer(EMBEDDING_MODEL)
    return model, 'local'

def get_llm_client():
    """Get OpenAI client for LLM"""
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key and not api_key.startswith(('your_', 'dummy_')):
        try:
            return OpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"OpenAI client failed: {e}")
    return None

def embed_texts(texts):
    """Generate embeddings for multiple texts"""
    model, model_type = get_embedding_model()
    
    if model_type == 'openai':
        try:
            response = model.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            return np.array([item.embedding for item in response.data])
        except Exception as e:
            logger.warning(f"OpenAI embedding failed: {e}. Falling back to local model.")
            model = SentenceTransformer(EMBEDDING_MODEL)
            return model.encode(texts)
    else:
        # Local model
        return model.encode(texts)

def build_or_load_index(document, chunks):
    """Build or load FAISS index for a document"""
    index_dir = os.path.join(settings.MEDIA_ROOT, 'indices')
    os.makedirs(index_dir, exist_ok=True)
    
    index_path = os.path.join(index_dir, f"{document.id}.index")
    
    # Check if index already exists
    if os.path.exists(index_path):
        store = FaissStore()
        store.load(index_path)
        if len(store.payloads) > 0:
            return store
    
    # Build new index
    if not chunks:
        raise ValueError("No chunks provided for indexing")
    
    # Prepare texts and payloads
    texts = [chunk['text'] for chunk in chunks]
    payloads = [{'page': chunk['page'], 'text': chunk['text']} for chunk in chunks]
    
    # Generate embeddings
    vectors = embed_texts(texts)
    
    # Create and populate index
    dim = vectors.shape[1]
    store = FaissStore(dim=dim, index_path=index_path)
    store.add(vectors.tolist(), payloads)
    store.save(index_path)
    
    return store

def retrieve_context(store, question, top_k=7):
    """Retrieve relevant context for a question"""
    # Embed the question
    query_embedding = embed_texts([question])[0]
    
    # Search for similar content
    results = store.search(query_embedding, k=top_k)
    
    # Prepare context and citations
    context = ""
    citations = []
    
    for i, result in enumerate(results):
        context += f"[p:{result['page']}] {result['chunk']}\n\n"
        citations.append({
            'page': result['page'],
            'snippet': result['chunk'][:200] + '...' if len(result['chunk']) > 200 else result['chunk']
        })
    
    return context, citations

def ask_llm(question, context, history=None):
    """Generate answer using OpenAI LLM with RAG context"""
    client = get_llm_client()
    
    if not client:
        return get_fallback_response(question, context)
    
    # Prepare messages
    messages = [
        {
            "role": "system", 
            "content": """You are a helpful assistant that answers questions based ONLY on the provided document context.
            
            RULES:
            1. Answer strictly from the provided context
            2. If information is missing, say "Based on the document, I cannot find specific information about this"
            3. Cite page numbers using [p:X] format
            4. Be precise and factual"""
        }
    ]
    
    # Add conversation history
    if history:
        messages.extend(history[-6:])  # Last 3 exchanges
    
    # Add current context and question
    messages.append({
        "role": "user",
        "content": f"""Document Context:
{context}

Question: {question}

Please answer based only on the document context above."""
    })
    
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return get_fallback_response(question, context, str(e))

def get_fallback_response(question, context, error_msg=None):
    """Generate intelligent fallback response without OpenAI"""
    # Simple keyword-based response
    lines = context.split('\n')
    relevant_info = []
    
    question_lower = question.lower()
    for line in lines:
        if any(keyword in line.lower() for keyword in question_lower.split()):
            relevant_info.append(line)
        elif len(relevant_info) < 3:  # Show some context
            relevant_info.append(line)
    
    response = f"Based on the document:\n\n"
    for info in relevant_info[:5]:
        response += f"• {info}\n"
    
    if error_msg:
        response += f"\n[Note: Fallback mode - {error_msg}]"
    else:
        response += "\n[Note: Using enhanced document analysis]"
    
    return response