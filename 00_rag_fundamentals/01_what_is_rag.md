# 01 · What is RAG (Retrieval-Augmented Generation)?

---

## Table of Contents

1. [The Problem RAG Solves](#1-the-problem-rag-solves)
2. [What is RAG?](#2-what-is-rag)
3. [The RAG Pipeline — Step by Step](#3-the-rag-pipeline--step-by-step)
4. [Core Components](#4-core-components)
5. [RAG vs Fine-Tuning vs Prompting](#5-rag-vs-fine-tuning-vs-prompting)
6. [Types of RAG](#6-types-of-rag)
7. [When to Use RAG](#7-when-to-use-rag)
8. [Limitations of RAG](#8-limitations-of-rag)
9. [Real-World Use Cases](#9-real-world-use-cases)
10. [Key Terminology Glossary](#10-key-terminology-glossary)

---

## 1. The Problem RAG Solves

Large Language Models (LLMs) like GPT-4, Claude, and Gemini are incredibly powerful — they can reason, write code, summarize, and answer questions. But they have a fundamental limitation:

> **They only know what they learned during training.**

This creates several problems:

| Problem | Description |
|---|---|
| **Knowledge Cutoff** | The model has no knowledge of events after its training date |
| **Hallucination** | When uncertain, models confidently fabricate plausible-sounding but incorrect answers |
| **No Private Data Access** | The model cannot access your internal documents, databases, or proprietary knowledge |
| **No Source Attribution** | Answers have no traceable source — you cannot verify where the information came from |
| **Staleness** | Even if trained recently, domain-specific knowledge (medical, legal, financial) goes out of date |

### The Classic Failure Example

```
User: "What are the Q3 2025 revenue figures for our company?"

LLM without RAG: "I don't have access to your company's financial data.
Based on general industry trends..." [proceeds to hallucinate numbers]
```

RAG solves this by giving the model access to a **dynamic, up-to-date knowledge base** at query time.

---

## 2. What is RAG?

**Retrieval-Augmented Generation (RAG)** is a technique that enhances LLM responses by first retrieving relevant information from an external knowledge base and then injecting that information into the prompt before generating an answer.

It was introduced by **Lewis et al. (Facebook AI Research, 2020)** in the paper:
> *"Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"*

### The Core Idea in One Sentence

> Instead of relying solely on the LLM's internal knowledge, RAG **looks up relevant facts** from your documents and **hands them to the LLM** along with the user's question.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RAG SYSTEM                                   │
│                                                                       │
│   ┌──────────┐    ┌──────────────┐    ┌───────────┐    ┌─────────┐  │
│   │  User    │───▶│   Retrieve   │───▶│  Augment  │───▶│Generate │  │
│   │  Query   │    │  (Search DB) │    │  (Prompt) │    │  (LLM)  │  │
│   └──────────┘    └──────────────┘    └───────────┘    └─────────┘  │
│                          ▲                                    │       │
│                          │                                    ▼       │
│                   ┌──────────────┐                    ┌───────────┐  │
│                   │  Vector      │                    │  Answer   │  │
│                   │  Database    │                    │ + Sources │  │
│                   └──────────────┘                    └───────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. The RAG Pipeline — Step by Step

RAG operates in two phases: **Indexing** (offline, done once) and **Querying** (online, done per request).

### Phase 1: Indexing (Offline)

This is the preparation phase where your documents are processed and stored.

```
                        INDEXING PIPELINE

  Raw Documents                                        Vector Store
  ┌──────────┐                                        ┌──────────┐
  │  PDF     │                                        │          │
  │  DOCX    │──▶ [Load] ──▶ [Chunk] ──▶ [Embed] ──▶│  Chunks  │
  │  HTML    │                                        │    +     │
  │  CSV     │                                        │ Vectors  │
  │  Web     │                                        │          │
  └──────────┘                                        └──────────┘

  Step 1: Load     → Read raw files using document loaders
  Step 2: Chunk    → Split into smaller, manageable pieces
  Step 3: Embed    → Convert text chunks to numerical vectors
  Step 4: Store    → Save vectors + original text to vector DB
```

**Step 1 — Document Loading**
```python
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("company_handbook.pdf")
documents = loader.load()
# Result: List of Document objects with page_content + metadata
```

**Step 2 — Chunking**
```
Original Document (10,000 words)
┌────────────────────────────────────────────────┐
│ Introduction... Section 1... Section 2...      │
│ ... lots of text ...                           │
└────────────────────────────────────────────────┘

After Chunking (500 words each, 50 word overlap)
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Chunk 1  │ │ Chunk 2  │ │ Chunk 3  │ │ Chunk 4  │
│ words    │ │ words    │ │ words    │ │ words    │
│ 1-500    │ │ 451-950  │ │ 901-1400 │ │ ...      │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
              ◀──50──▶     ◀──50──▶
              overlap       overlap
```

**Step 3 — Embedding**
```
"The company was founded in 2010 in San Francisco"
                        │
              Embedding Model
              (e.g. text-embedding-3-small)
                        │
                        ▼
[0.023, -0.871, 0.445, 0.112, -0.334, 0.778, ...]
 ◀────────────── 1536 dimensions ──────────────▶
```

**Step 4 — Vector Storage**
```
Vector Database
┌─────────────────────────────────────────────────────────┐
│  ID  │  Vector (1536d)  │  Text Chunk   │  Metadata     │
├─────────────────────────────────────────────────────────┤
│  001 │ [0.02, -0.87...] │ "Founded in.."│ source: doc1  │
│  002 │ [0.45, 0.11...]  │ "Products are"│ source: doc1  │
│  003 │ [-0.33, 0.78...] │ "In Q3 2024.."│ source: doc2  │
└─────────────────────────────────────────────────────────┘
```

---

### Phase 2: Querying (Online)

This happens every time a user asks a question.

```
                        QUERYING PIPELINE

  User Query                                              Final Answer
  ┌──────────┐                                           ┌───────────┐
  │"What is  │                                           │"The return│
  │ our      │                                           │ policy is │
  │ return   │                                           │ 30 days.. │
  │ policy?" │                                           │ Source:   │
  └──────────┘                                           │ doc3.pdf" │
       │                                                 └───────────┘
       │                                                       ▲
       ▼                                                       │
  ┌──────────┐    ┌──────────────┐    ┌───────────────────────┴──┐
  │  Embed   │    │   Search     │    │      LLM Generation      │
  │  Query   │───▶│  Vector DB   │───▶│                          │
  │          │    │  (Top-K)     │    │  System: You are a...    │
  └──────────┘    └──────────────┘    │  Context: [Chunk 1]      │
                        │             │           [Chunk 2]      │
                        ▼             │  Question: What is our.. │
                  ┌──────────┐        └──────────────────────────┘
                  │Retrieved │
                  │ Chunks   │
                  │ (Top 3-5)│
                  └──────────┘
```

**Step 1 — Query Embedding**
```python
query = "What is our return policy?"
query_vector = embedding_model.embed_query(query)
# Result: [0.031, -0.442, 0.891, ...]  same model as indexing
```

**Step 2 — Similarity Search**
```
Query Vector: [0.031, -0.442, 0.891, ...]

Compare against all stored vectors using cosine similarity:

Chunk 001: similarity = 0.21  ← not relevant
Chunk 002: similarity = 0.89  ← HIGHLY RELEVANT ✓
Chunk 003: similarity = 0.76  ← relevant ✓
Chunk 004: similarity = 0.31  ← not relevant
Chunk 005: similarity = 0.82  ← relevant ✓

Return Top-3: [Chunk 002, Chunk 005, Chunk 003]
```

**Step 3 — Prompt Augmentation**
```
┌─────────────────────────────────────────────────────────┐
│                    AUGMENTED PROMPT                      │
│                                                          │
│  System: You are a helpful assistant. Answer based       │
│  only on the provided context. If unsure, say so.        │
│                                                          │
│  Context:                                                │
│  [Chunk 002]: "Our return policy allows customers to     │
│   return products within 30 days of purchase..."         │
│                                                          │
│  [Chunk 005]: "Items must be in original packaging       │
│   and include the receipt for a full refund..."          │
│                                                          │
│  [Chunk 003]: "Digital products and gift cards are       │
│   non-refundable once activated..."                      │
│                                                          │
│  Question: What is our return policy?                    │
└─────────────────────────────────────────────────────────┘
```

**Step 4 — LLM Generation**
```
LLM reads the context and generates a grounded answer:

"Our return policy allows customers to return physical
products within 30 days of purchase. Items must be in
their original packaging and accompanied by the receipt
for a full refund. Note that digital products and gift
cards are non-refundable once activated.

Sources: company_handbook.pdf (pages 12, 15, 18)"
```

---

## 4. Core Components

### 4.1 Document Loaders

Convert raw files into a standard `Document` format.

```
┌────────────────────────────────────────┐
│           Document Loaders             │
├────────────┬───────────────────────────┤
│ Format     │ Loader                    │
├────────────┼───────────────────────────┤
│ PDF        │ PyPDFLoader, PDFMiner     │
│ Word/DOCX  │ Docx2txtLoader            │
│ HTML/Web   │ WebBaseLoader             │
│ CSV        │ CSVLoader                 │
│ JSON       │ JSONLoader                │
│ Markdown   │ UnstructuredMarkdownLoader│
│ YouTube    │ YoutubeAudioLoader        │
│ Database   │ SQLDatabaseLoader         │
└────────────┴───────────────────────────┘
```

### 4.2 Text Splitters / Chunkers

Break documents into smaller pieces for better retrieval precision.
*(Deep dive → [02_chunking_strategies.md](02_chunking_strategies.md))*

### 4.3 Embedding Models

Convert text to numerical vectors.
*(Deep dive → [03_embeddings_explained.md](03_embeddings_explained.md))*

```
Popular Embedding Models:
┌─────────────────────────┬──────────┬────────────────┐
│ Model                   │ Dims     │ Provider       │
├─────────────────────────┼──────────┼────────────────┤
│ text-embedding-3-small  │ 1536     │ OpenAI         │
│ text-embedding-3-large  │ 3072     │ OpenAI         │
│ embed-english-v3.0      │ 1024     │ Cohere         │
│ nomic-embed-text        │ 768      │ Nomic (local)  │
│ all-MiniLM-L6-v2        │ 384      │ HuggingFace    │
│ text-embedding-004      │ 768      │ Google         │
└─────────────────────────┴──────────┴────────────────┘
```

### 4.4 Vector Stores

Store and search embeddings efficiently.
*(Deep dive → [04_vector_databases.md](04_vector_databases.md))*

### 4.5 Retrievers

The bridge between query and stored documents.

```
Types of Retrievers:
┌───────────────────┬─────────────────────────────────────┐
│ Type              │ Description                          │
├───────────────────┼─────────────────────────────────────┤
│ Dense Retriever   │ Semantic similarity via embeddings   │
│ Sparse Retriever  │ Keyword-based (BM25, TF-IDF)        │
│ Hybrid Retriever  │ Dense + Sparse combined              │
│ MMR Retriever     │ Maximal Marginal Relevance           │
│ Multi-Query       │ Multiple query reformulations        │
│ Contextual        │ History-aware retrieval              │
└───────────────────┴─────────────────────────────────────┘
```

### 4.6 LLM (Generator)

The language model that reads context and generates the final answer.

---

## 5. RAG vs Fine-Tuning vs Prompting

```
┌────────────────────┬──────────────┬──────────────┬─────────────────┐
│ Dimension          │ Prompting    │ RAG          │ Fine-Tuning     │
├────────────────────┼──────────────┼──────────────┼─────────────────┤
│ Knowledge Source   │ LLM only     │ External DB  │ Baked into model│
│ Setup Cost         │ None         │ Medium       │ High            │
│ Compute Cost       │ Low          │ Medium       │ Very High       │
│ Updatability       │ Manual       │ Easy         │ Expensive       │
│ Source Attribution │ No           │ Yes          │ No              │
│ Private Data       │ No           │ Yes          │ Yes             │
│ Hallucination Risk │ High         │ Low          │ Medium          │
│ Latency            │ Fast         │ Moderate     │ Fast            │
│ Best For           │ General Q&A  │ Document Q&A │ Style/Format    │
└────────────────────┴──────────────┴──────────────┴─────────────────┘
```

### Decision Guide

```
Do you need the model to answer questions
about specific documents or private data?
              │
         YES  │  NO
              │
    ┌─────────▼──────┐      ┌──────────────────────┐
    │   Use RAG      │      │ Does it need a        │
    └────────────────┘      │ specific style/format?│
                            └──────────┬───────────┘
                                  YES  │  NO
                                       │
                           ┌───────────▼──┐  ┌──────────────┐
                           │ Fine-Tuning  │  │  Prompting   │
                           └─────────────┘  └──────────────┘
```

---

## 6. Types of RAG

The field has evolved rapidly. Here's the progression this repository covers:

```
RAG EVOLUTION TIMELINE

Naive RAG       →  Intermediate RAG     →  Advanced RAG         →  Agentic RAG
──────────────     ──────────────────      ──────────────────      ──────────────
Simple chunk       Metadata filtering      Reranking               Agent reasoning
+ embed            Hybrid search           Multi-query             Graph RAG
+ search           Better chunking         CRAG (Corrective)       Multimodal
                                                                   Adaptive RAG
```

| Module | Technique | Key Innovation |
|---|---|---|
| 01 | Naive RAG | Basic chunk → embed → retrieve → generate |
| 02 | Metadata Filtered RAG | Filter by date, category, source |
| 03 | Hybrid Search RAG | Dense + sparse retrieval combined |
| 04 | Reranking RAG | Cross-encoder re-scores retrieved chunks |
| 05 | Multi-Query RAG | Multiple query reformulations |
| 06 | Corrective RAG (CRAG) | Self-corrects poor retrievals |
| 07 | Agentic RAG | LangGraph-based multi-step reasoning |
| 08 | Graph RAG | Knowledge graph + embeddings |
| 09 | Multimodal RAG | Images + text combined |
| 10 | Adaptive RAG | Dynamically selects best strategy |

---

## 7. When to Use RAG

### RAG is a good fit when:

- You have a **large corpus of private/proprietary documents** (manuals, contracts, reports)
- You need **up-to-date information** the LLM wasn't trained on
- You need **source attribution** — users must be able to verify answers
- Knowledge **changes frequently** (e.g., product catalog, policies, news)
- You want to **avoid hallucinations** on factual questions
- Multiple knowledge bases need to be **searched selectively**

### RAG is not ideal when:

- The task requires **deep reasoning** across the entire document corpus
- You need the model to **internalize style or behavior** (use fine-tuning instead)
- Your queries are purely **general knowledge** (just use the LLM directly)
- You have **extremely low latency requirements** (retrieval adds overhead)

---

## 8. Limitations of RAG

```
COMMON RAG FAILURE MODES

1. RETRIEVAL FAILURE
   ┌─────────────────────────────────────────────────────┐
   │ The answer exists in the document but wasn't        │
   │ retrieved because the query phrasing didn't match   │
   │ the chunk's semantic space.                         │
   │ Fix: Multi-Query RAG, Hybrid Search, Better Chunking│
   └─────────────────────────────────────────────────────┘

2. CONTEXT WINDOW OVERFLOW
   ┌─────────────────────────────────────────────────────┐
   │ Too many chunks retrieved → exceeds LLM context     │
   │ window → information gets truncated.                │
   │ Fix: Reranking, Smaller Chunks, Summarization       │
   └─────────────────────────────────────────────────────┘

3. IRRELEVANT RETRIEVAL (Low Precision)
   ┌─────────────────────────────────────────────────────┐
   │ Retrieved chunks are semantically similar but not   │
   │ actually relevant to the question.                  │
   │ Fix: Reranking, Metadata Filtering, CRAG            │
   └─────────────────────────────────────────────────────┘

4. CHUNK FRAGMENTATION
   ┌─────────────────────────────────────────────────────┐
   │ An answer spans multiple chunks but only part is    │
   │ retrieved, giving an incomplete response.           │
   │ Fix: Larger chunks, Hierarchical chunking, Overlap  │
   └─────────────────────────────────────────────────────┘

5. FAITHFULNESS FAILURE
   ┌─────────────────────────────────────────────────────┐
   │ The LLM ignores the retrieved context and answers   │
   │ from its own (possibly wrong) knowledge.            │
   │ Fix: Better system prompts, CRAG, Adaptive RAG      │
   └─────────────────────────────────────────────────────┘
```

---

## 9. Real-World Use Cases

```
┌─────────────────────────────────────────────────────────────────┐
│                     RAG USE CASES BY INDUSTRY                    │
├─────────────────┬───────────────────────────────────────────────┤
│ Industry        │ Application                                    │
├─────────────────┼───────────────────────────────────────────────┤
│ Legal           │ Contract analysis, case law search             │
│ Healthcare      │ Clinical guidelines Q&A, drug interactions     │
│ Finance         │ Earnings report analysis, regulatory search    │
│ Customer Support│ Product FAQ chatbots, ticket resolution        │
│ Education       │ Personalized tutoring from course materials    │
│ Software Dev    │ Codebase Q&A, documentation assistant          │
│ HR / People Ops │ Policy handbook assistant, onboarding bot      │
│ Research        │ Academic paper Q&A, literature review          │
│ E-Commerce      │ Product recommendation with specs search       │
│ Government      │ Policy document Q&A, citizen services          │
└─────────────────┴───────────────────────────────────────────────┘
```

### Production System Architecture

```
                        PRODUCTION RAG SYSTEM

  ┌─────────┐    ┌──────────┐    ┌────────────┐    ┌──────────────┐
  │  User   │───▶│  API     │───▶│  Guardrails│───▶│   RAG Engine │
  │  (Web)  │    │ Gateway  │    │  & Auth    │    │              │
  └─────────┘    └──────────┘    └────────────┘    └──────┬───────┘
                                                          │
                    ┌─────────────────────────────────────┤
                    │                                     │
                    ▼                                     ▼
           ┌────────────────┐                   ┌────────────────┐
           │  Vector Store  │                   │  LLM Provider  │
           │  (Pinecone /   │                   │  (OpenAI /     │
           │   Weaviate)    │                   │   Anthropic)   │
           └────────────────┘                   └────────────────┘
                    │
                    ▼
           ┌────────────────┐    ┌────────────────┐
           │  Document      │    │  Observability  │
           │  Store (S3)    │    │  (LangSmith)    │
           └────────────────┘    └────────────────┘
```

---

## 10. Key Terminology Glossary

| Term | Definition |
|---|---|
| **RAG** | Retrieval-Augmented Generation — grounding LLM answers with retrieved documents |
| **Embedding** | A dense numerical vector representing the semantic meaning of text |
| **Vector Store** | Database optimized to store and search high-dimensional vectors |
| **Chunk** | A smaller segment of a document used as the retrieval unit |
| **Cosine Similarity** | Metric measuring directional closeness between two vectors (0=opposite, 1=identical) |
| **Top-K** | Retrieving the K most similar chunks to a query |
| **Context Window** | Maximum tokens an LLM can process in one call |
| **Hallucination** | When an LLM generates confident but factually incorrect information |
| **Grounding** | Anchoring LLM output to retrieved factual context |
| **Retriever** | Component responsible for finding relevant chunks from the knowledge base |
| **Generator** | The LLM that produces the final response using retrieved context |
| **BM25** | Classic sparse retrieval algorithm based on term frequency |
| **ANN** | Approximate Nearest Neighbor — fast algorithm for vector similarity search |
| **HNSW** | Hierarchical Navigable Small World — efficient graph-based ANN index |
| **Reranker** | A cross-encoder model that re-scores retrieved chunks for better relevance |

---

## Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        KEY TAKEAWAYS                             │
│                                                                   │
│  1. RAG = Retrieve relevant docs → Augment prompt → Generate     │
│                                                                   │
│  2. Two phases: INDEXING (offline) and QUERYING (online)         │
│                                                                   │
│  3. Core stack: Loader → Chunker → Embedder → VectorDB → LLM    │
│                                                                   │
│  4. RAG reduces hallucinations by grounding answers in facts     │
│                                                                   │
│  5. RAG is not fine-tuning — they solve different problems       │
│                                                                   │
│  6. Naive RAG works but has failure modes — this repo shows      │
│     10 progressively better techniques to address them           │
└─────────────────────────────────────────────────────────────────┘
```

---

**Next →** [02_chunking_strategies.md](02_chunking_strategies.md) — How to split documents effectively for optimal retrieval
