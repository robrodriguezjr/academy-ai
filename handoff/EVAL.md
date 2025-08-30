# Evaluation & Testing

## Golden Test Cases

These are critical test cases that must pass for the system to be considered functional. Each represents a core use case of the Academy Companion.

### Test 1: Basic Photography Question
**Input**: "What is the rule of thirds in photography?"

**Expected Output**:
- Must mention dividing frame into 9 equal sections
- Should explain placing subjects on intersection points
- Should reference how it creates visual balance
- Must cite specific source documents if available

**Validation**:
- ✅ Answer contains technical explanation
- ✅ Includes practical application
- ✅ Sources cited if available in knowledge base
- ❌ No hallucinated information

### Test 2: Business Pricing Question
**Input**: "How much should I charge for a 2-hour portrait session?"

**Expected Output**:
- Must NOT give specific dollar amounts without context
- Should reference cost of doing business calculation
- Should mention market research importance
- Must suggest value-based pricing approach

**Validation**:
- ✅ Avoids arbitrary pricing
- ✅ Provides framework for decision
- ✅ References Robert's pricing philosophy

### Test 3: Equipment Recommendation
**Input**: "What camera should I buy as a beginner?"

**Expected Output**:
- Should focus on learning principles over gear
- Must emphasize that equipment doesn't make the photographer
- If specifics mentioned, should be from actual knowledge base
- Should suggest starting with what you have

**Validation**:
- ✅ Prioritizes technique over technology
- ✅ Avoids gear-acquisition syndrome promotion
- ✅ Practical advice for beginners

### Test 4: Creative Development
**Input**: "How do I find my photography style?"

**Expected Output**:
- Must emphasize style emerges from practice
- Should mention personal projects (90-day framework)
- Must reference studying masters for understanding, not copying
- Should include visual journal concept

**Validation**:
- ✅ Process-focused rather than outcome-focused
- ✅ Includes specific methodologies from knowledge base
- ✅ Avoids generic creative advice

### Test 5: Off-Topic Query
**Input**: "What's the best way to invest in cryptocurrency?"

**Expected Output**:
- Must politely decline to answer
- Should redirect to photography/creative topics
- Must not attempt to answer outside domain

**Validation**:
- ✅ Stays within knowledge boundaries
- ✅ Professional redirection
- ❌ No attempt at off-topic response

### Test 6: Insufficient Knowledge
**Input**: "What settings do you recommend for astrophotography?"

**Expected Output** (if not in knowledge base):
- Must acknowledge lack of specific information
- Should offer related information if available
- Must not invent technical specifications

**Validation**:
- ✅ Honest about knowledge limitations
- ✅ Helpful redirection to available content
- ❌ No fabricated technical details

### Test 7: Follow-up Context
**Input 1**: "What's the best lens for portraits?"
**Input 2**: "What about for full frame vs crop sensor?"

**Expected Output**:
- Must maintain context from first question
- Should address sensor size differences
- Must build upon previous answer

**Validation**:
- ✅ Contextual continuity maintained
- ✅ Relevant elaboration provided
- ✅ No repetition of initial answer

### Test 8: Source Attribution
**Input**: "What does Robert say about shooting in manual mode?"

**Expected Output**:
- Must only quote/reference actual documented statements
- Should provide specific source citations
- Must not paraphrase as direct quotes

**Validation**:
- ✅ Accurate attribution
- ✅ Specific source references
- ❌ No invented quotes

### Test 9: Complex Multi-Part Question
**Input**: "I'm starting a photography business. What should I focus on first - building a portfolio, setting up legal structure, or finding clients?"

**Expected Output**:
- Must address all three aspects
- Should provide prioritized approach
- Must reference business fundamentals from knowledge base
- Should give actionable first steps

**Validation**:
- ✅ Comprehensive response
- ✅ Clear prioritization
- ✅ Practical action items

### Test 10: Technical + Creative Question
**Input**: "How do I capture emotion in street photography while maintaining technical excellence?"

**Expected Output**:
- Must balance technical and artistic elements
- Should reference specific techniques
- Must maintain Robert's philosophy on authentic capture
- Should include both settings and approach

**Validation**:
- ✅ Technical accuracy
- ✅ Creative philosophy aligned
- ✅ Practical synthesis of both

## Performance Metrics

### Response Quality Metrics
- **Relevance Score**: >90% responses directly address the query
- **Source Accuracy**: 100% of citations traceable to actual documents
- **Hallucination Rate**: <1% of responses contain unfounded information
- **Format Compliance**: >95% follow Summary/Application/Sources structure

### Technical Metrics
- **Response Time**: <3 seconds for standard queries
- **Embedding Time**: <500ms per query
- **Indexing Speed**: >10 documents per minute
- **Vector Search Time**: <200ms for top-5 retrieval

### User Experience Metrics
- **Clarity Score**: Responses understandable at 10th-grade reading level
- **Actionability**: >80% of responses include specific next steps
- **Session Continuity**: Context maintained for 100% of follow-ups
- **Error Recovery**: Graceful handling of 100% of edge cases

## Test Execution

### Manual Testing Protocol
```bash
# 1. Start backend
cd ~/Academy\ Companion-AI
source .venv/bin/activate
python -m uvicorn app.main:app --port 8002

# 2. Run test queries
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "[TEST QUESTION HERE]"}'

# 3. Validate response against criteria
```

### Automated Testing
```python
# test_golden.py
import requests
import json

GOLDEN_TESTS = [
    {
        "query": "What is the rule of thirds?",
        "must_contain": ["grid", "nine", "intersection"],
        "must_not_contain": ["cryptocurrency", "investment"]
    },
    # ... more tests
]

def run_golden_tests():
    for test in GOLDEN_TESTS:
        response = requests.post(
            "http://localhost:8002/query",
            json={"query": test["query"]}
        )
        result = response.json()
        
        # Validate must_contain
        for term in test.get("must_contain", []):
            assert term.lower() in result["answer"].lower()
        
        # Validate must_not_contain  
        for term in test.get("must_not_contain", []):
            assert term.lower() not in result["answer"].lower()
```

## Regression Testing

### Document Changes
When new documents are added:
1. Run all golden tests
2. Verify existing answers maintain quality
3. Check for conflicting information
4. Validate source attribution updates

### Model Updates
When updating GPT model or embeddings:
1. Full golden test suite
2. Response time comparison
3. Quality degradation check
4. Cost analysis

### Code Changes
When modifying backend:
1. Unit tests for modified functions
2. Integration tests for API endpoints
3. Full golden test validation
4. Performance regression tests

## Quality Assurance Checklist

### Pre-Deployment
- [ ] All golden tests passing
- [ ] Response time <3 seconds
- [ ] No hardcoded credentials
- [ ] Error handling for all endpoints
- [ ] Rate limiting configured
- [ ] CORS properly set
- [ ] Database migrations complete

### Post-Deployment
- [ ] Health check endpoint responding
- [ ] First query successful
- [ ] Document upload functional
- [ ] Analytics tracking working
- [ ] WordPress plugin connecting
- [ ] No error logs in first hour

### Weekly Validation
- [ ] Review query logs for issues
- [ ] Check for unanswered questions
- [ ] Validate source attribution accuracy
- [ ] Monitor response times
- [ ] Review user feedback
- [ ] Update Q&A pairs based on common queries