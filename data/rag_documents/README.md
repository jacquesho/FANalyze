# RAG Test Documents

This directory contains test documents for the RAG (Retrieval-Augmented Generation) system.

## Documents

1. **ticket_sales_strategies.txt** - Contains intentionally fake ticket sales strategies:
   - Reverse Psychology Pricing Manual
   - Midnight Ticket Release Protocol
   - Dynamic Pricing for Sentient Venues

2. **musician_histories.txt** - Contains intentionally fake musician biographies for:
   - Metallica
   - Taylor Swift
   - The Weeknd
   - Coldplay
   - Beyoncé
   - Bruno Mars
   - Ed Sheeran

## Usage

These documents are designed to test RAG retrieval - they contain obviously fake information that makes it easy to tell when the RAG system is using these documents vs. real-world knowledge.

### Testing with Text Files

The document processor supports `.txt` files directly:

```bash
python rag/document_processing/test_processor.py data/rag_documents/ticket_sales_strategies.txt
python rag/document_processing/test_processor.py data/rag_documents/musician_histories.txt
```

### Converting to PDF (Optional)

If you prefer PDF format, you can convert these files using:

**Using pandoc:**
```bash
pandoc ticket_sales_strategies.txt -o ticket_sales_strategies.pdf
pandoc musician_histories.txt -o musician_histories.pdf
```

**Using online tools:**
- Upload to Google Docs → Export as PDF
- Use online Markdown/Text to PDF converters

**Using Python (if you have reportlab installed):**
```python
# Simple conversion script
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def txt_to_pdf(txt_file, pdf_file):
    with open(txt_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    c = canvas.Canvas(pdf_file, pagesize=letter)
    y = 750
    for line in text.split('\n'):
        if y < 50:
            c.showPage()
            y = 750
        c.drawString(50, y, line)
        y -= 15
    c.save()
```

## Testing RAG Queries

Once processed, you can test RAG queries like:

- "What was Metallica's original genre?" (Should return: jazz fusion)
- "What time are tickets released?" (Should return: 3:33 AM on Friday the 13th)
- "What was Taylor Swift's first band?" (Should return: Swift Destruction, death metal)
- "How does weather affect ticket pricing?" (Should return: rain discounts for indoor shows)

These queries will help verify that the RAG system is correctly retrieving information from these documents.



