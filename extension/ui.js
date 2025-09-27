// ui.js - Main UI logic for the chat interface
class VidSageUI {
    constructor() {
        this.API_BASE = 'http://localhost:8000';
        this.currentVideoId = null;
        this.sessionId = this.generateSessionId();
        this.isProcessing = false;
      
        this.initElements();
        this.bindEvents();
        this.checkUrlParams();
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    initElements() {
        // Sections
        this.videoInputSection = document.getElementById('video-input-section');
        this.chatSection = document.getElementById('chat-section');
        this.errorSection = document.getElementById('error-section');
        
        // Input elements
        this.videoInput = document.getElementById('video-input');
        this.startChatBtn = document.getElementById('start-chat-btn');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        
        // Display elements
        this.videoIdDisplay = document.getElementById('video-id-display');
        this.messagesContainer = document.getElementById('messages-container');
        this.loadingIndicator = document.getElementById('loading-indicator');
        
        // Control elements
        this.newVideoBtn = document.getElementById('new-video-btn');
        this.retryBtn = document.getElementById('retry-btn');
        this.errorTitle = document.getElementById('error-title');
        this.errorMessage = document.getElementById('error-message');
    }
    
    bindEvents() {
        // Video input events
        this.startChatBtn.addEventListener('click', () => this.handleStartChat());
        this.videoInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.isProcessing) {
                this.handleStartChat();
            }
        });
        
        // Chat events
        this.sendBtn.addEventListener('click', () => this.handleSendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.isProcessing) {
                this.handleSendMessage();
            }
        });
        
        // Control events
        this.newVideoBtn.addEventListener('click', () => this.showVideoInput());
        this.retryBtn.addEventListener('click', () => this.showVideoInput());
    }
    
    checkUrlParams() {
        const urlParams = new URLSearchParams(window.location.search);
        const videoId = urlParams.get('video_id');
        
        if (videoId) {
            this.videoInput.value = videoId;
            this.handleStartChat();
        }
    }
    
    extractVideoId(input) {
        // Clean the input
        input = input.trim();
        
        // If it's already just a video ID (11 characters, alphanumeric)
        if (input.match(/^[a-zA-Z0-9_-]{11}$/)) {
            return input;
        }
        
        // Extract from various YouTube URL formats
        const patterns = [
            /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/,
            /v=([a-zA-Z0-9_-]{11})/
        ];
        
        for (const pattern of patterns) {
            const match = input.match(pattern);
            if (match) {
                return match[1];
            }
        }
        
        return null;
    }
    
    async handleStartChat() {
        if (this.isProcessing) return;
        
        const input = this.videoInput.value.trim();
        if (!input) {
            this.showError('Please enter a YouTube video ID or URL', 'Invalid Input');
            return;
        }
        
        const videoId = this.extractVideoId(input);
        if (!videoId) {
            this.showError('Please enter a valid YouTube video ID or URL', 'Invalid Format');
            return;
        }
        
        this.isProcessing = true;
        this.startChatBtn.disabled = true;
        this.startChatBtn.textContent = 'Processing...';
        
        try {
            // Ingest the video
            const response = await fetch(`${this.API_BASE}/ingest/${videoId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to process video');
            }
            
            const result = await response.json();
            
            // Success - show chat interface
            this.currentVideoId = videoId;
            this.showChat();
            
        } catch (error) {
            console.error('Error ingesting video:', error);
            this.showError(error.message || 'Failed to process the video. Please check if the video ID is correct and try again.', 'Processing Error');
        } finally {
            this.isProcessing = false;
            this.startChatBtn.disabled = false;
            this.startChatBtn.textContent = 'Start Chat';
        }
    }
    
    async handleSendMessage() {
        if (this.isProcessing) return;
        
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        
        // Show loading
        this.showLoading(true);
        this.isProcessing = true;
        this.sendBtn.disabled = true;
        this.messageInput.disabled = true;
        
        try {
            const response = await fetch(`${this.API_BASE}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_id: this.currentVideoId,
                    session_id: this.sessionId,
                    question: message
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to get response');
            }
            
            const result = await response.json();
            
            // Add AI response to chat
            this.addMessage(result.answer, 'ai');
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('Sorry, I encountered an error while processing your question. Please try again.', 'ai');
        } finally {
            this.showLoading(false);
            this.isProcessing = false;
            this.sendBtn.disabled = false;
            this.messageInput.disabled = false;
            this.messageInput.focus();
        }
    }
    
    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const avatar = document.createElement('img');
        avatar.src = sender === 'user' ? 'assets/icons/icon1.png' : 'assets/icons/icon2.png';
        avatar.className = `${sender}-avatar`;
        avatar.alt = sender === 'user' ? 'User' : 'AI';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = text;
        
        content.appendChild(messageText);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        // Insert before loading indicator or at the end
        const loadingIndicator = this.messagesContainer.querySelector('#loading-indicator');
        if (loadingIndicator && loadingIndicator.parentNode === this.messagesContainer) {
            this.messagesContainer.insertBefore(messageDiv, loadingIndicator);
        } else {
            this.messagesContainer.appendChild(messageDiv);
        }
        
        // Scroll to bottom
        this.scrollToBottom();
        
        // Add animation
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            messageDiv.style.transition = 'all 0.3s ease';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 50);
    }
    
    showLoading(show) {
        if (show) {
            // Remove existing loading indicator if any
            const existingLoading = this.messagesContainer.querySelector('.loading-message');
            if (existingLoading) {
                existingLoading.remove();
            }

            // Create new loading message with AI avatar
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading-message';
            
            // Add AI avatar
            const avatar = document.createElement('img');
            avatar.src = 'assets/icons/icon2.png';
            avatar.className = 'ai-avatar';
            avatar.alt = 'AI';
            
            // Create loading dots container
            const dotsContainer = document.createElement('div');
            dotsContainer.className = 'loading-dots';
            
            // Add dots
            for (let i = 0; i < 3; i++) {
                const dot = document.createElement('div');
                dot.className = 'dot';
                dotsContainer.appendChild(dot);
            }
            
            // Assemble the loading message
            loadingDiv.appendChild(avatar);
            loadingDiv.appendChild(dotsContainer);
            
            // Add to messages container
            this.messagesContainer.appendChild(loadingDiv);
            this.scrollToBottom();
        } else {
            // Remove loading message
            const loadingMessage = this.messagesContainer.querySelector('.loading-message');
            if (loadingMessage) {
                loadingMessage.remove();
            }
        }
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }
    
    showVideoInput() {
        this.videoInputSection.classList.remove('hidden');
        this.chatSection.classList.add('hidden');
        this.errorSection.classList.add('hidden');
        
        // Reset state
        this.currentVideoId = null;
        this.sessionId = this.generateSessionId();
        this.videoInput.value = '';
        this.clearChat();
        
        // Focus input
        this.videoInput.focus();
    }
    
    showChat() {
        this.videoInputSection.classList.add('hidden');
        this.chatSection.classList.remove('hidden');
        this.errorSection.classList.add('hidden');
        
        // Update video ID display
        this.videoIdDisplay.textContent = `Video ID: ${this.currentVideoId}`;
        
        // Focus message input
        this.messageInput.focus();
    }
    
    showError(message, title = 'Error') {
        this.videoInputSection.classList.add('hidden');
        this.chatSection.classList.add('hidden');
        this.errorSection.classList.remove('hidden');
        
        this.errorTitle.textContent = title;
        this.errorMessage.textContent = message;
    }
    
    clearChat() {
        // Keep only the welcome message
        const messages = this.messagesContainer.querySelectorAll('.message');
        messages.forEach(msg => msg.remove());
        
        // Clear message input
        this.messageInput.value = '';
    }
}

// Initialize the UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.vidSageUI = new VidSageUI();
});