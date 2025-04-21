
# Capstone Project Proposal

## Student Information*
Name: Jacques Ho  
Email: jacquesho@gmail.com

## Project Overview*
Project Title (give it an awesome one): FANalyze – Your AI Hype Assistant for Live Rock & Metal Shows
Domain Area: Music / Event Intelligence / AI
One-Line Description: An AI-powered assistant that helps rock and metal fans discover the most buzzworthy concerts by combining real-time fan sentiment, historical show data, and document-based reviews.

## Technical Components*

### Data Sources*
1. Real-time Source:
   - Description: Reddit fan discussions and sentiment posts from subreddits like r/metal, r/rock, r/concerts
   - Update frequency: Near real-time (every 5–15 minutes)
   - Estimated volume: 10–50 posts/day filtered by band/genre
   - Access method (API/webhook/etc): Reddit API via PRAW or Pushshift (simulated via polling or Kafka stream)

2. Batch Source:
   - Description: Songkick API (upcoming shows) and simulated ticket sales data (CSV)
   - Update frequency: Songkick - daily/hourly; Ticket data - static or weekly updates
   - Estimated volume: 100–500 show records, 1K+ ticket rows
   - Data format: JSON (API), CSV (ticket data)

3. Document Processing:
   - File type(s): PDF (concert reviews, show recaps)
   - Processing needs: Extract and chunk review text; store as vector embeddings with metadata
   - Expected volume: 3–5 reviews to start (expandable)

### Data Model
Fact Tables:
- fact_show_performance
- fact_ticket_sales
- fact_fan_buzz

Dimension Tables:
- dim_artist
- dim_venue
- dim_date
- (Optional) dim_album

### AI Component
Query Types:
- "Is the upcoming Gojira show worth seeing?"
- "Which concerts in Ho Chi Minh City have the highest fan buzz this month?"
- "How does Sleep Token’s current setlist compare to their last tour?"
- "What are fans saying about Megadeth’s performance at [Venue] last week?"

Document Processing Approach:
- Extract text from PDF reviews using PyMuPDF
- Chunk reviews by paragraph or section
- Generate embeddings for each chunk using OpenAI or Sentence-Transformers
- Store in vector DB (Chroma or FAISS)  << We haven't covered vector DB in class, cái này hợp không?

RAG Implementation Plan:
- User inputs question to chatbot interface (e.g., Streamlit)
- Query is used to search vector DB for semantically similar document chunks
- Top-k chunks + structured warehouse data passed to LLM
- Response is generated based on retrieved context + data

### Extra Features (Optional)
Planned additional features:
- Simple chatbot UI (Streamlit or Gradio)
- Hype score dashboard with visual rankings
- Genre filter & artist comparisons
- PDF citation reference in chatbot answers

## Implementation Timeline*
Module 1:
- Finalize schema and data model (fact_show_performance, dim_artist, etc.)
- Simulate ticket sales data in CSV format
- Ingest upcoming shows from Songkick API
- Ingest historical setlists from Setlist.fm API
- Set up Airflow DAGs to orchestrate batch ingestion
- Add transformation logic and error handling
- ** Cold Call - use batch data first, once that's working, move on to API.
  (API not required to pass module 1 test)
  ** 1 fact table, 

Month 3 - AI Ops, scope it down to 1 question for each criteria
1. Does chatbot connects to batch data?  1 question to showcase
2. Realtime data - data needs to land within 5 minutes, chatbot needs to answer from that data/row
3. Uploading PDF works

Module 2:
- Simulate Reddit stream using PRAW or Pushshift (or Kafka stream)
- Ingest Reddit data and push into staging tables
- Build dbt models to calculate buzz_score and hype_score
- Set up dbt tests (nulls, FK checks, value ranges)
- Configure CI/CD to automate dbt workflows and schema versioning

Module 3:
- Collect and preprocess 2–3 PDF concert reviews
- Extract and chunk review text for embeddings
- Store embeddings in vector database (Chroma/FAISS)
- Build chatbot prototype to handle fan queries using retrieved content
- Handle queries related to artist comparisons, setlists, and fan reviews

Module 4:
- Connect all pipelines: batch, stream, and RAG
- Build frontend UI using Streamlit or Gradio
- Add charts and visual dashboards (e.g., top shows, fan buzz graphs)
- Optimize system performance (RAG latency, data loads)
- Finalize README, documentation, and prepare demo video or live walk-through

## Technical Considerations
Known Challenges:
- Aligning data across inconsistent sources (e.g., artist names, show IDs)
- Parsing Reddit posts cleanly (removing noise, sarcasm)
- Processing and embedding PDFs accurately
- Building a smooth, low-latency RAG pipeline

Support Needed:
- API setup for Reddit and Songkick
- Guidance on document embedding best practices
- Help connecting Airflow, dbt, and vector DB into one workflow

Required Resources:
- Songkick and Reddit API keys
- PDF parser (e.g., PyMuPDF)
- Chroma/FAISS for vector storage
- OpenAI API or HuggingFace for embedding model
- Airflow + dbt setup environment

## Additional Notes
- This project is designed to evolve with the AI Engineering curriculum — each major capstone requirement aligns with what is being taught in the corresponding module.
- Content is themed around a personal passion (rock/metal concerts) to increase engagement and follow-through.
- Dataset sizes are kept manageable but realistic, with room for future growth post-course.
