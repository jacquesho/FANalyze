# FANalyze 2.0 - Capstone Presentation Sequence & Talking Points 🎤

## 📋 Presentation Overview
**Total Time: 30 minutes**
- **Phase 1**: Real-time Pipeline (5 min)
- **Phase 2**: Batch & ML Pipeline (5 min)
- **Phase 3**: AI Agent & RAG (10 min)
- **Phase 4**: Advanced Features & Q&A (10 min)

---

## 🎯 Phase 1: Real-time Data Pipeline (5 minutes)

### **Opening Statement** (30 seconds)
> "FANalyze 2.0 is an end-to-end data engineering and AI analytics platform for music industry insights. I'll demonstrate how we process real-time ticket sales data, batch historical concert information, and enable natural language queries through an AI agent."

### **Step 1: CI/CD Pipeline Initiation** (1 minute)

**Action:**
- Start CI job (manual trigger or new commit)
- Show GitHub Actions workflow running

**Talking Points:**
- "Let me start by triggering our CI/CD pipeline. This demonstrates our DevOps implementation with GitHub Actions."
- "Our CI pipeline includes automated checks for code quality, linting, and integration tests."
- "This ensures code quality before deployment and meets the DevOps & CI requirement."

**What to Show:**
- GitHub Actions workflow page
- At least 2 automated checks running (linting, tests)
- Explain branching strategy if relevant

**Key Message:** ✅ **DevOps & CI (5 points)** - Automated quality checks, proper version control

---

### **Step 2: Real-time Data Flow Demonstration** (3 minutes)

**Action:**
1. Show real-time data source (current state in Snowflake)
2. Run producer in dedicated CLI window
3. Run consumer in adjacent CLI window
4. Verify data landing → Show exact data in Snowflake with timestamps
5. Cleanup → Execute `docker-compose down` on Kafka containers

**Talking Points:**

**Before Starting:**
- "Now I'll demonstrate our real-time streaming pipeline using Kafka. This processes synthetic ticket sales events that simulate live concert ticket purchases."

**During Producer:**
- "The producer generates ticket sales events with fields like artist name, venue, tickets sold, revenue, and timestamp."
- "Events are published to Kafka at a rate of 100+ events per minute, simulating real-world streaming data."

**During Consumer:**
- "The consumer subscribes to the Kafka topic and processes messages in real-time."
- "It writes data to PostgreSQL staging tables, which serves as our OLTP staging layer."
- "This architecture allows us to handle high-throughput streaming data with low latency."

**Data Verification:**
- "Let me verify the data landed successfully in Snowflake."
- [Show Snowflake query] "Here we can see the exact records that were just ingested, with timestamps showing they arrived within the last few minutes."
- "The data flows: Kafka → PostgreSQL → Snowflake FAN_RAW schema, meeting our requirement for data to land in the raw layer."

**Key Messages:**
- ✅ **Real-time/Streaming Pipeline (15 points)** - Kafka implementation with <5 min latency
- ✅ **Data Landing** - Successfully lands in raw layer (Snowflake FAN_RAW)
- ✅ **Live Demo** - New data ingested during presentation

**Technical Details to Mention:**
- Kafka topic: `ticket-sales`
- PostgreSQL staging schema: `staging.ticket_sales`
- Snowflake raw schema: `FAN_RAW.raw_tickets`
- Latency: < 5 minutes from event generation to Snowflake

---

### **Step 3: CI/CD Results Review** (1 minute)

**Action:**
- Return to CI page
- Present all criteria and results

**Talking Points:**
- "Let me check back on our CI/CD pipeline results."
- "All checks passed successfully, demonstrating our automated testing and quality assurance."
- "This ensures our codebase maintains high quality standards."

**Key Message:** ✅ **DevOps & CI requirement met** - GitHub Actions with 2+ automated checks

---

## 🎯 Phase 2: Batch Processing & ML Pipeline (5 minutes)

### **Step 1: Airflow Setup** (2 minutes)

**Action:**
- Run `docker-compose up` for Airflow (or show already running)
- While waiting, present dbt structure and criteria

**Talking Points:**

**Airflow Introduction:**
- "Now I'll demonstrate our batch processing pipeline orchestrated by Airflow."
- "Airflow manages our entire data pipeline with multiple DAGs, each containing 3+ tasks."
- "This meets the orchestration requirement for pipelines with at least 3 tasks."

