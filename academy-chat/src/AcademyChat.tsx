import React, { useState } from 'react';
import axios from 'axios';
import './AcademyChat.css';

const API_URL = 'https://academy-ai-production.up.railway.app';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{ title?: string; url?: string }>;
}

export const AcademyChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hello! I'm Academy Companion, your AI learning assistant from Creative Path Academy. How can I help you with your photography journey today?"
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);

  const suggestions = [
    "How do I find my photography style?",
    "What's the best camera for beginners?",
    "How should I price my photography services?",
    "Tips for better portrait lighting"
  ];

  const handleSuggestion = (suggestion: string) => {
    setInput(suggestion);
    setShowSuggestions(false);
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/query`, {
        query: userMessage,
        top_k: 5
      });

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }]);
    }
    setLoading(false);
  };

  return (
    <div className="academy-chat">
      <div className="chat-header">
        <h3>Academy Companion</h3>
        <span className="subtitle">Ask me anything about photography</span>
      </div>
      
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="content">{msg.content}</div>
            {msg.sources && msg.sources.length > 0 && (
              <div className="sources">
                <small>Sources:</small>
                {msg.sources.map((src, i) => (
                  <small key={i}> • {src.title}</small>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="message assistant loading">Thinking...</div>}
        
        {showSuggestions && messages.length === 1 && (
          <div className="suggestions">
            <p>Try asking:</p>
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                className="suggestion-chip"
                onClick={() => handleSuggestion(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask about photography, business, techniques..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
};
