# Key Decisions & Rationale

## Architecture Decisions

### Decision: RAG over Fine-tuning
**Choice**: Retrieval-Augmented Generation using ChromaDB + GPT-4o-mini

**Rationale**:
- Content frequently updated (new blog posts, sessions)
- Maintains source attribution for credibility
- Cost-effective compared to fine-tuning
- Easier to debug and modify responses

**Rejected Alternative**: Fine-tuned model
- Would require retraining for updates
- Loses source attribution capability
- Higher cost and complexity
- Black box behavior harder to control

**Tradeoffs**:
- (+) Dynamic content updates
- (+) Explainable responses with sources
- (-) Slightly higher latency (vector search + LLM)
- (-) Dependent on embedding quality

### Decision: ChromaDB for Vector Storage
**Choice**: ChromaDB over alternatives (Pinecone, Weaviate, Qdrant)

**Rationale**:
- Open source with local storage option
- Simple deployment without external dependencies
- Sufficient for <200k vectors scale
- Good Python integration

**Rejected Alternatives**:
- Pinecone: Unnecessary cloud dependency and cost
- PostgreSQL + pgvector: Added database complexity
- FAISS: Lacks built-in persistence and metadata handling

**Tradeoffs**:
- (+) Self-hosted, no external costs
- (+) Simple deployment
- (-) Less scalable than cloud solutions
- (-) Fewer advanced features

### Decision: FastAPI Framework
**Choice**: FastAPI over Flask/Django

**Rationale**:
- Native async support for better performance
- Automatic API documentation (OpenAPI/Swagger)
- Type hints and validation built-in
- Modern Python features

**Rejected Alternatives**:
- Flask: Lacks built-in async and validation
- Django: Overkill for API-only service
- Express.js: Would split tech stack

**Tradeoffs**:
- (+) Performance and modern features
- (+) Developer experience
- (-) Smaller community than Flask/Django
- (-) Newer, less battle-tested

### Decision: Railway Deployment
**Choice**: Railway over AWS/GCP/Heroku

**Rationale**:
- Simple deployment from GitHub
- Persistent volume support for ChromaDB
- Predictable pricing at small scale
- Minimal DevOps complexity

**Rejected Alternatives**:
- AWS: Overcomplicated for current scale
- Heroku: No persistent filesystem
- Vercel: Doesn't support Python well
- Self-hosted: Maintenance burden

**Tradeoffs**:
- (+) Simplicity and speed to deploy
- (+) Good developer experience
- (-) Less control than AWS
- (-) Potential vendor lock-in

## Content Processing Decisions

### Decision: 1000 Token Chunks with 100 Overlap
**Choice**: Chunk size ~1000 tokens, overlap ~100 tokens

**Rationale**:
- Balances context completeness with retrieval precision
- Overlap ensures concepts aren't split
- Fits well within GPT context limits
- Optimal for paragraph-level information

**Rejected Alternatives**:
- Smaller chunks (200-500): Too granular, loses context
- Larger chunks (2000+): Less precise retrieval
- No overlap: Risks splitting important concepts

**Tradeoffs**:
- (+) Good balance of precision and context
- (+) Handles most content types well
- (-) May split very long concepts
- (-) More vectors to store/search

### Decision: YAML Frontmatter for Metadata
**Choice**: Parse YAML frontmatter from Markdown files

**Rationale**:
- Human-readable and editable
- Standard in static site generators
- Preserves metadata through conversions
- Git-friendly for version control

**Rejected Alternative**: Database-only metadata
- Would separate content from metadata
- Harder to manage in bulk
- Loss of portability

**Tradeoffs**:
- (+) Portable and version-controlled
- (+) Easy manual editing
- (-) Parsing complexity
- (-) Not all formats support it

## Frontend Decisions

### Decision: WordPress Plugin for Members
**Choice**: Native WordPress plugin over iframe/external app

