(function() {
    // Wait for page to load
    window.addEventListener('DOMContentLoaded', function() {
        console.log('Academy Chat: DOM loaded, initializing...');
        
        // Check for embedded chat first
        const chatRoot = document.getElementById('academy-companion-root');
        console.log('Academy Chat: Embedded chat root found:', chatRoot);
        
        // Check for floating chat
        const floatingRoot = document.getElementById('academy-companion-root-float');
        const toggleButton = document.getElementById('academy-chat-toggle');
        const backdrop = document.getElementById('academy-companion-backdrop');
        console.log('Academy Chat: Floating elements found:', floatingRoot, toggleButton, backdrop);
        
        // Initialize embedded chat if present
        if (chatRoot) {
            initializeChat(chatRoot, false);
        }
        
        // Initialize floating chat if present
        if (floatingRoot && toggleButton && backdrop) {
            initializeFloatingChat(floatingRoot, toggleButton, backdrop);
        }
    });
    
    function initializeFloatingChat(chatRoot, toggleButton, backdrop) {
        console.log('Academy Chat: Initializing floating chat', chatRoot, toggleButton, backdrop);
        let isOpen = false;
        
        // Toggle chat visibility
        toggleButton.addEventListener('click', function(e) {
            console.log('Academy Chat: Toggle button clicked!', e);
            e.preventDefault();
            e.stopPropagation();
            
            if (isOpen) {
                chatRoot.style.display = 'none';
                chatRoot.classList.remove('show');
                backdrop.style.display = 'none';
                backdrop.classList.remove('show');
                isOpen = false;
            } else {
                if (!chatRoot.innerHTML.trim()) {
                    initializeChat(chatRoot, true);
                }
                
                // FORCE center positioning - override ALL CSS
                console.log('Academy Chat: Applying styles to chatRoot', chatRoot);
                chatRoot.style.cssText = `
                    position: fixed !important;
                    top: 50% !important;
                    left: 50% !important;
                    right: auto !important;
                    bottom: auto !important;
                    transform: translate(-50%, -50%) scale(0.95) !important;
                    width: 500px !important;
                    height: 650px !important;
                    z-index: 999999 !important;
                    background: white !important;
                    border-radius: 20px !important;
                    box-shadow: 0 25px 50px rgba(0,0,0,0.25) !important;
                    border: 5px solid red !important;
                    display: block !important;
                    opacity: 1 !important;
                    margin: 0 !important;
                `;
                console.log('Academy Chat: Aggressive styles applied with cssText');
                
                backdrop.style.display = 'block';
                chatRoot.style.display = 'block';
                setTimeout(() => {
                    backdrop.classList.add('show');
                    chatRoot.classList.add('show');
                    chatRoot.style.setProperty('transform', 'translate(-50%, -50%) scale(1)', 'important');
                    console.log('Academy Chat: Animation complete, final transform applied');
                }, 10);
                isOpen = true;
                
                // Hide unread indicator
                const unreadCount = document.getElementById('unread-count');
                if (unreadCount) {
                    unreadCount.style.display = 'none';
                }
            }
        });
        
        // Close chat when clicking backdrop
        backdrop.addEventListener('click', function(e) {
            if (isOpen && e.target === backdrop) {
                chatRoot.style.display = 'none';
                chatRoot.classList.remove('show');
                backdrop.style.display = 'none';
                backdrop.classList.remove('show');
                isOpen = false;
            }
        });
    }
    
    function initializeChat(chatRoot, isFloating) {
        // Create chat HTML
        const chatHtml = `
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
                        <button class="suggestion-chip">How do I find my photography style?</button>
                        <button class="suggestion-chip">Tips for better portrait lighting</button>
                        <button class="suggestion-chip">How should I price my services?</button>
                    </div>
                </div>
                
                <div class="input-area">
                    <input type="text" id="chat-input" placeholder="Ask about photography, business, techniques..." />
                    <button id="chat-send">Send</button>
                </div>
            </div>
        `;
        
        chatRoot.innerHTML = chatHtml;
        
        // Set up event handlers
        const input = chatRoot.querySelector('#chat-input');
        const sendBtn = chatRoot.querySelector('#chat-send');
        const messages = chatRoot.querySelector('#chat-messages');
        
        sendBtn.addEventListener('click', sendMessage);
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
        
        // Create scoped suggestion function for this chat instance
        const useSuggestion = function(text) {
            input.value = text;
            const suggestions = chatRoot.querySelector('#suggestions');
            if (suggestions) suggestions.style.display = 'none';
        };
        
        // Add click handlers to suggestion chips
        const suggestionChips = chatRoot.querySelectorAll('.suggestion-chip');
        suggestionChips.forEach(chip => {
            chip.addEventListener('click', function() {
                useSuggestion(this.textContent);
            });
        });
        
        async function sendMessage() {
            const query = input.value.trim();
            if (!query) return;
            
            // Hide suggestions after first message
            const suggestions = chatRoot.querySelector('#suggestions');
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
                const loadingMsg = chatRoot.querySelector('#loading');
                if (loadingMsg) loadingMsg.remove();
                
                // Check for API errors
                if (data.detail || !data.answer) {
                    const errorMsg = data.detail || 'Sorry, I encountered an error processing your request.';
                    messages.innerHTML += `
                        <div class="message assistant">
                            <div class="content">I'm experiencing some technical difficulties right now. Please try again in a few moments. If the issue persists, the system may be undergoing maintenance.</div>
                        </div>
                    `;
                    return;
                }
                
                // Format the AI response for better display
                let formattedAnswer = data.answer;
                
                // Convert **bold** to <strong>
                formattedAnswer = formattedAnswer.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                
                // Convert bullet points (- or •) to proper list items
                formattedAnswer = formattedAnswer.replace(/^\s*[-•]\s+(.+)$/gm, '<li>$1</li>');
                
                // Wrap consecutive list items in <ul> tags
                formattedAnswer = formattedAnswer.replace(/(<li>.*<\/li>)/gs, function(match) {
                    // Only wrap if not already wrapped
                    if (!match.includes('<ul>')) {
                        return '<ul>' + match + '</ul>';
                    }
                    return match;
                });
                
                // Convert line breaks to <br> for better spacing
                formattedAnswer = formattedAnswer.replace(/\n\n/g, '<br><br>');
                formattedAnswer = formattedAnswer.replace(/\n/g, '<br>');
                
                // Add sources
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
                        <div class="content">${formattedAnswer}</div>
                        ${sourcesHtml}
                    </div>
                `;
                
            } catch (error) {
                // Remove loading and show error
                const loadingMsg = chatRoot.querySelector('#loading');
                if (loadingMsg) loadingMsg.remove();
                
                messages.innerHTML += `
                    <div class="message assistant">
                        <div class="content">Sorry, I encountered an error. Please try again.</div>
                    </div>
                `;
            }
            
            // Scroll to bottom
            messages.scrollTop = messages.scrollHeight;
            
            // Show unread indicator if floating and closed
            if (isFloating && !chatRoot.closest('#academy-companion-root-float').classList.contains('show')) {
                const unreadCount = document.getElementById('unread-count');
                if (unreadCount) {
                    unreadCount.style.display = 'flex';
                }
            }
        }
    }
})();