**Show Airflow UI:**
- "Here's our Airflow dashboard showing two main DAGs:"
  - **Batch Pipeline DAG**: CSV ingestion → dbt transformations
  - **Streaming Pipeline DAG**: Kafka validation → PostgreSQL sync → dbt transformations

**dbt Structure Overview:**
- "Our dbt project uses a three-layer architecture:"
  - **Staging Layer**: Cleans and standardizes raw data (views for freshness)
  - **Intermediate Layer**: Applies business logic and deduplication (tables for performance)
  - **Marts Layer**: Final analytics tables (fact and dimension tables)

**Key Messages:**
- ✅ **Pipeline Orchestration** - Airflow with 3+ tasks per DAG
- ✅ **Data Modeling Approach** - Dimensional data modeling (star schema)

---

### **Step 2: Data Processing** (2 minutes)

**Action:**
- Execute Airflow trigger (batch pipeline DAG)
- While waiting, present data modeling documentation
- Explain chosen modeling technique and rationale
- Show Airflow job completion and results

**Talking Points:**

**Triggering Batch Pipeline:**
- "I'll trigger our batch pipeline DAG, which orchestrates CSV ingestion and dbt transformations."
- "This DAG has 4 tasks: schema cleanup, CSV ingestion, dbt run, and dbt test."

**Data Modeling Explanation:**
- "We chose dimensional data modeling (star schema) because:"
  - "It's optimized for analytics queries"
  - "Clear separation between facts (events) and dimensions (artists, venues)"
  - "Industry best practice for data warehousing"
- "Our schema includes:"
  - **Fact Tables**: `fact_shows`, `fact_ticket_sales` (incremental)
  - **Dimension Tables**: `dim_artists`, `dim_venues`
  - **Marts**: `marts_artist_performance`, `marts_ticket_performance`, `marts_show_lifecycle`, `marts_daily_ticket_summary`

**Incremental Materialization (STAR FEATURE):**
- "One of our key achievements is the incremental materialization for `fact_ticket_sales`."
- "Since ticket sales stream in continuously, we can't rebuild the entire table every time."
- "Our incremental strategy:"
  - "First run: Processes all data"
  - "Subsequent runs: Queries max timestamp, processes only newer records"
  - "Uses merge strategy to handle updates and avoid duplicates"
- "Impact: Processing time reduced from minutes to seconds, compute costs reduced by 90%+"

**Show Airflow Results:**
- "The DAG completed successfully. All tasks passed:"
  - ✅ Schema cleanup
  - ✅ CSV ingestion to Snowflake
  - ✅ dbt run (21 models transformed)
  - ✅ dbt test (all tests passed)

**Key Messages:**
- ✅ **Batch Data Source** - CSV files ingested successfully
- ✅ **Data Modeling** - Dimensional modeling approach
- ✅ **Incremental Materialization** - Correctly implemented, no duplication
- ✅ **dbt Tests** - Proper testing via dbt test
- ✅ **Live Demo** - dbt executed successfully via orchestrator

**Technical Details:**
- Batch source: `shows_history.csv`, `shows_future.csv`
- dbt models: 21 models across 3 layers
- Incremental model: `fact_ticket_sales` with merge strategy
- Test coverage: 3+ tests per model layer

---

### **Step 3: Machine Learning (Optional - Skip if not implemented)** (1 minute)

**If you have ML components:**
- Execute ML model job
- Present results and explain business value

**If you don't have ML components:**
- Use this time to emphasize data quality and transformation results
- Highlight the comprehensive testing framework

**Talking Points (if no ML):**
- "While we don't have ML components, our data transformation pipeline enables predictive analytics."
- "The clean, structured data in our marts layer is ready for ML model training."
- "Our data quality framework ensures reliable inputs for any future ML initiatives."

---

## 🎯 Phase 3: AI Agent & RAG System (10 minutes)

### **Step 1: Document Processing** (2 minutes)

**Action:**
- Display PDF file content
- Explain chunking strategy
- Execute chunking and embedding process

**Talking Points:**

**Document Overview:**
- "Our RAG system processes PDF documents containing music industry knowledge."
- "We have 3 documents: concert industry reports, venue information, and artist performance guides."