**Rationale**:
- Seamless authentication with existing members
- Native integration with site design
- No CORS or security complications
- Better mobile experience

**Rejected Alternatives**:
- Iframe embed: Security and UX issues
- Separate subdomain: Authentication complexity
- JavaScript widget: Less control

**Tradeoffs**:
- (+) Best user experience
- (+) Secure authentication
- (-) WordPress-specific code
- (-) Updates require plugin deployment

### Decision: React for Admin Dashboard
**Choice**: React + TypeScript for dashboard

**Rationale**:
- Rich interactivity for admin features
- Type safety with TypeScript
- Excellent charting libraries
- Modern developer experience

**Rejected Alternative**: Server-side rendered (Django admin)
- Less interactive
- Poorer real-time updates
- Limited UI capabilities

**Tradeoffs**:
- (+) Rich, interactive UI
- (+) Better developer experience
- (-) Separate deployment
- (-) Additional complexity

## Data Management Decisions

### Decision: SQLite for Metadata
**Choice**: SQLite over PostgreSQL/MySQL

**Rationale**:
- Zero configuration database
- Sufficient for metadata scale
- Single file backup/restore
- No separate database server

**Rejected Alternative**: PostgreSQL
- Overkill for current needs
- Additional deployment complexity
- Another service to manage

**Tradeoffs**:
- (+) Simplicity
- (+) Portability
- (-) Limited concurrent writes
- (-) Less suitable if scaling

### Decision: Local Document Storage
**Choice**: Store documents in filesystem during indexing

**Rationale**:
- Simple file management
- Easy backup and version control
- Direct access for debugging
- No blob storage complexity

**Rejected Alternative**: S3/Cloud storage
- Unnecessary complexity
- Additional costs
- Network latency

**Tradeoffs**:
- (+) Simplicity and control
- (+) No external dependencies
- (-) Manual backup needed
- (-) Not distributed

## Security Decisions

### Decision: Bearer Token for Admin
**Choice**: Simple bearer token over OAuth/JWT

**Rationale**:
- Single admin user currently
- Minimal complexity
- Sufficient for internal use
- Easy to rotate

**Rejected Alternative**: Full OAuth2
- Overcomplicated for single admin
- Additional infrastructure
- Unnecessary for current scale

**Tradeoffs**:
- (+) Simple implementation
- (+) Easy to understand
- (-) Less secure than OAuth2
- (-) Manual token management

### Decision: WordPress Auth for Users
**Choice**: Leverage WordPress native authentication

**Rationale**:
- Users already authenticated
- No duplicate user management
- Maintains single sign-on
- Trusted authentication system

**Rejected Alternative**: Separate auth system
- Would require user migration
- Duplicate password management
- Poor user experience

**Tradeoffs**:
- (+) Seamless user experience
- (+) Secure by default
- (-) Tied to WordPress
- (-) Limited flexibility

## Model Selection Decisions

### Decision: GPT-4o-mini for Generation
**Choice**: GPT-4o-mini over GPT-4 or GPT-3.5

**Rationale**:
- Best cost/quality balance
- Fast response times
- Sufficient quality for use case
- 10x cheaper than GPT-4

**Rejected Alternatives**:
- GPT-4: Too expensive for volume
- GPT-3.5: Lower quality responses
- Claude: API availability concerns

**Tradeoffs**:
- (+) Cost effective
- (+) Good performance
- (-) Not cutting edge
- (-) Occasional quality issues

### Decision: text-embedding-3-small
**Choice**: OpenAI's text-embedding-3-small model

**Rationale**:
- Good quality embeddings
- Cost effective
- 1536 dimensions reasonable size
- Same provider as LLM

**Rejected Alternative**: Custom embeddings
- Would require training
- Maintenance burden
- Uncertain quality

**Tradeoffs**:
- (+) Proven quality
- (+) No training needed
- (-) Vendor lock-in
- (-) Can't customize