import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useDropzone } from 'react-dropzone';
import './Dashboard.css';

const API_URL = process.env.REACT_APP_API_URL || 'https://academy-ai-production.up.railway.app';
const ADMIN_TOKEN = process.env.REACT_APP_ADMIN_TOKEN || 'supersecret123';

interface Document {
  id: string;
  title: string;
  path: string;
  chunk_count: number;
  last_indexed: string;
}

interface Metrics {
  total_queries: number;
  queries_today: number;
  queries_week: number;
  active_users: number;
  avg_response_time: number;
  popular_topics: { topic: string; count: number }[];
  daily_usage: { date: string; count: number }[];
  messages_sent: number;
  training_characters: number;
}

interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  sources?: { title: string; url?: string; source?: string }[];
}

export const Dashboard: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [vectorCount, setVectorCount] = useState(0);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [activeView, setActiveView] = useState<'overview' | 'chat-history' | 'leads' | 'documents' | 'training' | 'qa'>('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      text: 'Hello! I\'m Academy Companion, your AI learning assistant from Creative Path Academy. How can I help you with your photography journey today?',
      isUser: false,
      timestamp: new Date()
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchStatus();
    fetchDocuments();
    fetchMetrics();
  }, []);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [chatMessages, chatLoading]);

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/index-status`);
      setVectorCount(response.data.vector_count || 0);
    } catch (error) {
      console.error('Failed to fetch status:', error);
    }
  };

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_URL}/admin/documents`, {
        headers: { Authorization: `Bearer ${ADMIN_TOKEN}` }
      });
      setDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await axios.get(`${API_URL}/admin/metrics`, {
        headers: { Authorization: `Bearer ${ADMIN_TOKEN}` }
      });
      setMetrics(response.data);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
      // Set some demo data for visualization
      setMetrics({
        total_queries: 0,
        queries_today: 0,
        queries_week: 0,
        active_users: 0,
        avg_response_time: 0,
        messages_sent: 11,
        training_characters: 10700000,
        popular_topics: [],
        daily_usage: []
      });
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: async (acceptedFiles) => {
      setUploading(true);
      
      for (const file of acceptedFiles) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
          await axios.post(`${API_URL}/admin/upload-document`, formData, {
            headers: { 
              Authorization: `Bearer ${ADMIN_TOKEN}`,
              'Content-Type': 'multipart/form-data'
            }
          });
        } catch (error) {
          console.error('Upload failed:', error);
        }
      }
      
      setUploading(false);
      setShowUploadModal(false);
      await fetchDocuments();
      await fetchStatus();
    },
    accept: {
      'text/markdown': ['.md'],
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf']
    }
  });

  const triggerReindex = async () => {
    if (!window.confirm('Re-index all documents? This may take several minutes.')) return;
    
    try {
      await axios.post(`${API_URL}/reindex`, {}, {
        headers: { Authorization: `Bearer ${ADMIN_TOKEN}` }
      });
      alert('Reindexing started. Check back in a few minutes.');
    } catch (error) {
      alert('Failed to start reindexing');
    }
  };

  // Chat functionality
  const formatResponse = (text: string): string => {
    // Convert **bold** to <strong>
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert numbered sections like "1) Summary" to bold headers
    text = text.replace(/^(\d+\)\s*\*\*.*?\*\*)/gm, '<div style="font-weight:600;color:#ffffff;margin:15px 0 8px 0;font-size:15px;">$1</div>');
    
    // Convert bullet points to proper list items
    text = text.replace(/^\s*[-•]\s+(.+)$/gm, '<li style="margin:4px 0;line-height:1.5;color:rgba(255,255,255,0.9);">$1</li>');
    
    // Wrap consecutive list items in <ul>
    text = text.replace(/(<li.*?<\/li>\s*)+/g, function(match) {
      return '<ul style="margin:8px 0;padding-left:20px;">' + match + '</ul>';
    });
    
    // Convert line breaks to <br> for better spacing
    text = text.replace(/\n\n/g, '<br><br>');
    text = text.replace(/\n/g, '<br>');
    
    // Make links clickable
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color:#667eea;text-decoration:none;font-weight:500;">$1</a>');
    
    // Remove source citations that appear in the text
    text = text.replace(/3\)\s*\*\*Sources\*\*:?\s*[\s\S]*$/, '');
    text = text.replace(/Sources:\s*[\s\S]*$/, '');
    
    return text;
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim() || chatLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      text: chatInput,
      isUser: true,
      timestamp: new Date()
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setChatLoading(true);

    try {
      const response = await axios.post(`${API_URL}/query`, {
        query: chatInput,
        top_k: 5
      });

      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: response.data.answer || 'Sorry, I encountered an error. Please try again.',
        isUser: false,
        timestamp: new Date(),
        sources: response.data.sources || []
      };

      setChatMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an error connecting to the API. Please try again.',
        isUser: false,
        timestamp: new Date()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleChatKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  };

  // Chart data
  const pieData = [
    { name: 'Used', value: 75 },
    { name: 'Remaining', value: 25 }
  ];
  const COLORS = ['#ff6b35', '#f7931e'];

  return (
    <div className="dashboard-container">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-icon">AC</div>
            {!sidebarCollapsed && <span>Academy Companion</span>}
          </div>
          <button onClick={() => setSidebarCollapsed(!sidebarCollapsed)} className="toggle-btn">
            ☰
          </button>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section">
            <div className="nav-section-title">ACTIVITY</div>
            <button 
              className={`nav-item ${activeView === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveView('overview')}
            >
              <span className="icon">📊</span>
              {!sidebarCollapsed && <span>Overview</span>}
            </button>
            <button 
              className={`nav-item ${activeView === 'chat-history' ? 'active' : ''}`}
              onClick={() => setActiveView('chat-history')}
            >
              <span className="icon">💬</span>
              {!sidebarCollapsed && <span>Chat History</span>}
            </button>
            <button 
              className={`nav-item ${activeView === 'leads' ? 'active' : ''}`}
              onClick={() => setActiveView('leads')}
            >
              <span className="icon">👥</span>
              {!sidebarCollapsed && <span>Users</span>}
            </button>
          </div>

          <div className="nav-section">
            <div className="nav-section-title">TRAINING DATA</div>
            <button 
              className={`nav-item ${activeView === 'documents' ? 'active' : ''}`}
              onClick={() => setActiveView('documents')}
            >
              <span className="icon">📄</span>
              {!sidebarCollapsed && <span>Documents</span>}
            </button>
            <button 
              className={`nav-item ${activeView === 'training' ? 'active' : ''}`}
              onClick={() => setActiveView('training')}
            >
              <span className="icon">📝</span>
              {!sidebarCollapsed && <span>Text Training</span>}
            </button>
            <button 
              className={`nav-item ${activeView === 'qa' ? 'active' : ''}`}
              onClick={() => setActiveView('qa')}
            >
              <span className="icon">❓</span>
              {!sidebarCollapsed && <span>Q&A</span>}
            </button>
          </div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="main-header">
          <h1>{activeView === 'overview' ? 'Overview' : 
               activeView === 'chat-history' ? 'Chat History' : 
               activeView === 'leads' ? 'Users' :
               activeView === 'documents' ? 'Links / Documents' : 
               activeView === 'training' ? 'Text Training' :
               'Q&A Management'}</h1>
          <div className="header-actions">
            <span className="user-info">Robert Rodriguez Jr</span>
          </div>
        </header>

        <div className="content-area">
          {activeView === 'overview' && (
            <>
              {/* ✨ TAILWIND TRANSFORMATION: Responsive grid with modern cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg hover:shadow-xl transition-shadow duration-300">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl">👥</span>
                    <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">Today's Users</span>
                  </div>
                  <div className="text-3xl font-bold text-white mb-1">{metrics?.active_users || 0}</div>
                  <div className="text-sm text-gray-500">Active Users</div>
                </div>

                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg hover:shadow-xl transition-shadow duration-300">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl">💬</span>
                    <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">Messages</span>
                  </div>
                  <div className="text-3xl font-bold text-orange-accent mb-1">{metrics?.queries_today || 0}</div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Total Messages</span>
                    <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">0.00%</span>
                  </div>
                </div>

                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg hover:shadow-xl transition-shadow duration-300">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl">📚</span>
                    <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">Messages Sent</span>
                  </div>
                  <div className="flex items-baseline space-x-2 mb-3">
                    <span className="text-3xl font-bold text-white">{metrics?.messages_sent || 11}</span>
                    <span className="text-lg text-gray-500">/ 2000</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-orange-accent h-2 rounded-full transition-all duration-500" style={{width: '0.55%'}}></div>
                  </div>
                </div>

                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg hover:shadow-xl transition-shadow duration-300">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl">🎯</span>
                    <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">Leads</span>
                  </div>
                  <div className="text-3xl font-bold text-white mb-1">0</div>
                  <div className="text-sm text-gray-500">Generated</div>
                </div>

                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg hover:shadow-xl transition-shadow duration-300">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl">📝</span>
                    <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">Training Data</span>
                  </div>
                  <div className="flex items-baseline space-x-2 mb-1">
                    <span className="text-2xl font-bold text-white">{(vectorCount * 1000).toLocaleString()}</span>
                    <span className="text-sm text-gray-500">/ 12M</span>
                  </div>
                  <div className="text-sm text-gray-500">Characters used</div>
                  <ResponsiveContainer width="100%" height={60}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={15}
                        outerRadius={25}
                        paddingAngle={0}
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* ✨ TAILWIND TRANSFORMATION: Responsive chart grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg">
                  <h3 className="text-xl font-semibold text-white mb-6 flex items-center">
                    <span className="mr-2">📈</span>
                    Activity Over Time
                  </h3>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={metrics?.daily_usage || []}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                        <XAxis dataKey="date" stroke="#9ca3af" />
                        <YAxis stroke="#9ca3af" />
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: '#2a2a2a',
                            border: '1px solid #404040',
                            borderRadius: '8px',
                            color: '#ffffff'
                          }}
                        />
                        <Line type="monotone" dataKey="count" stroke="#ff8c42" strokeWidth={3} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg">
                  <h3 className="text-xl font-semibold text-white mb-6 flex items-center">
                    <span className="mr-2">🌍</span>
                    Popular Countries
                  </h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-dark-bg rounded-lg hover:bg-gray-800 transition-colors">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">🇺🇸</span>
                        <span className="text-white font-medium">United States</span>
                      </div>
                      <span className="bg-orange-accent text-white px-3 py-1 rounded-full text-sm font-medium">5</span>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-dark-bg rounded-lg hover:bg-gray-800 transition-colors">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">🇨🇦</span>
                        <span className="text-white font-medium">Canada</span>
                      </div>
                      <span className="bg-gray-600 text-white px-3 py-1 rounded-full text-sm font-medium">2</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* ✨ TAILWIND TRANSFORMATION: Modern chat interface */}
              <div className="bg-dark-card rounded-xl border border-dark-border shadow-lg overflow-hidden">
                <div className="bg-gradient-to-r from-orange-accent to-orange-hover p-4">
                  <h3 className="text-xl font-semibold text-white flex items-center">
                    <span className="mr-2">💬</span>
                    Live Chat Interface
                  </h3>
                </div>
                <div className="h-96 flex flex-col">
                  <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={chatMessagesRef}>
                    {chatMessages.map((message) => (
                      <div key={message.id} className={`chat-message ${message.isUser ? 'user' : 'assistant'}`}>
                        <div className="message-content">
                          {message.isUser ? (
                            <span>{message.text}</span>
                          ) : (
                            <div dangerouslySetInnerHTML={{ __html: formatResponse(message.text) }} />
                          )}
                          {message.sources && message.sources.length > 0 && (
                            <div className="message-sources">
                              <div className="sources-header">📚 Sources:</div>
                              {message.sources.map((source, index) => (
                                <div key={index} className="source-item">
                                  • <strong>{source.title || `Document ${index + 1}`}</strong>
                                  {source.url && (
                                    <> - <a href={source.url} target="_blank" rel="noopener noreferrer">View Article</a></>
                                  )}
                                  {source.source && !source.url && (
                                    <> - <em>{source.source}</em></>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="message-time">
                          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                    ))}
                    {chatLoading && (
                      <div className="chat-message assistant loading">
                        <div className="message-content">
                          <span>Thinking...</span>
                        </div>
                      </div>
                    )}
                  </div>
                  {/* ✨ TAILWIND TRANSFORMATION: Modern input with button */}
                  <div className="border-t border-dark-border p-4">
                    <div className="flex space-x-3">
                      <textarea
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyPress={handleChatKeyPress}
                        placeholder="Ask about photography, business, or creative techniques..."
                        className="flex-1 bg-dark-bg border border-dark-border rounded-lg px-4 py-3 text-white placeholder-gray-400 resize-none focus:ring-2 focus:ring-orange-accent focus:border-transparent transition-all"
                        rows={2}
                        disabled={chatLoading}
                      />
                      <button 
                        onClick={sendChatMessage}
                        disabled={chatLoading || !chatInput.trim()}
                        className="bg-orange-accent hover:bg-orange-hover disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 flex items-center justify-center min-w-[60px]"
                      >
                        {chatLoading ? (
                          <div className="animate-spin">⏳</div>
                        ) : (
                          <span className="text-lg">→</span>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}

          {activeView === 'leads' && (
            <div className="users-view">
              {/* ✨ USERS DASHBOARD: Comprehensive user analytics */}
              
              {/* User Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl">👥</span>
                    <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">Total Users</span>
                  </div>
                  <div className="text-3xl font-bold text-white mb-1">1,247</div>
                  <div className="text-sm text-green-400">+23 this month</div>
                </div>

                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl">⚡</span>
                    <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">Active Users</span>
                  </div>
                  <div className="text-3xl font-bold text-orange-accent mb-1">{metrics?.active_users || 89}</div>
                  <div className="text-sm text-gray-500">This week</div>
                </div>

                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl">💬</span>
                    <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">Questions Asked</span>
                  </div>
                  <div className="text-3xl font-bold text-white mb-1">{metrics?.queries_today || 0}</div>
                  <div className="text-sm text-gray-500">Today</div>
                </div>

                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl">📊</span>
                    <span className="text-sm font-medium text-gray-400 uppercase tracking-wide">Engagement</span>
                  </div>
                  <div className="text-3xl font-bold text-white mb-1">67%</div>
                  <div className="text-sm text-green-400">+5% vs last week</div>
                </div>
              </div>

              {/* User Activity & Demographics */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {/* User Activity Chart */}
                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg">
                  <h3 className="text-xl font-semibold text-white mb-6 flex items-center">
                    <span className="mr-2">📈</span>
                    User Activity Over Time
                  </h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={metrics?.daily_usage || []}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                        <XAxis dataKey="date" stroke="#9ca3af" />
                        <YAxis stroke="#9ca3af" />
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: '#2a2a2a',
                            border: '1px solid #404040',
                            borderRadius: '8px',
                            color: '#ffffff'
                          }}
                        />
                        <Line type="monotone" dataKey="count" stroke="#ff8c42" strokeWidth={3} name="Active Users" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Top User Locations */}
                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg">
                  <h3 className="text-xl font-semibold text-white mb-6 flex items-center">
                    <span className="mr-2">🌍</span>
                    User Locations
                  </h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-dark-bg rounded-lg hover:bg-gray-800 transition-colors">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">🇺🇸</span>
                        <div>
                          <span className="text-white font-medium">United States</span>
                          <div className="text-sm text-gray-400">North America</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="bg-orange-accent text-white px-3 py-1 rounded-full text-sm font-medium">892</div>
                        <div className="text-xs text-gray-500 mt-1">71.5%</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 bg-dark-bg rounded-lg hover:bg-gray-800 transition-colors">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">🇨🇦</span>
                        <div>
                          <span className="text-white font-medium">Canada</span>
                          <div className="text-sm text-gray-400">North America</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="bg-gray-600 text-white px-3 py-1 rounded-full text-sm font-medium">234</div>
                        <div className="text-xs text-gray-500 mt-1">18.8%</div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-dark-bg rounded-lg hover:bg-gray-800 transition-colors">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">🇬🇧</span>
                        <div>
                          <span className="text-white font-medium">United Kingdom</span>
                          <div className="text-sm text-gray-400">Europe</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="bg-gray-600 text-white px-3 py-1 rounded-full text-sm font-medium">87</div>
                        <div className="text-xs text-gray-500 mt-1">7.0%</div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-dark-bg rounded-lg hover:bg-gray-800 transition-colors">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">🇦🇺</span>
                        <div>
                          <span className="text-white font-medium">Australia</span>
                          <div className="text-sm text-gray-400">Oceania</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="bg-gray-600 text-white px-3 py-1 rounded-full text-sm font-medium">34</div>
                        <div className="text-xs text-gray-500 mt-1">2.7%</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* User Insights */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Popular Topics */}
                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                    <span className="mr-2">🔥</span>
                    Popular Topics
                  </h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-white">Photography Basics</span>
                      <span className="bg-orange-accent/20 text-orange-accent px-2 py-1 rounded text-sm">342</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-white">Lightroom Editing</span>
                      <span className="bg-gray-600/20 text-gray-300 px-2 py-1 rounded text-sm">289</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-white">Business Tips</span>
                      <span className="bg-gray-600/20 text-gray-300 px-2 py-1 rounded text-sm">156</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-white">Composition</span>
                      <span className="bg-gray-600/20 text-gray-300 px-2 py-1 rounded text-sm">134</span>
                    </div>
                  </div>
                </div>

                {/* Usage Patterns */}
                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                    <span className="mr-2">⏰</span>
                    Usage Patterns
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-300">Peak Hours</span>
                        <span className="text-orange-accent">2-4 PM EST</span>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-300">Avg Session</span>
                        <span className="text-white">8.5 minutes</span>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-300">Questions/Session</span>
                        <span className="text-white">3.2</span>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-300">Return Rate</span>
                        <span className="text-green-400">73%</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Recent Activity */}
                <div className="bg-dark-card p-6 rounded-xl border border-dark-border shadow-lg">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                    <span className="mr-2">📝</span>
                    Recent Activity
                  </h3>
                  <div className="space-y-3 text-sm">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                      <span className="text-gray-300">New user from Canada</span>
                      <span className="text-gray-500 ml-auto">2m ago</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-orange-accent rounded-full"></div>
                      <span className="text-gray-300">Question about printing</span>
                      <span className="text-gray-500 ml-auto">5m ago</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                      <span className="text-gray-300">User session started</span>
                      <span className="text-gray-500 ml-auto">8m ago</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                      <span className="text-gray-300">New user from UK</span>
                      <span className="text-gray-500 ml-auto">12m ago</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeView === 'documents' && (
            <div className="documents-view">
              <div className="documents-header">
                <div className="stats-row">
                  <div className="stat-item">
                    <span className="stat-label">Crawled Links</span>
                    <span className="stat-value">{documents.length}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Characters</span>
                    <span className="stat-value">{(vectorCount * 1000).toLocaleString()} / 12M</span>
                  </div>
                  <div className="stat-item indexed">
                    <span className="stat-dot"></span>
                    <span className="stat-label">Indexed</span>
                    <span className="stat-value">{documents.length}</span>
                  </div>
                  <div className="stat-item pending">
                    <span className="stat-dot"></span>
                    <span className="stat-label">Pending</span>
                    <span className="stat-value">0</span>
                  </div>
                  <div className="stat-item failed">
                    <span className="stat-dot"></span>
                    <span className="stat-label">Failed</span>
                    <span className="stat-value">0</span>
                  </div>
                </div>
                {/* ✨ TAILWIND TRANSFORMATION: Modern upload button */}
                <button 
                  className="bg-orange-accent hover:bg-orange-hover text-white px-6 py-3 rounded-lg font-medium flex items-center space-x-2 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105" 
                  onClick={() => setShowUploadModal(true)}
                >
                  <span>📁</span>
                  <span>Upload Documents</span>
                </button>
              </div>

              <div className="documents-table">
                <div className="table-controls">
                  <input type="text" placeholder="Search..." className="search-input" />
                  <button className="btn-secondary">Retrain the bot</button>
                  <button className="btn-secondary">Delete (0)</button>
                </div>
                <table>
                  <thead>
                    <tr>
                      <th><input type="checkbox" /></th>
                      <th>STATUS</th>
                      <th>CHARS</th>
                      <th>DATA</th>
                      <th>DATE ADDED</th>
                      <th>RETRAIN</th>
                      <th>TYPE</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="empty-state">No documents indexed yet. Upload some files to get started.</td>
                      </tr>
                    ) : (
                      documents.map(doc => (
                        <tr key={doc.id}>
                          <td><input type="checkbox" /></td>
                          <td><span className="status-badge indexed">Indexed</span></td>
                          <td>{(doc.chunk_count * 1000).toLocaleString()}</td>
                          <td className="doc-title">{doc.title}</td>
                          <td>{new Date(doc.last_indexed).toLocaleDateString()}</td>
                          <td>✓</td>
                          <td><span className="type-badge">DOC</span></td>
                          <td>
                            <button className="btn-icon">🗑</button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeView === 'training' && (
            <div className="training-view">
              <div className="training-header">
                <p>This is a quick and easy method to quickly train your chatbot on extra data. Simply add any text below.</p>
              </div>
              <div className="training-content">
                <textarea 
                  className="training-textarea"
                  placeholder="Enter your training content here..."
                  onChange={(e) => console.log(e.target.value.length, 'characters')}
                ></textarea>
                <div className="training-footer">
                  <span className="char-count">0 characters</span>
                  <button className="btn-primary">Save</button>
                </div>
              </div>
            </div>
          )}

          {activeView === 'qa' && (
            <div className="qa-view">
              <div className="qa-header">
                <p>Use this section to add frequently asked questions and the responses the chatbot should provide.</p>
                <div className="qa-actions">
                  <button className="btn-success">↓ Upgrade for self improving Q&A</button>
                  <button className="btn-primary">⊕ Add Q&A</button>
                  <button className="btn-secondary">Save</button>
                  <button className="btn-secondary">Delete (0)</button>
                  <button className="btn-info">Export all</button>
                </div>
              </div>
              <div className="qa-list">
                <div className="qa-item">
                  <div className="qa-question">
                    <input type="text" placeholder="Enter Question" />
                  </div>
                  <div className="qa-answer">
                    <textarea placeholder="Enter Answer"></textarea>
                  </div>
                  <button className="btn-icon delete">🗑</button>
                </div>
              </div>
            </div>
          )}

          {/* Add other views as needed */}
        </div>
      </main>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Upload Documents</h2>
            <div {...getRootProps()} className="dropzone">
              <input {...getInputProps()} />
              {isDragActive ? (
                <p>Drop files here...</p>
              ) : (
                <div>
                  <div className="dropzone-icon">📁</div>
                  <p>Drag & drop documents here, or click to select</p>
                  <small>Supports: .md, .txt, .pdf</small>
                </div>
              )}
              {uploading && <p className="uploading">Uploading...</p>}
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowUploadModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;