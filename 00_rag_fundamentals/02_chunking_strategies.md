# 02 · Chunking Strategies

> **Chunking is the most underestimated step in building a good RAG system.**
> Poor chunking breaks retrieval even with perfect embeddings and a powerful LLM.

---

## Table of Contents

1. [Why Chunking Matters](#1-why-chunking-matters)
2. [The Chunking Tradeoff](#2-the-chunking-tradeoff)
3. [Strategy 1 — Fixed-Size Chunking](#3-strategy-1--fixed-size-chunking)
4. [Strategy 2 — Sentence-Based Chunking](#4-strategy-2--sentence-based-chunking)
5. [Strategy 3 — Paragraph-Based Chunking](#5-strategy-3--paragraph-based-chunking)
6. [Strategy 4 — Recursive Character Chunking](#6-strategy-4--recursive-character-chunking)
7. [Strategy 5 — Semantic Chunking](#7-strategy-5--semantic-chunking)
8. [Strategy 6 — Hierarchical / Parent-Child Chunking](#8-strategy-6--hierarchical--parent-child-chunking)
9. [Strategy 7 — Markdown / Structure-Aware Chunking](#9-strategy-7--markdown--structure-aware-chunking)
10. [Chunk Overlap Explained](#10-chunk-overlap-explained)
11. [How to Choose Chunk Size](#11-how-to-choose-chunk-size)
12. [Chunking Strategy Comparison](#12-chunking-strategy-comparison)

---

## 1. Why Chunking Matters

Documents are too large to embed as a whole — embedding a 100-page PDF as a single vector loses all granularity. But chunks that are too small lose context.

```
THE CHUNKING PROBLEM

Too Large (whole document as 1 chunk)
┌──────────────────────────────────────────────────────┐
│  Chapter 1... Chapter 2... Chapter 3... Chapter 4... │
│  Chapter 5... Chapter 6... Chapter 7...              │
└──────────────────────────────────────────────────────┘
  Query: "What is the return policy?"
  Vector: average of everything → diluted signal
  Result: POOR retrieval — everything looks equally relevant

Too Small (1 sentence per chunk)
┌────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│"Returns    │ │"within   │ │"30 days."│ │"Items    │
│ are allowed│ │ a period │ │          │ │ must be..│
└────────────┘ └──────────┘ └──────────┘ └──────────┘
  Query: "What is the return policy?"
  Result: FRAGMENTED — answer split across many chunks

Just Right (paragraph or semantic unit)
┌──────────────────────────────────────────────────────┐
│  "Returns are allowed within 30 days. Items must be  │
│   in original packaging with receipt. Digital goods  │
│   are non-refundable once activated."                │
└──────────────────────────────────────────────────────┘
  Query: "What is the return policy?"
  Result: PERFECT — complete answer in one chunk
```

---

## 2. The Chunking Tradeoff

```
CHUNK SIZE vs RETRIEVAL QUALITY

  Precision                             Context
  (narrow answer)                       (broad answer)
       ▲                                     ▲
       │                                     │
  High │  ●                             High │              ●
       │      ●                              │          ●
       │           ●                         │      ●
  Low  │                ●             Low   │  ●
       └─────────────────────               └──────────────────
         Small → Large (chunk size)           Small → Large

  Small chunks = High precision but low context
  Large chunks = Low precision but high context

SWEET SPOT: 256–1024 tokens depending on the document type
```

Key factors that determine the right chunk size:
- **Query type**: Short factual questions → smaller chunks; Analytical questions → larger chunks
- **Document type**: Legal/technical docs → larger; News articles → smaller
- **Embedding model**: Check its max input token limit (most cap at 512–8192 tokens)
- **LLM context window**: More context window → can handle more/larger chunks

---

## 3. Strategy 1 — Fixed-Size Chunking

The simplest and most common approach: split every N characters or tokens regardless of content structure.

```
FIXED-SIZE CHUNKING (chunk_size=300, overlap=50)

Original: "Photosynthesis is the process by which plants use sunlight,
water, and carbon dioxide to produce oxygen and energy in the form
of sugar. This process occurs in chloroplasts..."

Chunk 1:  "Photosynthesis is the process by which plants use
           sunlight, water, and carbon dioxide to produce oxygen
           and energy in the form of sugar. This process..."
           ◀────────────── 300 chars ──────────────▶

Chunk 2:  "...form of sugar. This process occurs in chloroplasts,
           specifically in the thylakoid membranes using..."
           ◀──50 overlap──▶◀──── 250 new chars ────▶

Chunk 3:  "...thylakoid membranes using chlorophyll to absorb light..."
```

**LangChain Implementation:**
```python
from langchain_text_splitters import CharacterTextSplitter

splitter = CharacterTextSplitter(
    chunk_size=500,       # characters per chunk
    chunk_overlap=50,     # overlap between chunks
    separator="\n"        # preferred split point
)

chunks = splitter.split_documents(documents)
```

| Pros | Cons |
|---|---|
| Simple and fast | Ignores sentence/paragraph boundaries |
| Predictable chunk count | Can cut mid-sentence |
| Good baseline | Loses semantic coherence |
| Works on any text | Not ideal for structured docs |

**Best for:** Quick prototyping, plain text, when simplicity matters

---

## 4. Strategy 2 — Sentence-Based Chunking

Split at sentence boundaries to preserve grammatical coherence.

```
SENTENCE-BASED CHUNKING

Original paragraph:
"Climate change refers to long-term shifts in temperatures.
Human activities are the main driver. Greenhouse gases trap
heat in the atmosphere. The primary gas is CO2."

Sentence chunks:
┌─────────────────────────────────────────────────────────┐
│ S1: "Climate change refers to long-term shifts in        │
│      temperatures."                                      │
├─────────────────────────────────────────────────────────┤
│ S2: "Human activities are the main driver."             │
├─────────────────────────────────────────────────────────┤
│ S3: "Greenhouse gases trap heat in the atmosphere."     │
├─────────────────────────────────────────────────────────┤
│ S4: "The primary gas is CO2."                           │
└─────────────────────────────────────────────────────────┘

With grouping (3 sentences per chunk):
┌───────────────────────────────────────────────────┐
│ "Climate change refers to long-term shifts in      │
│  temperatures. Human activities are the main       │
│  driver. Greenhouse gases trap heat..."            │
└───────────────────────────────────────────────────┘
```

**LangChain Implementation:**
```python
from langchain_text_splitters import NLTKTextSplitter, SpacyTextSplitter

# NLTK-based
splitter = NLTKTextSplitter(chunk_size=500)

# Spacy-based (more accurate sentence detection)
splitter = SpacyTextSplitter(chunk_size=500)

chunks = splitter.split_documents(documents)
```

| Pros | Cons |
|---|---|
| Preserves sentence integrity | Short chunks may lack context |
| Good for Q&A tasks | Requires NLTK/spaCy installation |
| Natural reading units | Slow for large corpora |

**Best for:** FAQ documents, news articles, conversational data

---

## 5. Strategy 3 — Paragraph-Based Chunking

Split on blank lines or double newlines — treating each paragraph as a natural semantic unit.

```
PARAGRAPH-BASED CHUNKING

Document:
┌────────────────────────────────────────────────────────┐
│ Introduction                                            │
│ The Industrial Revolution began in Britain around 1760. │
│ It marked a shift from agrarian economies to industrial.│
│                                                         │  ← split here
│ Key Innovations                                         │
│ Steam power transformed manufacturing and transport.    │
│ The spinning jenny and power loom automated textiles.   │
│                                                         │  ← split here
│ Social Impact                                           │
│ Urban populations grew rapidly as rural workers moved.  │
│ New social classes emerged: industrial capitalists and  │
│ the urban working class.                               │
└────────────────────────────────────────────────────────┘

Resulting chunks:
Chunk 1: "Introduction\nThe Industrial Revolution began..."
Chunk 2: "Key Innovations\nSteam power transformed..."
Chunk 3: "Social Impact\nUrban populations grew..."
```

**LangChain Implementation:**
```python
from langchain_text_splitters import CharacterTextSplitter

splitter = CharacterTextSplitter(
    separator="\n\n",     # split on blank lines
    chunk_size=1000,
    chunk_overlap=100
)

chunks = splitter.split_documents(documents)
```

| Pros | Cons |
|---|---|
| Preserves topical coherence | Paragraph length varies wildly |
| Headers stay with content | May create very large chunks |
| Works well on structured prose | Depends on author formatting |

**Best for:** Books, blog posts, articles, reports with consistent formatting

---

## 6. Strategy 4 — Recursive Character Chunking

The **recommended default** strategy. It tries multiple separators in priority order — splitting on paragraphs first, then sentences, then words, then characters.

```
RECURSIVE CHARACTER CHUNKING — Priority Order

Priority 1: "\n\n"  (double newline — paragraph break)
Priority 2: "\n"    (single newline — line break)
Priority 3: ". "    (sentence end)
Priority 4: " "     (word boundary)
Priority 5: ""      (character — last resort)

If chunk after splitting on Priority 1 is still too large,
recursively try Priority 2 on that piece, then 3, etc.

Example:
┌────────────────────────────────────────────────────────────┐
│ Document                                                    │
└────────────────────────────────────────────────────────────┘
          │
          ▼ Try "\n\n" split
┌─────────────────┐  ┌──────────────────────────────────────┐
│ Para 1 (small)  │  │ Para 2 (too large — recurse)         │
│ → keep as is    │  └──────────────────────────────────────┘
└─────────────────┘             │
                                ▼ Try "\n" split
                   ┌────────────┐  ┌──────────────┐
                   │ Line 1     │  │ Lines 2-5    │
                   │ (small)    │  │ (keep)       │
                   └────────────┘  └──────────────┘
```

**LangChain Implementation:**
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],  # default order
    length_function=len,
)

chunks = splitter.split_documents(documents)
print(f"Created {len(chunks)} chunks")
```

**With token-based counting (recommended for LLM compatibility):**
```python
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer

splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    model_name="gpt-4",
    chunk_size=512,    # tokens, not characters
    chunk_overlap=64,
)
```

| Pros | Cons |
|---|---|
| Respects natural text boundaries | Slightly more complex |
| Adapts to content structure | Still not fully semantic |
| Works well across document types | May miss domain-specific structures |
| Widely used and battle-tested | |

**Best for:** Most RAG pipelines — this is the go-to default

---

## 7. Strategy 5 — Semantic Chunking

Instead of splitting by size, split where the **meaning shifts** by measuring cosine similarity between consecutive sentences.

```
SEMANTIC CHUNKING — How It Works

Step 1: Split into sentences
S1: "The heart pumps blood throughout the body."
S2: "It beats approximately 100,000 times per day."
S3: "Blood carries oxygen to all organs and tissues."
S4: "Meanwhile, the stock market saw record highs."  ← Topic shift!
S5: "Tech stocks led the rally with 3% gains."

Step 2: Embed each sentence and compare adjacent similarities

S1↔S2: similarity = 0.87  (same topic — cardiac function)
S2↔S3: similarity = 0.79  (related — still cardiovascular)
S3↔S4: similarity = 0.12  ← BIG DROP = chunk boundary!
S4↔S5: similarity = 0.81  (same topic — finance)

Step 3: Create chunks at boundaries

Chunk 1: [S1, S2, S3]  — Cardiovascular content
Chunk 2: [S4, S5]      — Financial content

Similarity threshold: 0.5 (split where similarity drops below)
```

**Visualization:**
```
Semantic Similarity Between Adjacent Sentences
1.0 │
    │   ●───●───●
0.8 │                   ●───●
    │
0.5 │── threshold line ──────────────────
    │
0.1 │           ●
    │           ▲
    └───────────────────────────────────
    S1 S2 S3 S4 S5 S6 S7

         Chunk boundary = where similarity dips below threshold
```

**LangChain Implementation:**
```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()

splitter = SemanticChunker(
    embeddings=embeddings,
    breakpoint_threshold_type="percentile",  # or "standard_deviation"
    breakpoint_threshold_amount=95,          # top 95th percentile of drops
)

chunks = splitter.split_documents(documents)
```

| Pros | Cons |
|---|---|
| Chunks respect topic boundaries | Slower — requires embedding every sentence |
| Best semantic coherence | More expensive (API calls) |
| Adapts to content naturally | Harder to control chunk size |
| Produces meaningful units | Requires an embedding model upfront |

**Best for:** Complex documents where topics shift, research papers, long-form content

---

## 8. Strategy 6 — Hierarchical / Parent-Child Chunking

Store **small chunks for precise retrieval** but return **large parent chunks for richer context** to the LLM.

```
HIERARCHICAL CHUNKING CONCEPT

                    FULL DOCUMENT
              ┌──────────────────────────┐
              │   Parent Document        │
              │   (full chapter/section) │
              └──────────────┬───────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
    ┌───────────┐      ┌───────────┐      ┌───────────┐
    │  Child 1  │      │  Child 2  │      │  Child 3  │
    │ (128 tok) │      │ (128 tok) │      │ (128 tok) │
    └───────────┘      └───────────┘      └───────────┘
    ← Embedded & indexed for search →

RETRIEVAL FLOW:
  1. Query matches Child 2 (small, precise chunk)
  2. System looks up Child 2's parent
  3. Returns full Parent to LLM for rich context
  4. LLM answers with full context, not just the snippet
```

**LangChain Implementation:**
```python
from langchain.retrievers import ParentDocumentRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.storage import InMemoryStore

# Small chunks for retrieval
child_splitter = RecursiveCharacterTextSplitter(chunk_size=200)

# Large chunks returned to LLM
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)

vectorstore = Chroma(embedding_function=embeddings)
store = InMemoryStore()  # holds parent documents

retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)

retriever.add_documents(documents)
```

| Pros | Cons |
|---|---|
| Best of both worlds | More complex setup |
| Precise retrieval + rich context | Requires document store + vector store |
| Reduces hallucination significantly | Higher memory usage |
| Great for long-form documents | |

**Best for:** Long technical documents, books, documentation wikis — module 04+ in this repo

---

## 9. Strategy 7 — Markdown / Structure-Aware Chunking

Respects the **logical structure** of Markdown, HTML, or code — splits at headers, sections, or code blocks.

```
MARKDOWN-AWARE CHUNKING

Input Markdown:
# Introduction
Some intro text here...

## Section 1: Background
Background content goes here. More details follow.

### Subsection 1.1
Specific details about the subtopic.

## Section 2: Methods
Methods described here in detail.

Split at header level 2 (##):

Chunk 1:
┌────────────────────────────────────┐
│ # Introduction                      │
│ Some intro text here...             │
└────────────────────────────────────┘

Chunk 2:
┌────────────────────────────────────┐
│ ## Section 1: Background            │
│ Background content goes here.       │
│ ### Subsection 1.1                  │
│ Specific details about...           │
└────────────────────────────────────┘

Chunk 3:
┌────────────────────────────────────┐
│ ## Section 2: Methods              │
│ Methods described here in detail.   │
└────────────────────────────────────┘
```

**LangChain Implementation:**
```python
from langchain_text_splitters import MarkdownHeaderTextSplitter

headers_to_split_on = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]

splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on,
    strip_headers=False,
)

chunks = splitter.split_text(markdown_text)

# Each chunk now has metadata like:
# {"h1": "Introduction", "h2": "Section 1"}
# Great for metadata-filtered RAG!
```

| Pros | Cons |
|---|---|
| Preserves document hierarchy | Only works for structured formats |
| Metadata-rich chunks | Requires well-formatted source docs |
| Great for docs sites | Markdown-only (not PDFs) |
| Chunks align with human understanding | |

**Best for:** Documentation sites, wikis, technical manuals in Markdown/HTML

---

## 10. Chunk Overlap Explained

Overlap ensures that sentences or ideas that fall at a chunk boundary are not lost.

```
WITHOUT OVERLAP — Information Loss

Chunk 1: "...The final step is to heat the mixture to 180°C."
Chunk 2: "This temperature must be maintained for 20 minutes..."

Query: "How long should I heat the mixture?"

Chunk 1 retrieved → mentions 180°C but not duration
Chunk 2 retrieved → mentions 20 minutes but not context

Result: Incomplete answer!

WITH OVERLAP (overlap = 1 sentence)

Chunk 1: "...The final step is to heat the mixture to 180°C."
                                                         ↓↓↓↓↓↓
Chunk 2: "The final step is to heat the mixture to 180°C.
          This temperature must be maintained for 20 minutes..."

Query: "How long should I heat the mixture?"
Chunk 2 retrieved → contains FULL context → correct answer!
```

**How to set overlap:**
```
Recommended overlap = 10–20% of chunk size

chunk_size = 1000 tokens
chunk_overlap = 100–200 tokens  (10–20%)

Too little overlap → information falls through the cracks
Too much overlap  → redundancy, wastes context window, increases cost
```

---

## 11. How to Choose Chunk Size

```
CHUNK SIZE SELECTION GUIDE

Document Type          │ Recommended Size    │ Reasoning
───────────────────────┼─────────────────────┼──────────────────────────
Short FAQs / Q&A       │ 128–256 tokens      │ Each Q&A is atomic
News articles          │ 256–512 tokens      │ Paragraph = full story
Technical docs         │ 512–1024 tokens     │ Need full context
Research papers        │ 512–1024 tokens     │ Dense information
Legal contracts        │ 256–512 tokens      │ Precise clause retrieval
Code files             │ Full function/class │ Don't split mid-function
Books / Long reports   │ 1024–2048 tokens    │ Chapters need context
Chat/Support logs      │ Full conversation   │ Context-dependent

RULE OF THUMB:
  If your chunks feel like they could stand alone as answers → right size
  If chunks feel incomplete without reading adjacent chunks → too small
  If chunks cover multiple topics → too large
```

**Empirical approach:**
```
1. Start with chunk_size=512, overlap=64
2. Index your documents
3. Run 10 representative queries
4. Check if retrieved chunks contain the answers
5. Adjust: too fragmented → increase size; too unfocused → decrease size
```

---

## 12. Chunking Strategy Comparison

```
┌────────────────────┬────────────┬─────────────┬──────────┬────────────────┐
│ Strategy           │ Speed      │ Coherence   │ Control  │ Best Use Case  │
├────────────────────┼────────────┼─────────────┼──────────┼────────────────┤
│ Fixed-Size         │ Fastest    │ Low         │ High     │ Prototyping    │
│ Sentence-Based     │ Fast       │ Medium      │ Medium   │ FAQ, Q&A docs  │
│ Paragraph-Based    │ Fast       │ High        │ Low      │ Articles/Books │
│ Recursive (default)│ Fast       │ Medium-High │ High     │ General RAG    │
│ Semantic           │ Slow       │ Highest     │ Low      │ Complex docs   │
│ Hierarchical       │ Medium     │ Highest     │ Medium   │ Long documents │
│ Markdown-Aware     │ Fast       │ High        │ High     │ Docs sites     │
└────────────────────┴────────────┴─────────────┴──────────┴────────────────┘

Complexity:  Fixed ──────────────────────────────────────▶ Hierarchical
Quality:     Fixed ──────────────────────────────────────▶ Semantic
```

### Quick Decision Tree

```
What type of documents do you have?
│
├─ Markdown / HTML → Markdown-Aware Chunking
│
├─ Short FAQs / Q&A pairs → Sentence-Based (small chunks)
│
├─ General text (articles, reports) → Recursive Character (default)
│
├─ Long documents needing context → Hierarchical / Parent-Child
│
└─ Complex multi-topic documents → Semantic Chunking
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        KEY TAKEAWAYS                             │
│                                                                   │
│  1. Chunking is foundational — bad chunking breaks all RAG       │
│                                                                   │
│  2. Default choice: RecursiveCharacterTextSplitter (512 tokens)  │
│                                                                   │
│  3. Always use overlap (10–20% of chunk size)                    │
│                                                                   │
│  4. Token-based sizing > character-based for LLM compatibility   │
│                                                                   │
│  5. Test your chunking by checking if retrieved chunks contain   │
│     actual answers to your test queries                          │
│                                                                   │
│  6. For production: consider Hierarchical chunking               │
└─────────────────────────────────────────────────────────────────┘
```

---

**Previous ←** [01_what_is_rag.md](01_what_is_rag.md)
**Next →** [03_embeddings_explained.md](03_embeddings_explained.md) — How text becomes searchable vectors