**Chunking Strategy:**
- "We use semantic chunking to preserve context."
- "Chunks are sized appropriately to maintain meaning while fitting within embedding model limits."
- "Each chunk is embedded and stored in Pinecone vector database."

**Processing Execution:**
- "Let me process these documents now."
- [Show processing] "Documents are being chunked, embedded, and indexed in Pinecone."
- "This creates a searchable knowledge base for our AI agent."

**Key Message:** ✅ **Core RAG System** - Document processing implemented

---

### **Step 2: Question Preparation** (2 minutes)

**Action:**
While processing, prepare demonstration questions:
- Batch data queries on Snowflake
- Real-time data queries (show data landed 10 minutes ago)
- PDF content questions
- Combined/complex queries

**Talking Points:**

**Preparing Questions:**
- "While documents process, let me prepare demonstration questions that showcase our AI agent's capabilities."
- "I'll ask questions covering:"
  1. **Batch Data**: "What are the top 5 artists by total revenue?"
  2. **Real-time Data**: "Show me ticket sales from the last hour"
  3. **PDF Content**: "What are best practices for concert promotion?"
  4. **Combined Query**: "Based on the concert industry report, which artists have the highest demand based on recent ticket sales?"

**Why These Questions:**
- "These demonstrate the agent's ability to query both warehouse data and document knowledge."
- "The combined query shows advanced reasoning that integrates multiple sources."

---

### **Step 3: AI Agent Demonstration** (4 minutes)

**Action:**
- Initialize AI Agent after PDF processing completes
- **Batch Data Query**: Ask question → Compare with Snowflake results
- **Real-time Data Query**: Ask question → Compare with recent Snowflake data
- **PDF Content Query**: Ask question → Compare with PDF content
- **Combined Query**: Demonstrate complex multi-source question

**Talking Points:**

**Agent Introduction:**
- "Our AI agent is built with LangGraph and uses RAG to answer questions about both data warehouse content and document knowledge."
- "It has conversation memory, so it can maintain context across multiple questions."

**Demo 1: Batch Data Query**
- **Question**: "What are the top 5 artists by total revenue from historical shows?"
- **Show Agent Response**: [Agent provides answer]
- **Verify**: "Let me verify this against Snowflake." [Run SQL query]
- **Result**: "The agent correctly queried our `marts_artist_performance` table and provided accurate results."
- ✅ **Demonstrates**: Understanding of batch-loaded data source

**Demo 2: Real-time Data Query**
- **Question**: "Show me ticket sales from the last hour for Taylor Swift shows."
- **Show Agent Response**: [Agent provides answer with recent data]
- **Verify**: "Let me check Snowflake for recent records." [Show timestamp query]
- **Result**: "The agent correctly identified and queried real-time ticket sales data that landed just minutes ago."
- ✅ **Demonstrates**: Understanding of real-time data source

**Demo 3: PDF Content Query**
- **Question**: "What are best practices for concert promotion according to the industry reports?"
- **Show Agent Response**: [Agent provides answer from PDF]
- **Verify**: "This information comes from our processed PDF documents." [Show relevant chunk]
- **Result**: "The agent successfully retrieved and synthesized information from our document knowledge base."
- ✅ **Demonstrates**: Successful document querying

**Demo 4: Combined Query (ADVANCED)**
- **Question**: "Based on the concert industry report, which artists have the highest demand based on recent ticket sales?"
- **Show Agent Response**: [Agent combines PDF knowledge with warehouse data]
- **Explain**: "This query required the agent to:"
  - "Understand the concept of 'demand' from the PDF"
  - "Query recent ticket sales data"
  - "Synthesize both sources to provide an answer"
- ✅ **Demonstrates**: Combining PDF knowledge with warehouse data

**Key Messages:**
- ✅ **Core RAG System (10 points)** - Functional chatbot with conversation memory, document querying
- ✅ **Data Integration & Querying (10 points)** - Answers questions about batch data, real-time data, and combines PDF knowledge

**Technical Highlights:**
- LangGraph for agent orchestration
- Pinecone for vector storage
- Hybrid search with reranking (advanced feature)
- Conversation memory for context retention

---

### **Step 4: Complex Queries** (2 minutes)

**Action:**
- Demonstrate additional complex queries if time permits
- Show agent's reasoning capabilities

