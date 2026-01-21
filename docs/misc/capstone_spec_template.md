![Foundry AI Academy Logo](https://raw.githubusercontent.com/foundry-ai-academy/fa-cdn/1.0.0/images/FoundryAI_academy_logo_on_yellow_space.png)
---

# Capstone Project Specification Template 🎯

**Complete this template for your M01 W04 submission. Update weekly as your project evolves.**

---

## 🚨 M01 W04 SUBMISSION CHECKLIST

### ⚠️ Deadline: Module 1, Week 4
**Submit this completed template + working repository**

### 📋 What You Must Deliver

**1. Repository Setup**
- ✅ Valid GitHub 🌟 repository with proper structure
- ✅ Add trainers as collaborators (Github): `il-dat`, `il-minh`, `nhatil`, `thu-IL`
- ✅ Repository permissions allow trainer read/write access
- [ ] At least 2 branches, 1 merged PR, 3+ meaningful commits

**2. Working Mini Pipeline**
- [ ] **Real-time pipeline**: API → PostgreSQL 🌟 (row-by-row data collection)
- [ ] **Batch pipeline**: Local files → Snowflake 🌟 (500+ rows bulk loading)
- [ ] **Two different data sources**: One for real-time, one for batch (see data sources guide)
- [ ] Both pipelines run independently and successfully (you should check it yourself, trainer won't be able to execute your code)
- [ ] Data lands correctly in both databases

**3. Required Files**
- [ ] `README.md` - Project overview (see `PROJECT SPECIFICATION TEMPLATE` below 👇) and setup instructions
- [ ] `docs/execution_plan.md` - Step-by-step implementation plan - see `IMPLEMENTATION PLAN TEMPLATE` below 👇
- [ ] `pyproject.toml` + `uv.lock` - Dependency management
- [ ] `.env.example` - Environment variables template
- [ ] `.gitignore` - Python/DE specific ignores

---

## 📝 PROJECT SPECIFICATION TEMPLATE

### Project Overview
- **Working title**:
- **One-sentence summary**:
- **Business/value objective**:
- **Success metrics** (quantitative):

### Problem & Scope
- **Problem statement and constraints**:
- **Personas/stakeholders and primary use cases**:
- **In/out of scope**:

### Data Sources
- **Real-time source**: [API name, endpoint, data format, update frequency] - feeds into real-time pipeline
- **Batch source**: [Dataset name, format, volume, update cadence] - feeds into batch pipeline
- **Why 2 different sources**: [Brief explanation of why you need both real-time and batch data]

### Architecture Overview
- **High-level diagram**: [Link or describe your system flow]
- **Data flow**: [How data moves from sources → databases]
- **Technology choices**: [Justify your tech stack decisions]

---

## 🏗️ IMPLEMENTATION PLAN TEMPLATE

### M01 W04: Foundation (Current Focus)
**Goal**: Working mini pipeline with both batch and real-time processing

**Real-time Pipeline:**
- Source: [Your chosen real-time API] - must be different from batch source
- Process: Row-by-row data collection
- Destination: PostgreSQL (via Docker)
- Script: `ingestion/collect_realtime.py` + `ingestion/load_to_postgres.py`

**Batch Pipeline:**
- Source: [Your chosen batch dataset] - must be different from real-time source
- Process: Bulk data collection (500+ rows)
- Destination: Snowflake 🌟
- Script: `ingestion/collect_batch.py` + `ingestion/load_to_snowflake.py`

**Important**: You need 2 different data sources - one for each pipeline type!

### M02 W04: Data Processing (Future Planning)
- dbt transformations and data modeling
- Data quality testing and validation
- Warehouse structure optimization

### M03 W04: Real-time & Orchestration (Future Planning)
- Kafka 🌟 streaming implementation
- Airflow 🌟 pipeline orchestration
- End-to-end data flow automation

### M04 W04: AI Agent (Future Planning)
- LangGraph 🌟 agent development
- RAG system with document processing
- Natural language data querying

### M05 W04: Final Integration (Future Planning)
- System testing and validation
- Performance optimization
- Demo preparation and documentation

>[!NOTE]
> **Future Technologies**: The technologies mentioned above (Kafka, Airflow, dbt, LangGraph) will be taught in their respective modules. For M01 W04, focus only on basic data collection and loading.

---

## 🛠️ TECHNOLOGY STACK

### Core Technologies (M01 W04 Focus)
- **Data Collection**: Python 🌟 (requests, polars)
- **Real-time Processing**: Direct API → PostgreSQL 🌟
- **Batch Processing**: Local files → Snowflake 🌟
- **Database**: PostgreSQL (Docker) + Snowflake 🌟

### Future Technologies (Planning Only)
- **Orchestration**: Kafka 🌟, Airflow 🌟 (M03)
- **Data Transformation**: dbt 🌟 (M02)
- **AI/ML**: LangGraph 🌟, RAG systems (M04)

### Development Tools
- **Package Management**: uv
- **Testing**: pytest, great-expectations
- **Version Control**: Git + GitHub 🌟
- **Containerization**: Docker

>[!NOTE]
> **🌟 Technology Flexibility**: Any technology marked with 🌟 can be replaced with alternatives. See [Technology Alternatives](./capstone_technology_alternatives.md) for approved options.

---

## 🚀 NEXT STEPS

### This Week (M01 W04)
1. **Complete this template** with your project details
2. **Set up repository** with required structure
3. **Implement mini pipeline** (real-time + batch)
4. **Test everything** works end-to-end
5. **Submit for review** by deadline

### Future Weeks
- Follow the implementation plan above
- Update this template weekly
- Document decisions and challenges
- Seek help when needed

---

## 📝 IMPORTANT NOTES

>[!NOTE]
> **Check-in Point, Not Assessment** 📋
>
> This is a check-in point - your trainer won't check if your code actually runs locally. Trainers only look at the overall project structure and progress. This serves as a reminder to start working on your Capstone now. There is no hard point requirement on submitting this. The end goal is always passing the final test.

>[!NOTE]
> **Technology Flexibility** 🛠️
>
> Some of the tools and design patterns mentioned here are optional. See [Technology Alternatives](./capstone_technology_alternatives.md) for approved alternatives to the suggested technology stack.

---

**Remember**: Focus on making it work first, then make it better! 🚀

---
© 2024 Foundry AI Academy.

All rights reserved.

This material is confidential and proprietary to FoundryAI Academy. It may not be reproduced, transmitted, or stored, in whole or in part, in any form or by any means without written permission from FoundryAI Academy.

![Foundry AI Academy Logo](https://raw.githubusercontent.com/foundry-ai-academy/fa-cdn/1.0.0/images/FoundryAI_academy_logo_symbol_yellow_space.png)
