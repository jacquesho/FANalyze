# FANalyze 2.0 - Presentation Quick Reference Card 🎯

## ⏰ 30-Minute Timeline

| Phase | Time | Focus |
|-------|------|-------|
| **Phase 1** | 5 min | Real-time Pipeline |
| **Phase 2** | 5 min | Batch & ML Pipeline |
| **Phase 3** | 10 min | AI Agent & RAG |
| **Phase 4** | 10 min | Advanced Features & Q&A |

---

## 🎯 Phase 1: Real-time Pipeline (5 min)

### ✅ Checklist
- [ ] Start CI/CD pipeline (GitHub Actions)
- [ ] Show 2+ automated checks running
- [ ] Run Kafka producer (CLI window 1)
- [ ] Run Kafka consumer (CLI window 2)
- [ ] Verify data in Snowflake (show timestamps)
- [ ] Check CI/CD results
- [ ] Cleanup: `docker-compose down` Kafka

### 🎤 Key Talking Points
- "Real-time streaming pipeline using Kafka"
- "100+ events/minute, <5 min latency"
- "Data flows: Kafka → PostgreSQL → Snowflake FAN_RAW"
- "Meets requirement: data lands in raw layer"

### 📊 Points Covered
- ✅ Real-time/streaming pipeline (15 pts)
- ✅ DevOps & CI (5 pts)

---

## 🎯 Phase 2: Batch Pipeline (5 min)

### ✅ Checklist
- [ ] Show Airflow UI (2 DAGs visible)
- [ ] Explain dbt three-layer architecture
- [ ] Trigger batch pipeline DAG
- [ ] Explain dimensional modeling
- [ ] Highlight incremental materialization (STAR FEATURE)
- [ ] Show DAG completion (all tasks passed)
- [ ] Show dbt test results

### 🎤 Key Talking Points
- "Airflow orchestrates pipeline with 3+ tasks per DAG"
- "Three-layer dbt architecture: staging → intermediate → marts"
- "Dimensional modeling: fact tables + dimension tables"
- "Incremental loading: 90%+ cost reduction, minutes → seconds"

### 📊 Points Covered
- ✅ Batch data source (15 pts)
- ✅ Data modeling & transformation (15 pts)
- ✅ Pipeline orchestration (15 pts)

---

## 🎯 Phase 3: AI Agent & RAG (10 min)

### ✅ Checklist
- [ ] Show PDF documents
- [ ] Explain chunking strategy
- [ ] Process documents (chunking + embedding)
- [ ] Prepare 4 demo questions:
  1. Batch data query
  2. Real-time data query
  3. PDF content query
  4. Combined query
- [ ] Initialize AI agent
- [ ] Demo each question type
- [ ] Verify answers against Snowflake/PDFs

### 🎤 Key Talking Points
- "LangGraph agent with RAG capabilities"
- "Hybrid search: semantic + keyword matching"
- "Conversation memory for context retention"
- "Combines warehouse data + document knowledge"

### 📊 Points Covered
- ✅ Core RAG System (10 pts)
- ✅ Data Integration & Querying (10 pts)

---

## 🎯 Phase 4: Advanced Features (10 min)

### ✅ Feature 1: Hybrid Search with Reranking (2.5 min)
**Talking Points:**
- Combines dense (semantic) + sparse (keyword) vectors
- Reranking improves relevance
- Graceful degradation if features fail
- Production-ready implementation

### ✅ Feature 2: Custom dbt Macros & Advanced Incremental (2.5 min)
**Talking Points:**
- Custom macros: `calculate_sales_velocity`, `generate_ticket_sales_key`
- Advanced incremental: merge strategy + deduplication
- Handles late-arriving data
- 90%+ cost reduction

### ✅ Q&A Prep (5 min)
**Common Questions:**
- Biggest challenge? → Late-arriving data → Solved with deduplication
- How does it scale? → Incremental loading, Kafka throughput, Snowflake partitioning
- Why dimensional modeling? → Analytics optimization, best practice
- Data quality? → Comprehensive dbt tests, validation framework
- Business value? → Real-time monitoring, performance analytics, operational insights

---

## 📊 Core Requirements Checklist (60 points)

### Data Ingestion & Orchestration (15 pts)
- ✅ Batch source (CSV)
- ✅ Real-time pipeline (Kafka, <5 min)
- ✅ Airflow (3+ tasks)
- ✅ Data in raw layer
- ✅ Live demo

### Data Modeling (15 pts)
- ✅ Dimensional modeling
- ✅ Incremental materialization
- ✅ dbt tests
- ✅ Live demo via orchestrator

### DevOps & CI (5 pts)
- ✅ GitHub Actions (2+ checks)
- ✅ Version control
- ✅ Live demo

### Documentation (5 pts)
- ✅ README.md
- ✅ Architecture diagram

### AI Agent (20 pts)
- ✅ RAG system (10 pts)
- ✅ Data integration (10 pts)

---

## 🌟 Bonus Features (40 points potential)

1. **Hybrid Search + Reranking** (15-20 pts)
   - Dense + sparse vectors
   - Reranking model
   - Graceful degradation

2. **Custom Macros + Advanced Incremental** (15-20 pts)
   - Reusable business logic
   - Merge strategy
   - Deduplication
   - 90%+ cost reduction

---

## 🎤 Elevator Pitch (30 seconds)

> "FANalyze 2.0 is an end-to-end data engineering and AI analytics platform for music industry insights. We process real-time ticket sales via Kafka, batch historical concert data, transform it using dbt with incremental loading that reduces costs by 90%+, and enable natural language queries through an AI agent with advanced RAG capabilities including hybrid search and reranking."

---

## 🚨 Backup Plans

**Kafka fails:**
- Show screenshots
- Explain architecture
- Show data in Snowflake

**Airflow fails:**
- Show DAG code
- Manual dbt run
- Previous successful runs

**AI Agent fails:**
- Show code
- Separate document processing demo
- Example queries/responses

---

## ⏰ Time Management

- **Stick to timeline** - 30 min goes fast!
- **Practice transitions** - Smooth flow
- **Have questions ready** - Pre-written agent queries
- **Test everything** - Verify before presentation

---

## 💡 Key Stats to Mention

- **21 dbt models** across 3 layers
- **2 data sources** (batch + streaming)
- **90%+ cost reduction** from incremental loading
- **100+ events/minute** processing capacity
- **Minutes → Seconds** processing time improvement
- **Hybrid search** with reranking (advanced RAG)
- **Custom macros** for reusable logic

---

**🎯 Remember: Focus on demonstrating working system + explaining business value!**
