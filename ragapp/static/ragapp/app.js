// ragapp/static/ragapp/app.js
document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');
    
    let sessionId = null;
    let documentTitle = null;

    // Show chat section function
    function showChatSection(title) {
        const chatSection = document.getElementById('chat-section');
        const documentTitleElement = document.getElementById('document-title');
        
        chatSection.style.display = 'block';
        documentTitleElement.textContent = title;
        
        // Scroll to chat section smoothly
        chatSection.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
        
        // Focus on the chat input
        setTimeout(() => {
            document.getElementById('chat-input').focus();
        }, 300);
    }

    // Handle file upload
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!fileInput.files.length) {
            alert('Please select a PDF file');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        uploadStatus.textContent = 'Uploading and processing PDF...';
        uploadStatus.style.color = '#000';
        
        fetch('/upload/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.ok) {
                sessionId = data.session_id;
                documentTitle = data.title;
                uploadStatus.textContent = `Upload successful! Document: ${data.title}, Pages: ${data.num_pages}`;
                uploadStatus.style.color = 'green';
                
                showChatSection(data.title);
                // In your upload success handler, update the welcome message call:
addMessage(`I've processed "${data.title}" (${data.num_pages} pages). Ask me anything about this document!`, 'bot', '');

// And in the initial load:
addMessage("Welcome! I'm ready to answer questions about your document. Ask me anything about the content.", 'bot', '');
            } else {
                // Handle different error formats
                let errorMessage = 'Upload failed: ';
                
                if (data.error) {
                    errorMessage += data.error;
                } else if (data.errors) {
                    // Format form field errors
                    errorMessage += Object.values(data.errors).flat().join(', ');
                } else {
                    errorMessage += 'Unknown error occurred';
                }
                
                uploadStatus.textContent = errorMessage;
                uploadStatus.style.color = 'red';
            }
        })
        .catch(error => {
            uploadStatus.textContent = 'Upload error: ' + error;
            uploadStatus.style.color = 'red';
        });
    });

    // Handle sending messages
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // ragapp/static/ragapp/app.js - Fix the sendMessage function
function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || !sessionId) return;
    
    const question = message; // Store the question before clearing
    addMessage(question, 'user');
    chatInput.value = '';
    
    fetch('/ask/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            session_id: sessionId,
            question: question
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.ok) {
            addMessage(data.answer, 'bot', question); // Pass the question here
        } else {
            addMessage('Error: ' + (data.error || 'Unknown error'), 'bot', question);
        }
    })
    .catch(error => {
        addMessage('Error sending message: ' + error, 'bot', question);
    });
}

    function addMessage(text, sender, question = '') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    let formattedText = text.replace(/\n/g, '<br>');
    
    // Highlight keywords only for bot responses and if question is provided
    if (sender === 'bot' && question) {
        formattedText = highlightKeywords(formattedText, question);
    }
    
    formattedText = formattedText
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/🔍|📄|📑|💡|⚡|ℹ️/g, '<span class="emoji">$&</span>');
    
    messageDiv.innerHTML = formattedText;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});








function highlightKeywords(text, question) {
    if (!question) return text;
    
    // Extract keywords from question
    const stopWords = new Set(['what', 'are', 'my', 'the', 'a', 'an', 'is', 'can', 'you', 
                              'me', 'how', 'where', 'when', 'why', 'which', 'who', 'please',
                              'tell', 'about', 'your', 'this', 'that', 'there']);
    
    const keywords = question.toLowerCase().split(' ')
        .filter(word => {
            const cleanWord = word.replace(/[^\w]/g, '');
            return cleanWord.length > 2 && !stopWords.has(cleanWord.toLowerCase());
        })
        .map(word => word.replace(/[^\w]/g, ''));
    
    // Remove duplicates
    const uniqueKeywords = [...new Set(keywords)];
    
    // Highlight keywords in text
    let highlightedText = text;
    uniqueKeywords.forEach(keyword => {
        if (keyword) {
            const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
            highlightedText = highlightedText.replace(regex, 
                '<span class="keyword-highlight">$&</span>');
        }
    });
    
    return highlightedText;
}

// Update addMessage function
function addMessage(text, sender, question = '') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    let formattedText = text.replace(/\n/g, '<br>');
    
    // Highlight keywords in bot responses
    if (sender === 'bot' && question) {
        formattedText = highlightKeywords(formattedText, question);
    }
    
    formattedText = formattedText
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    messageDiv.innerHTML = formattedText;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}