**Talking Points:**
- "Let me show one more complex query that demonstrates the agent's reasoning."
- **Question**: "Compare ticket sales velocity between artists in different genres."
- "This requires the agent to join multiple tables and apply business logic."
- "The agent successfully navigates our dimensional model to provide insights."

---

## 🎯 Phase 4: Advanced Features & Q&A (10 minutes)

### **Extra Features Demonstration** (5 minutes)

**Feature 1: Advanced RAG - Hybrid Search with Reranking** (2.5 minutes)

**Talking Points:**
- "One advanced feature I implemented is hybrid search with reranking in our RAG system."
- "This goes beyond basic RAG by combining multiple search techniques:"
  - **Dense Vector Search**: Semantic understanding using embeddings
  - **Sparse Vector Search**: Keyword-based matching (BM25-style)
  - **Reranking**: Uses Pinecone's reranking model to improve result relevance
- "Why this matters:"
  - "Hybrid search combines semantic understanding with exact keyword matching"
  - "Reranking improves relevance by re-scoring results based on query intent"
  - "This provides more accurate document retrieval than standard vector search"
- "Implementation details:"
  - "Uses Pinecone's inference API for sparse vector generation"
  - "Implements graceful degradation: if sparse vectors fail, falls back to dense-only"
  - "Reranking model: `pinecone-rerank-v0`"
- "Business value:"
  - "More accurate answers from the AI agent"
  - "Better user experience with relevant document retrieval"
  - "Production-ready with error handling"

**Show Code/Demo:**
- [Show retriever.py code] "Here's the hybrid search implementation."
- "The system automatically chooses the best search method based on query type."

**Key Message:** 🌟 **Advanced RAG Features** - Hybrid search + reranking (15-20 points potential)

---

**Feature 2: Custom dbt Macros & Advanced Incremental Loading** (2.5 minutes)

**Talking Points:**
- "Another advanced feature is our custom dbt macros and sophisticated incremental loading strategy."
- "Custom Macros:"
  - **`calculate_sales_velocity`**: Reusable business logic for sales rate calculations
  - **`generate_ticket_sales_key`**: Consistent key generation across models
  - "These macros ensure consistency and reduce code duplication"
- "Advanced Incremental Loading:"
  - "Not just basic incremental - we use merge strategy with deduplication"
  - "Handles late-arriving data using window functions"
  - "Prevents duplicates even when the same event arrives multiple times"
  - "Efficient timestamp-based filtering with proper edge case handling"
- "Implementation highlights:"
  - "Merge strategy: `WHEN MATCHED THEN UPDATE, WHEN NOT MATCHED THEN INSERT`"
  - "Deduplication: `ROW_NUMBER() OVER (PARTITION BY key ORDER BY timestamp DESC)`"
  - "First-run detection: `is_incremental()` macro handles initial load"
- "Impact:"
  - "90%+ cost reduction vs full refresh"
  - "Processing time: minutes → seconds"
  - "Handles 100+ events/minute efficiently"
  - "Production-ready with proper error handling"

**Show Code/Demo:**
- [Show fact_ticket_sales.sql] "Here's the incremental model with merge strategy."
- [Show macros] "These custom macros are reused across multiple models."

**Key Message:** 🌟 **Advanced Data Modeling** - Custom macros + sophisticated incremental loading (15-20 points potential)

---

**Additional Advanced Features to Mention (if time):**

**Data Quality Validation Framework:**
- "We have a comprehensive data validation framework that runs automated checks."
- "Validates data integrity, completeness, and quality metrics."
- "Integrated into our pipeline for continuous monitoring."

**Error Handling & Retry Logic:**
- "Our Kafka producer and consumer implement retry logic with exponential backoff."
- "API requests include retry mechanisms for rate limiting."
- "Graceful degradation in RAG system if advanced features fail."

**Key Messages:**
- 🌟 **Advanced Features** - Multiple sophisticated implementations
- 🌟 **Production-Ready** - Error handling, monitoring, scalability
- 🌟 **Business Value** - Real-world practicality and impact

---

### **Q&A Session** (5 minutes)

**Prepare for Common Questions:**

**Q: "What was your biggest challenge?"**
- "Handling late-arriving data in the streaming pipeline. Solved with deduplication logic using window functions."

