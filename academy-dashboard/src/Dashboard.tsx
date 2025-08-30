import React, { useState, useEffect } from 'react';
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

export const Dashboard: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [vectorCount, setVectorCount] = useState(0);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [activeView, setActiveView] = useState<'overview' | 'chat-history' | 'leads' | 'documents' | 'training' | 'qa'>('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    fetchStatus();
    fetchDocuments();
    fetchMetrics();
  }, []);

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

  // Chart data
  const pieData = [
    { name: 'Used', value: 75 },
    { name: 'Remaining', value: 25 }
  ];
  const COLORS = ['#667eea', '#e0e7ff'];

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
              {!sidebarCollapsed && <span>Members</span>}
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
               activeView === 'leads' ? 'Members' :
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
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-icon">👥</span>
                    <span className="metric-label">Today's Users</span>
                  </div>
                  <div className="metric-value">{metrics?.active_users || 0}</div>
                  <div className="metric-subtext">Users</div>
                </div>

                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-icon">💬</span>
                    <span className="metric-label">Messages</span>
                  </div>
                  <div className="metric-value">{metrics?.queries_today || 0}</div>
                  <div className="metric-subtext">Messages</div>
                  <div className="metric-badge">0.00%</div>
                </div>

                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-icon">📚</span>
                    <span className="metric-label">Has sent</span>
                  </div>
                  <div className="metric-value">{metrics?.messages_sent || 11} <span className="metric-total">/ 2000</span></div>
                  <div className="metric-chart">
                    <div className="progress-bar">
                      <div className="progress-fill" style={{width: '0.55%'}}></div>
                    </div>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-icon">🎯</span>
                    <span className="metric-label">Leads</span>
                  </div>
                  <div className="metric-value">0</div>
                  <div className="metric-subtext">Generated</div>
                </div>

                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-icon">📝</span>
                    <span className="metric-label">Training</span>
                  </div>
                  <div className="metric-value">{(vectorCount * 1000).toLocaleString()} <span className="metric-unit">/ 12M</span></div>
                  <div className="metric-subtext">Characters used</div>
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

              <div className="chart-section">
                <div className="chart-card">
                  <h3>Activity Over Time</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={metrics?.daily_usage || []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="count" stroke="#667eea" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div className="world-map-card">
                  <h3>Popular Countries</h3>
                  <div className="map-placeholder">
                    <div className="country-list">
                      <div className="country-item">
                        <span className="country-flag">🇺🇸</span>
                        <span>United States</span>
                        <span className="country-count">5</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="chat-preview">
                <h3>Live Chat</h3>
                <div className="chat-widget">
                  <div className="chat-message assistant">
                    Hello! I'm Academy Companion, your AI learning assistant from Creative Path Academy. How can I help you with your photography journey today?
                  </div>
                </div>
              </div>
            </>
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
                <button className="btn-primary" onClick={() => setShowUploadModal(true)}>
                  <span>⊕</span> Add Links / Upload Docs
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