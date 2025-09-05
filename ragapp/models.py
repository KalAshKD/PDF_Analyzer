from django.db import models
import os

class Document(models.Model):
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    num_pages = models.IntegerField(default=0)
    index_path = models.CharField(max_length=500, blank=True)  # Add this field
    
    def save(self, *args, **kwargs):
        if not self.title:
            self.title = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Chunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    page_num = models.IntegerField()
    content = models.TextField()
    embedding_dim = models.IntegerField(default=3072) # for text-embedding-3-large
    # Optional: store embedding bytes for audit/debug (not used for retrieval at runtime)
    embedding = models.BinaryField(null=True, blank=True)


class ChatSession(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='sessions')
    session_id = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    question = models.TextField(blank=True, default='')  # Make nullable first
    answer = models.TextField(blank=True, default='')    # Make nullable first
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Q: {self.question[:50]}..."