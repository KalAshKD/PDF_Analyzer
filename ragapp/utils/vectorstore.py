import os, faiss, numpy as np, json


class FaissStore:
    def __init__(self, dim: int = None, index_path: str = None):
        self.dim = dim
        self.index_path = index_path
        self.index = faiss.IndexFlatIP(dim) if dim else None
        self.payloads = [] # [{'page':int,'chunk':str}]
        if index_path and os.path.exists(index_path) and os.path.exists(index_path + '.meta'):
            self._load()

    def add(self, vectors: np.ndarray, payloads):
        # If index doesn't exist yet, create it with the correct dimension
        if self.index is None:
            self.dim = vectors.shape[1]
            self.index = faiss.IndexFlatIP(self.dim)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.payloads.extend(payloads)


    def search(self, query_vec: np.ndarray, k: int = 5):
        try:
            # Ensure query_vec is the right shape and type
            q = query_vec.astype('float32').reshape(1, -1)
            faiss.normalize_L2(q)
            
            # Search
            D, I = self.index.search(q, k)
            
            results = []
            for idx in I[0]:
                if idx != -1 and idx < len(self.payloads):  # Check bounds
                    results.append(self.payloads[idx])
            
            return results
            
        except Exception as e:
            print(f"Search error: {e}")
            # Return empty results or some fallback
            return self.payloads[:min(k, len(self.payloads))] if self.payloads else []


    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.index_path + '.meta', 'w', encoding='utf-8') as f:
            json.dump(self.payloads, f)


    def _load(self):
        self.index = faiss.read_index(self.index_path)
        with open(self.index_path + '.meta','r',encoding='utf-8') as f:
            self.payloads = json.load(f)