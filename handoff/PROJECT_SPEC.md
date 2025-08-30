# Academy Companion - Project Specification

## Purpose
Academy Companion is an AI-powered knowledge assistant for Creative Path Academy, designed to provide personalized, contextual answers about photography, creative business, and artistic development based on Robert Rodriguez Jr's extensive body of work and teaching materials.

## Target Audience
- **Primary**: Creative Path Academy members (50-100 photographers and artists)
- **Secondary**: Prospective members evaluating the academy
- **User Profile**: Professional and aspiring photographers seeking guidance on technique, business, and creative development

## Core Functionality

### 1. Knowledge-Based Q&A
- Answers questions strictly from indexed content (900+ blog posts, 60+ workshop materials, 50+ session transcripts)
- Returns sources with each answer for credibility
- Formats responses in Robert's teaching style (clear, practical, encouraging)

### 2. Document Management
- Upload and index new training materials (MD, TXT, PDF)
- Track document status (indexed, pending, failed)
- Character count tracking against limits
- Batch operations for reindexing

### 3. Training Enhancement
- Direct text training input for quick knowledge additions
- Q&A pairs for frequently asked questions
- Self-improving capability through usage tracking

### 4. Analytics Dashboard
- Query volume tracking (daily/weekly/monthly)
- Popular topics identification
- User engagement metrics
- Response time monitoring

### 5. Multi-Platform Access
- WordPress plugin for member-only access
- Raycast extension for local development
- Web API for third-party integrations

## Key Features

### User-Facing
- **Conversational Interface**: Natural language interaction with suggested questions
- **Source Attribution**: Every answer includes referenced documents
- **Session Context**: Maintains conversation history within a session
- **Response Formatting**: Structured answers (Summary → How to Apply → Sources)

### Admin-Facing
- **Document Upload**: Drag-and-drop interface for new content
- **Usage Analytics**: Real-time metrics and trend visualization
- **Content Management**: Add/edit/delete indexed documents
- **Q&A Management**: Pre-define responses to common questions

## Success Metrics
- **Response Accuracy**: >90% relevant answers from knowledge base
- **Response Time**: <3 seconds for standard queries
- **User Satisfaction**: Measured through query patterns and follow-ups
- **Content Coverage**: 100% of uploaded documents successfully indexed

## Constraints
- **Knowledge Boundary**: Only answers from indexed content, no general knowledge
- **Rate Limits**: OpenAI API constraints (3000 req/min)
- **Storage**: 10GB Railway volume for ChromaDB vectors
- **Character Limit**: 12M characters for training data

## Integration Points
- **OpenAI API**: GPT-4o-mini for response generation, text-embedding-3-small for vectors
- **ChromaDB**: Vector storage and similarity search
- **Railway**: Cloud hosting platform
- **WordPress**: Member authentication and access control