**Q: "How does your system scale?"**
- "Incremental loading scales efficiently. Kafka handles high throughput. Snowflake micro-partitioning for performance."

**Q: "Why did you choose dimensional modeling?"**
- "Optimized for analytics queries, clear separation of concerns, industry best practice, enables fast aggregations."

**Q: "How do you ensure data quality?"**
- "Comprehensive dbt tests at every layer, automated validation framework, data quality checks in pipeline."

**Q: "What makes your RAG system advanced?"**
- "Hybrid search combines semantic and keyword matching. Reranking improves relevance. Graceful degradation for reliability."

**Q: "What's the business value?"**
- "Real-time ticket sales monitoring, artist performance analytics, operational insights for promoters and venues."

---

## 📊 Summary Checklist

### ✅ Core Functionality (60 points)

**A. Data Ingestion & Pipeline Orchestration (15 points)**
- ✅ Batch data source (CSV files)
- ✅ Real-time/streaming pipeline (Kafka, <5 min latency)
- ✅ Airflow orchestration (3+ tasks per DAG)
- ✅ Data lands in raw layer (Snowflake FAN_RAW)
- ✅ Live demo: New data ingested during presentation

**B. Data Modeling & Transformation (15 points)**
- ✅ Proper data modeling (Dimensional/Star Schema)
- ✅ Incremental materialization (correctly implemented, no duplication)
- ✅ dbt tests (proper testing via dbt test)
- ✅ Live demo: dbt executed via orchestrator

**C. DevOps & CI (5 points)**
- ✅ GitHub Actions (2+ automated checks)
- ✅ Version control practices (branching, PR reviews)
- ✅ Live demo: CI/CD pipeline execution

**D. Documentation (5 points)**
- ✅ Comprehensive README.md
- ✅ Architecture diagram

**2. AI Agent Implementation (20 points)**

**A. Core RAG System (10 points)**
- ✅ Functional chatbot with conversation memory
- ✅ Live demo: Coherent conversation with context retention
- ✅ Basic RAG for PDF/document processing
- ✅ Live demo: Successful document querying

**B. Data Integration & Querying (10 points)**
- ✅ Live demo: Answers questions about batch data
- ✅ Live demo: Answers questions about real-time data
- ✅ Live demo: Combines PDF knowledge with warehouse data

### 🌟 Extra Features (40 points potential)

**Feature 1: Advanced RAG - Hybrid Search with Reranking**
- ✅ Hybrid search (dense + sparse vectors)
- ✅ Reranking for improved relevance
- ✅ Graceful degradation
- ✅ Production-ready implementation

**Feature 2: Custom dbt Macros & Advanced Incremental Loading**
- ✅ Custom dbt macros (reusable business logic)
- ✅ Advanced incremental loading (merge strategy, deduplication)
- ✅ Efficient processing (90%+ cost reduction)
- ✅ Production-ready with error handling

**Additional Features:**
- ✅ Data quality validation framework
- ✅ Error handling & retry logic
- ✅ Comprehensive testing

---

## 🎯 Key Messages to Emphasize

1. ✅ **Production-Ready**: Not just a demo - handles real-time data at scale
2. ✅ **Best Practices**: Three-layer architecture, comprehensive testing, proper error handling
3. ✅ **Performance**: Incremental loading reduces costs by 90%+ and processing time significantly
4. ✅ **Business Value**: Enables real-time insights and data-driven decisions
5. ✅ **Innovation**: Advanced RAG features and sophisticated data modeling techniques
6. ✅ **Maintainable**: Clear structure, documentation, reusable components

---

## ⏰ Time Management Tips

- **Stick to the timeline** - 30 minutes goes quickly
- **Have backup plans** - Screenshots/videos ready if live demo fails
- **Practice transitions** - Smooth flow between phases
- **Prepare questions** - Know what you'll ask the AI agent
- **Test everything** - Verify all components work before presentation

---

## 🚨 Backup Strategies

**If Kafka fails:**
- Show screenshots of working pipeline
- Explain architecture and data flow
- Demonstrate data already in Snowflake

**If Airflow fails:**
- Show DAG code and explain structure
- Demonstrate manual dbt execution
- Show previous successful runs

**If AI Agent fails:**
- Show code and explain implementation
- Demonstrate document processing separately
- Show example queries and responses

---

**Good luck with your presentation! 🚀**
