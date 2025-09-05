import os, uuid
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from .forms import UploadForm
from .models import Document, Chunk, ChatSession, ChatMessage
from django.conf import settings  

@require_http_methods(["GET"])
def index(request):
    return render(request, 'ragapp/index.html')

# ragapp/views.py - Update your upload_pdf view

# ragapp/views.py - Update upload_pdf function
# ragapp/views.py - Update the upload_pdf function with detailed error handling
@require_http_methods(["POST"])
def upload_pdf(request):
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            doc = form.save()
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            
            chunks = []
            page_count = 0
            
            # Process PDF
            for page_num, text in extract_pdf_text_with_pages(doc.file.path):
                page_count = page_num
                
                # Smart chunking
                text_chunks = chunk_text(text, chunk_size=800, chunk_overlap=150)
                
                for chunk_text_content in text_chunks:
                    if chunk_text_content.strip():
                        chunks.append({'page': page_num, 'text': chunk_text_content})
                        Chunk.objects.create(
                            document=doc, 
                            page_num=page_num, 
                            content=chunk_text_content
                        )
            
            doc.num_pages = page_count
            doc.save()
            
            # Build vector index
            store = build_or_load_index(doc, chunks)
            
            # Start chat session
            sid = uuid.uuid4().hex[:16]
            ChatSession.objects.create(document=doc, session_id=sid)
            
            return JsonResponse({
                'ok': True, 
                'session_id': sid, 
                'title': doc.title, 
                'num_pages': page_count,
                'chunk_count': len(chunks)
            })
            
        except Exception as e:
            if 'doc' in locals():
                doc.delete()
            return JsonResponse({
                'ok': False, 
                'error': f'PDF processing failed: {str(e)}'
            })
    
    return JsonResponse({
        'ok': False, 
        'error': 'Invalid form data'
    })
# ragapp/views.py - temporary fix

from django.shortcuts import render
from django.http import HttpResponse
import numpy as np

# Temporarily comment out problematic imports
# from .utils.pdf_loader import extract_pdf_text_with_pages
# from .utils.chunker import chunk_text
# from .utils.embeddings import embed_texts
# from .utils.vectorstore import FaissStore

# Add placeholder functions for testing
def extract_pdf_text_with_pages(pdf_file):
    return [(1, "Sample PDF text for testing")]

def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def embed_texts(texts):
    # Return dummy embeddings for testing
    return np.random.rand(len(texts), 1536).astype('float32')

class FaissStore:
    def __init__(self, dim, index_path):
        self.dim = dim
        self.index_path = index_path
    
    def add(self, vectors, payloads):
        pass
    
    def search(self, query_vec, k=5):
        return [{"page": 1, "chunk": "Sample result"}]

from .utils.pdf_loader import extract_pdf_text_with_pages
from .utils.chunker import chunk_text
from .utils.rag import build_or_load_index, retrieve_context, ask_llm  # Add these imports
import json
# ragapp/views.py - Add error handling to ask function
import os, uuid, json
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .forms import UploadForm
from .models import Document, Chunk, ChatSession, ChatMessage
from .utils.pdf_loader import extract_pdf_text_with_pages
from .utils.chunker import chunk_text
from .utils.rag import build_or_load_index, retrieve_context, ask_llm

# ragapp/views.py
import os
import uuid
import json
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.conf import settings
from .forms import UploadForm
from .models import Document, Chunk, ChatSession, ChatMessage
from .utils.pdf_loader import extract_pdf_text_with_pages
from .utils.chunker import chunk_text
from .utils.rag import build_or_load_index, retrieve_context, ask_llm

@require_http_methods(["GET"])
def index(request):
    return render(request, 'ragapp/index.html')

@require_http_methods(["POST"])
def upload_pdf(request):
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            doc = form.save()
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            
            chunks = []
            page_count = 0
            
            # Process PDF
            for page_num, text in extract_pdf_text_with_pages(doc.file.path):
                page_count = page_num
                
                # Smart chunking
                text_chunks = chunk_text(text, chunk_size=800, chunk_overlap=150)
                
                for chunk_text_content in text_chunks:
                    if chunk_text_content.strip():
                        chunks.append({'page': page_num, 'text': chunk_text_content})
                        Chunk.objects.create(
                            document=doc, 
                            page_num=page_num, 
                            content=chunk_text_content
                        )
            
            doc.num_pages = page_count
            doc.save()
            
            # Build vector index
            store = build_or_load_index(doc, chunks)
            
            # Start chat session
            sid = uuid.uuid4().hex[:16]
            ChatSession.objects.create(document=doc, session_id=sid)
            
            return JsonResponse({
                'ok': True, 
                'session_id': sid, 
                'title': doc.title, 
                'num_pages': page_count,
                'chunk_count': len(chunks)
            })
            
        except Exception as e:
            if 'doc' in locals():
                doc.delete()
            return JsonResponse({
                'ok': False, 
                'error': f'PDF processing failed: {str(e)}'
            })
    
    return JsonResponse({
        'ok': False, 
        'error': 'Invalid form data'
    })

@require_http_methods(["POST"])
def ask(request):
    """Handle chat questions using RAG"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        question = data.get('question')
        
        if not session_id or not question:
            return JsonResponse({'ok': False, 'error': 'Missing parameters'})
        
        # Get session and document
        session = ChatSession.objects.get(session_id=session_id)
        document = session.document
        
        # Get chunks from database
        chunks = []
        for chunk in Chunk.objects.filter(document=document):
            chunks.append({'page': chunk.page_num, 'text': chunk.content})
        
        # Build or load index
        store = build_or_load_index(document, chunks)
        
        # Retrieve context
        context, citations = retrieve_context(store, question, top_k=5)
        
        # Get chat history
        chat_history = []
        for msg in ChatMessage.objects.filter(session=session).order_by('-created_at')[:6]:
            chat_history.append({'role': 'user', 'content': msg.question})
            chat_history.append({'role': 'assistant', 'content': msg.answer})
        
        # Generate answer
        answer = ask_llm(question, context, chat_history)
        
        # Save conversation
        ChatMessage.objects.create(
            session=session,
            question=question,
            answer=answer
        )
        
        return JsonResponse({
            'ok': True, 
            'answer': answer, 
            'citations': citations
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Invalid session'})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)})