<?php
/**
 * Plugin Name: Academy Companion Chat Simple
 * Description: Simple working AI chat for Academy Members
 * Version: 1.0
 * Author: Robert Rodriguez Jr
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Only show to Academy Members
function academy_simple_check_user() {
    if (!is_user_logged_in()) {
        return false;
    }
    
    $user = wp_get_current_user();
    return in_array('academy_member', $user->roles);
}

// Add the chat widget
function academy_simple_add_chat() {
    if (!academy_simple_check_user()) {
        return;
    }
    ?>
    <div id="academy-simple-chat-btn" style="position:fixed;bottom:20px;right:20px;width:60px;height:60px;background:#0EA5E9;border-radius:50%;cursor:pointer;z-index:999999;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,0,0,0.2);">
        <svg width="24" height="24" fill="white" viewBox="0 0 24 24">
            <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z"/>
        </svg>
    </div>
    
    <div id="academy-simple-backdrop" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:999998;display:none;"></div>
    
    <div id="academy-simple-chat" style="position:fixed;top:50%;left:50%;width:650px;height:700px;background:white;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,0.3);z-index:999999;display:none;transform:translate(-50%,-50%);max-width:95vw;max-height:95vh;">
        <div style="padding:20px;background:linear-gradient(135deg,#0EA5E9,#3B82F6);color:white;border-radius:20px 20px 0 0;text-align:center;">
            <h3 style="margin:0;font-size:20px;">🎓 Academy Companion</h3>
            <p style="margin:5px 0 0 0;font-size:14px;opacity:0.9;">Your AI Photography Assistant</p>
        </div>
        
        <div id="academy-simple-messages" style="height:500px;overflow-y:auto;padding:20px;background:#f8f9fa;">
            <div style="background:white;padding:15px;border-radius:15px;margin-bottom:15px;border:1px solid #e0e0e0;">
                Hello! I'm Academy Companion, your AI learning assistant from Creative Path Academy. How can I help you with your learning journey today?
            </div>
        </div>
        
        <div style="padding:20px;border-top:1px solid #e0e0e0;display:flex;gap:10px;">
            <input type="text" id="academy-simple-input" placeholder="Ask your question..." style="flex:1;padding:12px;border:2px solid #e0e0e0;border-radius:25px;outline:none;font-size:14px;">
            <button id="academy-simple-send" style="padding:12px 20px;background:#0EA5E9;color:white;border:none;border-radius:25px;cursor:pointer;font-weight:600;">Send</button>
        </div>
    </div>

    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const btn = document.getElementById('academy-simple-chat-btn');
        const backdrop = document.getElementById('academy-simple-backdrop');
        const chat = document.getElementById('academy-simple-chat');
        const input = document.getElementById('academy-simple-input');
        const send = document.getElementById('academy-simple-send');
        const messages = document.getElementById('academy-simple-messages');
        
        let isOpen = false;
        
        // Function to format markdown-like text to HTML
        function formatResponse(text) {
            // Convert **bold** to <strong>
            text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            
            // Convert numbered sections like "1) Summary" to bold headers
            text = text.replace(/^(\d+\)\s*\*\*.*?\*\*)/gm, '<div style="font-weight:600;color:#1F2937;margin:15px 0 8px 0;font-size:15px;">$1</div>');
            
            // Convert bullet points to proper list items
            text = text.replace(/^\s*[-•]\s+(.+)$/gm, '<li style="margin:4px 0;line-height:1.5;">$1</li>');
            
            // Wrap consecutive list items in <ul>
            text = text.replace(/(<li.*?<\/li>\s*)+/g, function(match) {
                return '<ul style="margin:8px 0;padding-left:20px;">' + match + '</ul>';
            });
            
            // Convert line breaks to <br> for better spacing
            text = text.replace(/\n\n/g, '<br><br>');
            text = text.replace(/\n/g, '<br>');
            
            // Make links clickable - handle both markdown and plain URLs
            text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color:#0EA5E9;text-decoration:none;font-weight:500;">$1</a>');
            
            // Remove or clean up source citations that appear in the text
            text = text.replace(/3\)\s*\*\*Sources\*\*:?\s*[\s\S]*$/, ''); // Remove "3) Sources:" section
            text = text.replace(/Sources:\s*[\s\S]*$/, ''); // Remove "Sources:" section
            
            return text;
        }
        
        btn.addEventListener('click', function() {
            if (isOpen) {
                chat.style.display = 'none';
                backdrop.style.display = 'none';
                isOpen = false;
            } else {
                chat.style.display = 'block';
                backdrop.style.display = 'block';
                isOpen = true;
            }
        });
        
        backdrop.addEventListener('click', function() {
            chat.style.display = 'none';
            backdrop.style.display = 'none';
            isOpen = false;
        });
        
        function sendMessage() {
            const query = input.value.trim();
            if (!query) return;
            
            // Add user message
            messages.innerHTML += '<div style="text-align:right;margin:10px 0;"><div style="background:#0EA5E9;color:white;padding:10px 15px;border-radius:15px;display:inline-block;max-width:70%;">' + query + '</div></div>';
            
            // Add loading
            messages.innerHTML += '<div id="loading" style="background:white;padding:15px;border-radius:15px;margin:10px 0;border:1px solid #e0e0e0;"><em>Thinking...</em></div>';
            
            input.value = '';
            messages.scrollTop = messages.scrollHeight;
            
            // Call API
            fetch('https://academy-ai-production.up.railway.app/query', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: query, top_k: 5})
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('loading').remove();
                
                if (data.answer) {
                    const formattedAnswer = formatResponse(data.answer);
                    
                    // Add sources if available
                    let sourcesHtml = '';
                    if (data.sources && data.sources.length > 0) {
                        sourcesHtml = '<div style="margin-top:15px;padding:12px;background:#f8f9fa;border-radius:8px;border-left:3px solid #0EA5E9;">';
                        sourcesHtml += '<div style="font-weight:600;color:#374151;margin-bottom:8px;font-size:13px;">📚 Sources:</div>';
                        data.sources.forEach(function(source, index) {
                            sourcesHtml += '<div style="margin:4px 0;font-size:12px;color:#6b7280;">';
                            sourcesHtml += '• <strong>' + (source.title || 'Document ' + (index + 1)) + '</strong>';
                            if (source.url) {
                                sourcesHtml += ' - <a href="' + source.url + '" target="_blank" style="color:#0EA5E9;text-decoration:none;">View Article</a>';
                            } else if (source.path) {
                                sourcesHtml += ' - <em>' + source.source + '</em>';
                            }
                            sourcesHtml += '</div>';
                        });
                        sourcesHtml += '</div>';
                    }
                    
                    messages.innerHTML += '<div style="background:white;padding:15px;border-radius:15px;margin:10px 0;border:1px solid #e0e0e0;line-height:1.6;">' + formattedAnswer + sourcesHtml + '</div>';
                } else {
                    messages.innerHTML += '<div style="background:white;padding:15px;border-radius:15px;margin:10px 0;border:1px solid #e0e0e0;">Sorry, I encountered an error. Please try again.</div>';
                }
                
                messages.scrollTop = messages.scrollHeight;
            })
            .catch(error => {
                document.getElementById('loading').remove();
                messages.innerHTML += '<div style="background:white;padding:15px;border-radius:15px;margin:10px 0;border:1px solid #e0e0e0;">Sorry, I encountered an error. Please try again.</div>';
                messages.scrollTop = messages.scrollHeight;
            });
        }
        
        send.addEventListener('click', sendMessage);
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
    });
    </script>
    <?php
}
add_action('wp_footer', 'academy_simple_add_chat');
?>
