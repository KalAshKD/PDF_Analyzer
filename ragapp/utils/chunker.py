import tiktoken


# ragapp/utils/chunker.py
# ragapp/utils/chunker.py - Enhanced chunking
import re

def chunk_text(text, chunk_size=600, chunk_overlap=150):
    """Improved chunking that preserves context and structure"""
    # First, try to split by paragraphs
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for paragraph in paragraphs:
        para_length = len(paragraph)
        
        # If paragraph is very long, split it
        if para_length > chunk_size * 1.5:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                if current_length + len(sentence) > chunk_size and current_chunk:
                    chunks.append(' '.join(current_chunk))
                    # Keep overlap
                    current_chunk = current_chunk[-2:] if len(current_chunk) > 2 else []
                    current_length = sum(len(s) for s in current_chunk)
                
                current_chunk.append(sentence)
                current_length += len(sentence) + 1
        else:
            # Handle normal paragraphs
            if current_length + para_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                # Keep overlap
                current_chunk = current_chunk[-1:] if current_chunk else []
                current_length = sum(len(s) for s in current_chunk)
            
            current_chunk.append(paragraph)
            current_length += para_length + 2  # +2 for paragraph spacing
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def chunk_by_paragraphs(text, max_paragraphs=3):
    """Chunk by paragraphs for better context preservation"""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []
    
    for i in range(0, len(paragraphs), max_paragraphs):
        chunk = '\n\n'.join(paragraphs[i:i + max_paragraphs])
        if chunk:
            chunks.append(chunk)
    
    return chunks

def chunk_text_by_sentences(text, sentences_per_chunk=5):
    """Split text into chunks by sentences"""
    import re
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', text)
    
    chunks = []
    for i in range(0, len(sentences), sentences_per_chunk):
        chunk = ' '.join(sentences[i:i + sentences_per_chunk])
        chunks.append(chunk)
    
    return chunks



import re

class TextChunker:
    @staticmethod
    
    def chunk_text(text, chunk_size=1000, chunk_overlap=200):
        """Split text into chunks with overlap"""
        if not text.strip():
            return []
        
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            
            # Try to break at sentence boundaries
            if end < text_length:
                # Look for natural break points
                sentence_end = text.rfind('. ', start, end)
                if sentence_end != -1 and sentence_end > start + chunk_size // 2:
                    end = sentence_end + 2  # Include the period and space
                else:
                    # Look for other break points
                    for break_char in ['? ', '! ', '\n\n', '; ']:
                        break_pos = text.rfind(break_char, start, end)
                        if break_pos != -1:
                            end = break_pos + len(break_char)
                            break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - chunk_overlap
            if start < 0:
                start = 0
            if start >= text_length:
                break
        
        return chunks