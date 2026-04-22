# 04 · Vector Databases

> **Vector databases are the memory of your RAG system.**
> They store millions of embeddings and find the most similar ones in milliseconds.

---

## Table of Contents

1. [What is a Vector Database?](#1-what-is-a-vector-database)
2. [The Search Problem — Why Regular Databases Fail](#2-the-search-problem--why-regular-databases-fail)
3. [How Vector Search Works — ANN Algorithms](#3-how-vector-search-works--ann-algorithms)
4. [Key Concepts](#4-key-concepts)
5. [Major Vector Databases Compared](#5-major-vector-databases-compared)
6. [Deep Dive: Chroma (Local Development)](#6-deep-dive-chroma-local-development)
7. [Deep Dive: FAISS (In-Memory)](#7-deep-dive-faiss-in-memory)
8. [Deep Dive: Pinecone (Cloud)](#8-deep-dive-pinecone-cloud)
9. [Deep Dive: Weaviate (Hybrid Search)](#9-deep-dive-weaviate-hybrid-search)
10. [Deep Dive: Qdrant (Production)](#10-deep-dive-qdrant-production)
11. [How to Choose a Vector Database](#11-how-to-choose-a-vector-database)
12. [Metadata Filtering](#12-metadata-filtering)
13. [Vector DB in LangChain](#13-vector-db-in-langchain)

---

## 1. What is a Vector Database?

A **vector database** is a specialized database designed to store, index, and search high-dimensional numerical vectors efficiently.

Unlike traditional databases that store structured rows or documents, vector databases store:
- The **embedding vector** (e.g., 1536 floats for OpenAI)
- The **original text** (or a reference to it)
- **Metadata** (source, date, category, etc.)

And they answer one core question: **"Which stored vectors are most similar to this query vector?"**

```
TRADITIONAL DATABASE vs VECTOR DATABASE

SQL Database:
  SELECT * FROM docs WHERE category = 'finance' AND year = 2024
  → Finds exact matches by field values

Vector Database:
  search(query_vector, top_k=5)
  → Finds approximate semantic matches by vector proximity
  → Can combine with metadata filters!

Both are useful — RAG systems often use both:
  Vector DB for semantic search + SQL/metadata for filtering
```

---

## 2. The Search Problem — Why Regular Databases Fail

Finding the nearest vector in a database of 1 million 1536-dimensional vectors by brute force:

```
BRUTE FORCE SEARCH (Exact KNN)

For each query, compare against ALL stored vectors:

Query vector: [0.021, -0.432, 0.871, ...]

Step 1: Compare with vector_001 → similarity = 0.73
Step 2: Compare with vector_002 → similarity = 0.41
Step 3: Compare with vector_003 → similarity = 0.89
...
Step 1,000,000: Compare with vector_1M → similarity = 0.52

Sort all 1M scores → Return Top-5

Time complexity: O(n × d) where n = vectors, d = dimensions

For 1M vectors × 1536 dims = 1.5 BILLION multiplications per query
At 1GHz processor: ~1.5 seconds per query (too slow!)

Need: Millisecond search → Approximate Nearest Neighbor (ANN)
```

---

## 3. How Vector Search Works — ANN Algorithms

Approximate Nearest Neighbor (ANN) algorithms trade a tiny bit of accuracy for massive speed gains.

### HNSW — Hierarchical Navigable Small World

The most popular algorithm — used by Chroma, Qdrant, Weaviate, and others.

```
HNSW STRUCTURE (simplified)

Layer 2 (sparse):  ●───────────────────────────●
                   │                           │
Layer 1 (medium):  ●───●───────────●───────────●
                   │   │           │           │
Layer 0 (dense):   ●─●─●─●─●─●─●─●─●─●─●─●─●─●
                              ↑
                          Entry point for search

Search Process:
1. Enter at top layer (sparse connections — big jumps)
2. Find best neighbor at this level
3. Move down to next layer (denser) near that neighbor
4. Repeat until bottom layer reached
5. Fine-search locally at Layer 0

Like navigating: country → city → neighborhood → street
Each level narrows the search area rapidly

Time complexity: O(log n)  ← from O(n)
Typical speed:   1-10ms for 1M vectors
Typical recall:  95-99% (finds 95-99% of true nearest neighbors)
```

**Building the HNSW graph:**
```
As each vector is added:

1. Randomly assign to a max layer (geometric distribution)
   Most vectors land at Layer 0 (base)
   Few vectors reach Layer 2 (express highway)

2. At each layer, connect to M nearest neighbors

3. Result: Small-world network where any two nodes
   are reachable in O(log n) hops

Parameters:
  M = 16         (connections per node — higher = better recall, more memory)
  ef_construction = 200  (search width during build — higher = better quality)
  ef_search = 50         (search width during query — higher = better recall)
```

### IVF — Inverted File Index

Used by FAISS — groups vectors into clusters.

```
IVF STRUCTURE

Step 1: Cluster all vectors into K clusters (K-means)

        Cluster 1     Cluster 2     Cluster 3
        ┌────────┐    ┌────────┐    ┌────────┐
        │ ●●●●   │    │ ●● ●  │    │  ● ●● │
        │ ●● ●●  │    │ ●●●   │    │ ●●●   │
        │ ● ●●   │    │  ●●●  │    │  ●●   │
        └────────┘    └────────┘    └────────┘
         centroid1     centroid2     centroid3

Step 2: For each query:
  a. Find top-N closest cluster centroids
  b. Search only within those clusters

Result: Search 10% of vectors instead of 100%
        Speed: ~10x faster
        Recall: ~90-95%

Parameters:
  nlist = 100  (number of clusters)
  nprobe = 10  (how many clusters to search — more = better recall)
```

### LSH — Locality Sensitive Hashing

Older algorithm — maps similar vectors to the same hash bucket.

```
LSH CONCEPT

Similar vectors → Same hash bucket with high probability

Query: [0.5, 0.8, -0.3]  →  hash → "bucket_42"
Doc A: [0.4, 0.9, -0.2]  →  hash → "bucket_42"  ← found!
Doc B: [0.5, 0.8, -0.3]  →  hash → "bucket_42"  ← found!
Doc C: [-0.8, 0.1, 0.9]  →  hash → "bucket_17"  ← skipped

Only search bucket_42 → fast but may miss some neighbors
```

---

## 4. Key Concepts

### Distance Metrics in Vector DBs

```
┌─────────────────────┬──────────────────────────────────────────┐
│ Metric              │ When to Use                              │
├─────────────────────┼──────────────────────────────────────────┤
│ Cosine Similarity   │ Default for text — direction matters     │
│ Euclidean (L2)      │ When magnitude matters; FAISS default    │
│ Dot Product (IP)    │ Normalized vectors — equivalent to cosine│
│ Manhattan (L1)      │ Sparse vectors, categorical data         │
└─────────────────────┴──────────────────────────────────────────┘
```

### Recall vs Speed Tradeoff

```
RECALL vs LATENCY

    100% │ ●
         │   ●
  Recall │      ●
    (%)  │          ●
         │               ●
     50% │                    ●
         └────────────────────────────────▶
              Fast ←──────────── Slow
                     Latency (ms)

ANN Index Parameters control where on this curve you operate:
- Higher ef_search → better recall, slower
- Lower nprobe    → faster, worse recall
- Production RAG typically targets: >95% recall at <50ms
```

### Persistence Options

```
┌──────────────────┬───────────────────────────────────────────┐
│ Storage Type     │ Description                               │
├──────────────────┼───────────────────────────────────────────┤
│ In-Memory        │ Fastest; lost on restart (FAISS, Chroma)  │
│ Local Disk       │ Persistent; single machine (Chroma, FAISS)│
│ Managed Cloud    │ Scalable, replicated (Pinecone, Weaviate) │
│ Self-hosted      │ Full control; you manage (Qdrant, Weaviate)│
└──────────────────┴───────────────────────────────────────────┘
```

---

## 5. Major Vector Databases Compared

```
┌────────────────┬──────────┬───────────┬───────────┬─────────────┬──────────┐
│ Database       │ Hosting  │ Scale     │ Features  │ Best For    │ License  │
├────────────────┼──────────┼───────────┼───────────┼─────────────┼──────────┤
│ Chroma         │ Local    │ Small-Med │ Simple    │ Dev/prototyp│ Apache 2 │
│ FAISS          │ In-Memory│ Large     │ Low-level │ Research    │ MIT      │
│ Pinecone       │ Cloud    │ Any       │ Full      │ Production  │ Propriety│
│ Weaviate       │ Both     │ Large     │ Hybrid    │ Hybrid RAG  │ BSD      │
│ Qdrant         │ Both     │ Large     │ Full      │ Production  │ Apache 2 │
│ Milvus         │ Self-host│ Massive   │ Full      │ Enterprise  │ Apache 2 │
│ pgvector       │ PostgreSQL│ Medium   │ SQL+Vec   │ Existing PG │ MIT      │
│ Redis          │ Both     │ Medium    │ Fast      │ Caching     │ RSAL     │
└────────────────┴──────────┴───────────┴───────────┴─────────────┴──────────┘
```

---

## 6. Deep Dive: Chroma (Local Development)

Chroma is the easiest way to get started with vector search — zero infrastructure, runs in Python.

```
CHROMA ARCHITECTURE

Python Process
┌────────────────────────────────────────────────┐
│  ChromaDB                                       │
│  ┌──────────────────────────────────────────┐  │
│  │  Collection: "my_docs"                   │  │
│  │  ┌──────────────────────────────────┐    │  │
│  │  │ id    │ embedding  │ document │metadata│    │  │
│  │  ├──────────────────────────────────┤    │  │
│  │  │ doc_1 │ [0.2,-0.4] │ "text..." │{src}│    │  │
│  │  │ doc_2 │ [0.8, 0.1] │ "text..." │{src}│    │  │
│  │  └──────────────────────────────────┘    │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  Storage: SQLite + HNSW (local files)           │
└────────────────────────────────────────────────┘
```

**LangChain + Chroma:**
```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()

# In-memory (lost on restart)
vectorstore = Chroma(
    embedding_function=embeddings,
    collection_name="my_rag_docs"
)

# Persistent (saved to disk)
vectorstore = Chroma(
    embedding_function=embeddings,
    collection_name="my_rag_docs",
    persist_directory="./chroma_db"
)

# Add documents
vectorstore.add_documents(chunks)

# Search
results = vectorstore.similarity_search(
    "What is the return policy?",
    k=5
)

# Search with scores
results = vectorstore.similarity_search_with_score(
    "What is the return policy?",
    k=5
)
# Returns: List of (Document, score) tuples
```

**Pros:** Zero setup, great for development, good LangChain integration
**Cons:** Not suitable for large-scale production, single machine only

---

## 7. Deep Dive: FAISS (In-Memory)

Facebook AI Similarity Search — the most powerful library for large-scale, high-performance vector search.

```
FAISS INDEX TYPES

IndexFlatL2 (Exact Search):
  └─ Brute force, 100% recall, slow at scale
  └─ Use for: Small collections (<100K vectors)

IndexIVFFlat (Approximate):
  └─ Clusters + flat search within clusters
  └─ Use for: Medium collections (100K - 10M)

IndexIVFPQ (Compressed):
  └─ Product Quantization compresses vectors ~8x
  └─ Use for: Large collections (10M+) with memory constraints

IndexHNSWFlat (Graph-based):
  └─ Best recall/speed tradeoff for RAM-based search
  └─ Use for: Production with fast recall requirement
```

**LangChain + FAISS:**
```python
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()

# Build index from documents
vectorstore = FAISS.from_documents(chunks, embeddings)

# Save to disk
vectorstore.save_local("faiss_index")

# Load from disk
vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

# Merge two indexes
vectorstore.merge_from(another_vectorstore)
```

**Pros:** Extremely fast, battle-tested at Meta scale, flexible index types
**Cons:** In-memory (RAM-limited), no built-in persistence, no metadata query language

---

## 8. Deep Dive: Pinecone (Cloud)

Fully managed vector database — no infrastructure to manage, scales automatically.

```
PINECONE ARCHITECTURE

Your App                    Pinecone Cloud
┌──────────┐               ┌─────────────────────────────┐
│  Python  │───REST API───▶│  Pinecone Index              │
│  Client  │               │  ┌─────────────────────────┐ │
└──────────┘               │  │  Namespaces             │ │
                           │  │  ┌───────┐ ┌──────────┐ │ │
                           │  │  │ prod  │ │  staging │ │ │
                           │  │  └───────┘ └──────────┘ │ │
                           │  └─────────────────────────┘ │
                           │  Replicated, auto-scaled      │
                           └─────────────────────────────┘

Key Concepts:
  Index    = a collection (one per application/model)
  Namespace = logical partition within an index (like a folder)
  Pod Type = hardware tier (s1, p1, p2 for different scales)
```

**LangChain + Pinecone:**
```python
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import os

# Initialize
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Create index (one time)
pc.create_index(
    name="rag-index",
    dimension=1536,           # must match embedding model
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

# Use with LangChain
vectorstore = PineconeVectorStore(
    index_name="rag-index",
    embedding=embeddings,
    namespace="production"
)

# Add documents
vectorstore.add_documents(chunks)

# Search with metadata filter
results = vectorstore.similarity_search(
    "return policy",
    k=5,
    filter={"category": "legal", "year": {"$gte": 2023}}
)
```

**Pros:** Zero ops, scales to billions of vectors, built-in metadata filtering
**Cons:** Cost (pay per vector), data leaves your infrastructure, vendor lock-in

---

## 9. Deep Dive: Weaviate (Hybrid Search)

Weaviate is purpose-built for **hybrid search** — combining dense vector search with BM25 keyword search.

```
WEAVIATE HYBRID SEARCH

Query: "machine learning optimization techniques"

BM25 (Keyword):             Vector (Semantic):
Scores by keyword match     Scores by meaning similarity

doc_A: 0.82 (exact words)   doc_A: 0.71
doc_B: 0.45                 doc_B: 0.88 (best semantic match)
doc_C: 0.61                 doc_C: 0.63
doc_D: 0.12                 doc_D: 0.79

Reciprocal Rank Fusion combines:
  alpha=0.5 → equal weight to both
  alpha=0.0 → pure keyword
  alpha=1.0 → pure vector

Final ranking: [doc_B, doc_A, doc_C, doc_D]
```

**LangChain + Weaviate:**
```python
import weaviate
from langchain_weaviate.vectorstores import WeaviateVectorStore

client = weaviate.connect_to_local()  # or connect_to_weaviate_cloud()

vectorstore = WeaviateVectorStore(
    client=client,
    index_name="LangChainDocs",
    text_key="text",
    embedding=embeddings
)

# Hybrid search
results = vectorstore.similarity_search(
    "machine learning optimization",
    k=5,
    search_type="hybrid",
    alpha=0.5  # 0=keyword, 1=vector, 0.5=balanced
)
```

**Pros:** Best hybrid search, GraphQL API, schema-based, can run locally or cloud
**Cons:** More complex setup, steeper learning curve

---

## 10. Deep Dive: Qdrant (Production)

Qdrant is a high-performance vector database written in Rust — excellent for self-hosted production deployments.

```
QDRANT FEATURES

Collections → like tables in SQL
Points → each stored vector + payload + id

┌────────────────────────────────────────────────┐
│  Collection: "documents"                        │
│  ┌──────────────────────────────────────────┐  │
│  │  Point {                                 │  │
│  │    id: "uuid-1234",                      │  │
│  │    vector: [0.2, -0.4, 0.8, ...],        │  │
│  │    payload: {                            │  │
│  │      text: "The return policy...",       │  │
│  │      source: "handbook.pdf",             │  │
│  │      page: 12,                           │  │
│  │      category: "legal",                  │  │
│  │      created_at: "2024-01-15"           │  │
│  │    }                                    │  │
│  │  }                                      │  │
│  └──────────────────────────────────────────┘  │
│  Supports: Filtering, Named Vectors, Snapshots  │
└────────────────────────────────────────────────┘
```

**LangChain + Qdrant:**
```python
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(":memory:")  # or host="localhost", port=6333

# Create collection
client.create_collection(
    collection_name="my_docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

vectorstore = QdrantVectorStore(
    client=client,
    collection_name="my_docs",
    embedding=embeddings,
)

vectorstore.add_documents(chunks)

# Search with filter
from qdrant_client.models import Filter, FieldCondition, MatchValue

results = vectorstore.similarity_search(
    "return policy",
    k=5,
    filter=Filter(
        must=[FieldCondition(key="category", match=MatchValue(value="legal"))]
    )
)
```

**Pros:** Fast (Rust), self-hostable, advanced filtering, named vectors, snapshots
**Cons:** More complex API, self-managed ops overhead

---

## 11. How to Choose a Vector Database

```
DECISION TREE

What stage of development are you in?
│
├─ Prototyping / Learning
│   └─ Use CHROMA (zero setup, local)
│
├─ Research / Benchmarking
│   └─ Use FAISS (fastest, flexible index types)
│
└─ Production
    │
    ├─ Can you use a managed service?
    │   ├─ YES → PINECONE (easiest ops)
    │   └─ NO  → Self-host QDRANT or WEAVIATE
    │
    ├─ Do you need hybrid search (keyword + semantic)?
    │   └─ YES → WEAVIATE (best hybrid search)
    │
    ├─ Do you already use PostgreSQL?
    │   └─ YES → pgvector (add vector to existing DB)
    │
    └─ Do you need maximum performance at scale?
        └─ YES → QDRANT (Rust, high throughput)
```

### By Team Size and Scale

```
┌─────────────────┬──────────────────────────────────────────┐
│ Team/Scale      │ Recommended Stack                        │
├─────────────────┼──────────────────────────────────────────┤
│ Solo dev        │ Chroma (local) → Pinecone (when scaling) │
│ Small startup   │ Qdrant (self-hosted) or Pinecone         │
│ Scale-up        │ Weaviate cloud or Qdrant cluster         │
│ Enterprise      │ Milvus, Weaviate, or Pinecone Enterprise  │
│ Existing PG     │ pgvector extension                       │
│ Research        │ FAISS (maximum control)                  │
└─────────────────┴──────────────────────────────────────────┘
```

---

## 12. Metadata Filtering

Metadata filtering lets you narrow the search to specific subsets before or during vector search — critical for production RAG.

```
METADATA FILTERING CONCEPT

Without filtering:
  Query: "What is the refund policy?"
  Searches: ALL documents (policies, marketing, HR, legal, ...)
  Problem: May retrieve unrelated documents from wrong category

With filtering:
  Query: "What is the refund policy?"
  Filter: category = "legal" AND year >= 2023
  Searches: ONLY legal documents from 2023+
  Result: Precise, relevant answers

FILTER TYPES:
  Exact match:   category == "finance"
  Range:         date >= "2024-01-01"
  In list:       department IN ["HR", "Legal"]
  Combination:   source == "handbook" AND page > 10
  Negation:      NOT category == "draft"
```

**Adding metadata to chunks:**
```python
from langchain_core.documents import Document

# Method 1: Add during loading
chunks = [
    Document(
        page_content="The return policy allows...",
        metadata={
            "source": "handbook.pdf",
            "page": 12,
            "category": "legal",
            "year": 2024,
            "department": "customer_service"
        }
    )
]

# Method 2: Add metadata to existing chunks
for chunk in chunks:
    chunk.metadata["indexed_at"] = "2024-01-15"
    chunk.metadata["chunk_size"] = len(chunk.page_content)
```

**Filtering during search:**
```python
# Chroma
results = vectorstore.similarity_search(
    "return policy",
    filter={"category": "legal"}  # exact match
)

# Pinecone
results = vectorstore.similarity_search(
    "return policy",
    filter={"category": {"$eq": "legal"}, "year": {"$gte": 2023}}
)

# Qdrant
from qdrant_client.models import Filter, FieldCondition, Range

results = vectorstore.similarity_search(
    "return policy",
    filter=Filter(must=[
        FieldCondition(key="category", match=MatchValue(value="legal")),
        FieldCondition(key="year", range=Range(gte=2023))
    ])
)
```

---

## 13. Vector DB in LangChain

LangChain provides a unified interface across all vector databases.

### Universal Retriever Interface

```python
# Convert any vectorstore to a retriever
retriever = vectorstore.as_retriever(
    search_type="similarity",        # or "mmr" or "similarity_score_threshold"
    search_kwargs={
        "k": 5,                      # number of results
        "filter": {"cat": "legal"},  # optional metadata filter
    }
)

# Use in a chain
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini")

prompt = ChatPromptTemplate.from_template("""
Answer based only on the following context:
{context}

Question: {question}
""")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

answer = chain.invoke("What is the return policy?")
```

### MMR — Maximal Marginal Relevance

Avoids returning redundant results:

```python
# Problem without MMR:
# Top 5 results might all be very similar to each other
# User gets 5 versions of the same chunk

# MMR solution: balance relevance AND diversity
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5,             # final number to return
        "fetch_k": 20,      # fetch this many first
        "lambda_mult": 0.5  # 0=max diversity, 1=max relevance
    }
)
```

### Similarity Score Threshold

Only return results above a minimum confidence:

```python
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.7}
    # Returns only chunks with similarity > 0.7
    # Prevents returning irrelevant chunks when no good match exists
)
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        KEY TAKEAWAYS                             │
│                                                                   │
│  1. Vector DBs store embeddings and answer "find similar" queries│
│                                                                   │
│  2. ANN algorithms (HNSW, IVF) make search fast at scale        │
│                                                                   │
│  3. Start with Chroma (dev) → graduate to Pinecone/Qdrant (prod) │
│                                                                   │
│  4. Always add rich metadata — enables powerful filtering        │
│                                                                   │
│  5. Use MMR retriever to avoid redundant results                 │
│                                                                   │
│  6. Hybrid search (Weaviate) combines semantic + keyword search  │
│                                                                   │
│  7. Set similarity threshold to prevent "no good match" returns  │
└─────────────────────────────────────────────────────────────────┘
```

```
FULL FUNDAMENTALS COMPLETE — START BUILDING

00_rag_fundamentals/
  ├── 01_what_is_rag.md          ✓ RAG concepts, pipeline, use cases
  ├── 02_chunking_strategies.md  ✓ 7 chunking methods, how to choose
  ├── 03_embeddings_explained.md ✓ Vectors, similarity, model selection
  └── 04_vector_databases.md     ✓ ANN algorithms, DB comparison, LangChain

Now proceed to → 01_naive_rag/ to build your first RAG pipeline!
```

---

**Previous ←** [03_embeddings_explained.md](03_embeddings_explained.md)
**Next →** [../01_naive_rag/explanation.md](../01_naive_rag/explanation.md) — Building your first RAG pipeline
