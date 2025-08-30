(function() {
    // Wait for page to load
    window.addEventListener('DOMContentLoaded', function() {
        const chatRoot = document.getElementById('academy-companion-root');
        if (!chatRoot) return;
        
        // Create chat HTML
        chatRoot.innerHTML = `
            <div class="academy-chat">
                <div class="chat-header">
                    <h3>Academy Companion</h3>
                    <span class="subtitle">Your AI Photography Assistant</span>
                </div>
                
                <div class="messages" id="chat-messages">
                    <div class="message assistant">
                        <div class="content">Hello! I'm Academy Companion, your AI learning assistant from Creative Path Academy. How can I help you with your photography journey today?</div>
                    </div>
                    <div class="suggestions" id="suggestions">
                        <p>Try asking:</p>
                        <button class="suggestion-chip" onclick="useSuggestion('How do I find my photography style?')">How do I find my photography style?</button>
                        <button class="suggestion-chip" onclick="useSuggestion('Tips for better portrait lighting')">Tips for better portrait lighting</button>
                        <button class="suggestion-chip" onclick="useSuggestion('How should I price my services?')">How should I price my services?</button>
                    </div>
                </div>
                
                <div class="input-area">
                    <input type="text" id="chat-input" placeholder="Ask about photography, business, techniques..." />
                    <button id="chat-send">Send</button>
                </div>
            </div>
        `;
        
        // Set up event handlers
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('chat-send');
        const messages = document.getElementById('chat-messages');
        
        sendBtn.addEventListener('click', sendMessage);
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
        
        window.useSuggestion = function(text) {
            input.value = text;
            document.getElementById('suggestions').style.display = 'none';
        };
        
        async function sendMessage() {
            const query = input.value.trim();
            if (!query) return;
            
            // Hide suggestions after first message
            const suggestions = document.getElementById('suggestions');
            if (suggestions) suggestions.style.display = 'none';
            
            // Add user message
            messages.innerHTML += `
                <div class="message user">
                    <div class="content">${query}</div>
                </div>
            `;
            
            // Clear input and show loading
            input.value = '';
            messages.innerHTML += `
                <div class="message assistant loading" id="loading">
                    <div class="content">Thinking...</div>
                </div>
            `;
            
            // Scroll to bottom
            messages.scrollTop = messages.scrollHeight;
            
            try {
                // Call API
                const response = await fetch(academyCompanion.apiUrl + '/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: query,
                        top_k: 5
                    })
                });
                
                const data = await response.json();
                
                // Remove loading message
                const loadingMsg = document.getElementById('loading');
                if (loadingMsg) loadingMsg.remove();
                
                // Add assistant response
                let sourcesHtml = '';
                if (data.sources && data.sources.length > 0) {
                    sourcesHtml = '<div class="sources"><small>Sources: ';
                    data.sources.forEach(src => {
                        sourcesHtml += ` • ${src.title || 'Document'}`;
                    });
                    sourcesHtml += '</small></div>';
                }
                
                messages.innerHTML += `
                    <div class="message assistant">
                        <div class="content">${data.answer}</div>
                        ${sourcesHtml}
                    </div>
                `;
                
            } catch (error) {
                // Remove loading and show error
                const loadingMsg = document.getElementById('loading');
                if (loadingMsg) loadingMsg.remove();
                
                messages.innerHTML += `
                    <div class="message assistant">
                        <div class="content">Sorry, I encountered an error. Please try again.</div>
                    </div>
                `;
            }
            
            // Scroll to bottom
            messages.scrollTop = messages.scrollHeight;
        }
    });
})();
