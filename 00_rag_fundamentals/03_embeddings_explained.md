# 03 · Embeddings Explained

> **Embeddings are the bridge between human language and machine understanding.**
> They convert words, sentences, and documents into numerical vectors that capture meaning.

---

## Table of Contents

1. [What is an Embedding?](#1-what-is-an-embedding)
2. [Why Embeddings Work — The Geometry of Meaning](#2-why-embeddings-work--the-geometry-of-meaning)
3. [From Word2Vec to Transformers — A Brief History](#3-from-word2vec-to-transformers--a-brief-history)
4. [How Modern Embeddings are Created](#4-how-modern-embeddings-are-created)
5. [Similarity Metrics](#5-similarity-metrics)
6. [Dense vs Sparse Embeddings](#6-dense-vs-sparse-embeddings)
7. [Popular Embedding Models](#7-popular-embedding-models)
8. [How to Choose an Embedding Model](#8-how-to-choose-an-embedding-model)
9. [Embeddings in LangChain](#9-embeddings-in-langchain)
10. [Common Pitfalls](#10-common-pitfalls)

---

## 1. What is an Embedding?

An **embedding** is a fixed-length list of floating-point numbers (a vector) that represents the **semantic meaning** of a piece of text.

```
TEXT → EMBEDDING MODEL → VECTOR

"The cat sat on the mat"   →  [0.21, -0.43, 0.87, 0.12, -0.65, ...]
                                ◀──────── 1536 numbers ──────────▶

"A feline rested on a rug" →  [0.19, -0.41, 0.89, 0.10, -0.63, ...]
                                ◀──────── 1536 numbers ──────────▶

"Stock market hit record"  →  [-0.82, 0.34, -0.21, 0.91, 0.44, ...]
                                ◀──────── 1536 numbers ──────────▶
```

Notice:
- "The cat sat on the mat" and "A feline rested on a rug" have **very similar vectors** → same meaning
- "Stock market hit record" has a **very different vector** → unrelated meaning

This is the magic: **semantically similar text maps to nearby points in vector space.**

---

## 2. Why Embeddings Work — The Geometry of Meaning

Embeddings exist in a **high-dimensional space** (typically 384–3072 dimensions). While we can't visualize 1536 dimensions, we can understand the key properties:

### Semantic Proximity

```
2D PROJECTION (simplified from 1536D)

                    Animal World
                    ┌─────────────────────────────┐
                    │         ●cat                │
                    │    ●kitten                  │
                    │         ●feline             │
  Similarity  high  │    ●dog        ●puppy       │
                    │         ●wolf               │
                    └─────────────────────────────┘
                                  
                    Finance World  
                    ┌─────────────────────────────┐
                    │  ●stock  ●equity            │
  Similarity  high  │       ●portfolio            │
                    │  ●dividend   ●market        │
                    └─────────────────────────────┘
                    
              ◀──────────── Far apart ────────────▶
                 Animals                Finance
```

### The Famous Analogy Test

Embeddings capture **relationships**, not just similarity:

```
king - man + woman ≈ queen

Vector("king") - Vector("man") + Vector("woman")
≈ Vector("queen")

This arithmetic works because:
  king → man relationship = royalty + male
  Subtract male, add female → royalty + female = queen

Other analogies that work:
  Paris - France + Italy ≈ Rome
  walked - walk + run ≈ ran
  biggest - big + cold ≈ coldest
```

---

## 3. From Word2Vec to Transformers — A Brief History

```
EMBEDDING MODEL EVOLUTION TIMELINE

2013          2014      2017          2018          2019-Now
  │             │         │             │              │
Word2Vec     GloVe    Transformers   BERT/GPT    Modern Encoders
  │             │         │             │              │
  ▼             ▼         ▼             ▼              ▼
Context-     Global    Attention    Context-      Sentence-level
free         stats     mechanism    aware words   embeddings
embeddings             invented                   (S-BERT, etc.)

Each word had    Better but    Changed        Same word,      Full semantic
ONE vector       still static  everything     different       understanding
"bank" = same    representation               vectors by
whether river                                 context
or money
```

### The Context Problem

```
STATIC EMBEDDINGS (Word2Vec/GloVe) — Problem

"I went to the bank to deposit money"
"We picnicked on the river bank"

bank → [0.34, -0.12, 0.78, ...]   ← SAME vector for both!
       No way to distinguish financial bank from river bank

CONTEXTUAL EMBEDDINGS (BERT/Transformers) — Solution

"I went to the bank to deposit money"
bank → [0.12, 0.89, -0.34, ...]   ← Financial context

"We picnicked on the river bank"
bank → [0.78, -0.23, 0.91, ...]   ← Geographic context

Different vectors → correct meaning captured!
```

---

## 4. How Modern Embeddings are Created

Modern embedding models for RAG are typically **Transformer-based encoders** trained with **contrastive learning**.

### Training Process

```
CONTRASTIVE LEARNING — Training an Embedding Model

Step 1: Create training pairs from the data

Positive pair (similar):
  "What is the capital of France?" ←→ "Paris is the capital of France"

Negative pair (dissimilar):
  "What is the capital of France?" ←→ "The recipe requires 2 cups of flour"

Step 2: During training, push vectors together/apart

Before training:
  Query:    [0.3,  0.7, -0.2]
  Positive: [0.4,  0.5, -0.1]  ← should be close
  Negative: [0.4,  0.5, -0.1]  ← currently too close!

After training:
  Query:    [0.3,  0.7, -0.2]
  Positive: [0.31, 0.68, -0.19]  ← pushed closer ✓
  Negative: [-0.8, 0.1,  0.9 ]   ← pushed apart ✓

Step 3: The model learns to encode meaning, not just syntax
```

### The CLS Token (BERT-style)

```
BERT ENCODER ARCHITECTURE

Input:  [CLS] The cat sat on the mat [SEP]
           │    │   │   │   │  │   │
           ▼    ▼   ▼   ▼   ▼  ▼   ▼
       ┌─────────────────────────────────┐
       │     Transformer Encoder Layers  │
       │     (attention across all tokens)│
       └─────────────────────────────────┘
           │    │   │   │   │  │   │
           ▼    ▼   ▼   ▼   ▼  ▼   ▼
Output: [CLS] cat  sat  on  the mat [SEP]
           │
           ▼
      [0.21, -0.43, 0.87, ...]  ← Sentence embedding!
      (CLS token aggregates full sentence meaning)
```

---

## 5. Similarity Metrics

Once you have vectors, you need to measure how similar two vectors are.

### Cosine Similarity — The Most Common

```
COSINE SIMILARITY

Measures the ANGLE between two vectors (ignores magnitude)
Range: -1 (opposite) to 1 (identical)
RAG typical threshold: > 0.7 is relevant

           ▲
     v2 ●  │
           │  ← Small angle → HIGH similarity
     v1 ●──┤
           │
           └────────────────────────▶

           ▲
           │      ● v3
           │    ↗
           │  ← Large angle → LOW similarity
     v1 ●──┤
           │
           └────────────────────────▶

Formula:
  cos(θ) = (v1 · v2) / (|v1| × |v2|)

Example:
  v1 = [1, 0]
  v2 = [0.9, 0.1]   cos similarity ≈ 0.994  (very similar)
  v3 = [0, 1]       cos similarity = 0.0    (orthogonal = unrelated)
  v4 = [-1, 0]      cos similarity = -1.0   (opposite)
```

### Euclidean Distance (L2)

```
EUCLIDEAN DISTANCE

Measures the STRAIGHT-LINE DISTANCE between two points in space

         ● v1 (1, 2)
         │
         │  d = √((3-1)² + (4-2)²) = √8 ≈ 2.83
         │
         ● v2 (3, 4)

Range: 0 (identical) to ∞
Lower = more similar

When to use:
- If your vectors are normalized to unit length → same as cosine
- FAISS uses L2 by default
- Less intuitive for text similarity
```

### Dot Product

```
DOT PRODUCT

v1 · v2 = Σ(v1[i] × v2[i])

- Fast to compute
- Only valid when vectors have the same magnitude
- OpenAI recommends normalized embeddings → dot product ≈ cosine

Example:
  v1 = [0.6, 0.8]
  v2 = [0.8, 0.6]
  dot = (0.6×0.8) + (0.8×0.6) = 0.48 + 0.48 = 0.96
```

### Comparison

```
┌────────────────────┬──────────────┬──────────────────────────────┐
│ Metric             │ Range        │ Best For                      │
├────────────────────┼──────────────┼──────────────────────────────┤
│ Cosine Similarity  │ -1 to 1      │ Most text similarity tasks    │
│ Euclidean (L2)     │ 0 to ∞       │ Low-dimensional spaces        │
│ Dot Product        │ -∞ to ∞      │ When vectors are normalized   │
│ Manhattan (L1)     │ 0 to ∞       │ Sparse vectors                │
└────────────────────┴──────────────┴──────────────────────────────┘
```

---

## 6. Dense vs Sparse Embeddings

There are two fundamental types of vector representations:

### Dense Embeddings (Neural)

```
DENSE VECTOR — Every dimension has a value

text-embedding-3-small output (1536 dimensions):
[0.021, -0.432, 0.871, 0.123, -0.654, 0.234, 0.891, -0.012, ...]
  d1     d2     d3     d4     d5      d6     d7     d8

Characteristics:
- Every dimension is non-zero
- Dimensions have no direct interpretable meaning
- Captures semantic meaning
- ~1536 floats × 4 bytes = ~6KB per vector
- Excellent for semantic similarity
```

### Sparse Embeddings (BM25 / TF-IDF style)

```
SPARSE VECTOR — Mostly zeros (only present words get values)

Vocabulary size: 50,000 words
BM25 representation of "photosynthesis plants sunlight":

[0, 0, 0, ..., 3.2, 0, 0, ..., 1.8, 0, ..., 2.1, 0, 0, ...]
                ▲              ▲             ▲
          "photosynthesis"  "plants"     "sunlight"
               word 4521   word 12034   word 31892

50,000 dimensions, but only 3 non-zero values!
Stored as: {4521: 3.2, 12034: 1.8, 31892: 2.1}

Characteristics:
- Highly sparse (99.9%+ zeros)
- Dimensions directly represent vocabulary words
- Excellent for keyword matching
- Fails on synonyms ("car" ≠ "automobile")
```

### Hybrid — Best of Both Worlds

```
HYBRID RETRIEVAL (Module 03 in this repo)

Query: "What are the best electric vehicles in 2024?"

Dense Search → finds semantically related docs
   "Tesla Model 3 review" (synonym: EV = electric vehicle)
   "Battery technology advances" (semantic relation)

Sparse Search → finds exact keyword matches
   "electric vehicles 2024 comparison" (exact words)
   "EV market 2024 report" (keyword match)

RRF (Reciprocal Rank Fusion) combines both:
   Dense rank:  [doc_A=1, doc_C=2, doc_B=3, doc_D=4]
   Sparse rank: [doc_C=1, doc_A=2, doc_D=3, doc_B=4]

   Combined:    [doc_A: 1.5, doc_C: 1.5, doc_D: 3.5, doc_B: 3.5]
   Final order: doc_A, doc_C (tied), doc_D, doc_B
```

---

## 7. Popular Embedding Models

### OpenAI

```
┌─────────────────────────────┬──────────┬────────────┬───────────┐
│ Model                       │ Dims     │ Max Tokens │ Cost      │
├─────────────────────────────┼──────────┼────────────┼───────────┤
│ text-embedding-3-small      │ 1536     │ 8191       │ $0.02/1M  │
│ text-embedding-3-large      │ 3072     │ 8191       │ $0.13/1M  │
│ text-embedding-ada-002      │ 1536     │ 8191       │ $0.10/1M  │
└─────────────────────────────┴──────────┴────────────┴───────────┘
Recommendation: text-embedding-3-small (best value for RAG)
```

### Google

```
┌──────────────────────────────┬──────────┬────────────┬───────────┐
│ Model                        │ Dims     │ Max Tokens │ Cost      │
├──────────────────────────────┼──────────┼────────────┼───────────┤
│ text-embedding-004           │ 768      │ 2048       │ $0.025/1M │
│ text-multilingual-embedding  │ 768      │ 2048       │ $0.025/1M │
└──────────────────────────────┴──────────┴────────────┴───────────┘
```

### Open Source / Local

```
┌────────────────────────┬──────────┬────────────┬───────────────────┐
│ Model                  │ Dims     │ Max Tokens │ Notes             │
├────────────────────────┼──────────┼────────────┼───────────────────┤
│ all-MiniLM-L6-v2       │ 384      │ 256        │ Fast, good quality│
│ all-mpnet-base-v2      │ 768      │ 384        │ Higher quality    │
│ nomic-embed-text-v1.5  │ 768      │ 8192       │ Long context local│
│ bge-large-en-v1.5      │ 1024     │ 512        │ Top open source   │
│ e5-mistral-7b-instruct │ 4096     │ 4096       │ Strongest local   │
└────────────────────────┴──────────┴────────────┴───────────────────┘
```

### MTEB Leaderboard (as of 2024)

The **Massive Text Embedding Benchmark (MTEB)** is the standard for comparing embedding models:

```
MTEB AVERAGE SCORE (higher is better)

e5-mistral-7b-instruct   ████████████████████████ 64.9  (7B params, slow)
text-embedding-3-large   ███████████████████████  64.6  (API, fast)
bge-large-en-v1.5        █████████████████████    63.5  (open source)
text-embedding-3-small   ████████████████████     62.3  (API, cheapest)
all-mpnet-base-v2        ████████████████         57.8  (small, local)
all-MiniLM-L6-v2         ██████████████           56.3  (tiny, fastest)
```

---

## 8. How to Choose an Embedding Model

```
EMBEDDING MODEL SELECTION GUIDE

Question 1: Can you use an API (cost/privacy OK)?
├─ YES → Go to Question 2
└─ NO  → Use local: nomic-embed-text or bge-large-en-v1.5

Question 2: Is multilingual support required?
├─ YES → text-multilingual-embedding-002 (Google)
│        or multilingual-e5-large (HuggingFace)
└─ NO  → Go to Question 3

Question 3: What's your priority?
├─ Cost     → text-embedding-3-small (OpenAI)
├─ Quality  → text-embedding-3-large (OpenAI)
└─ Speed    → text-embedding-3-small (fastest API)

Question 4: Long documents (>512 tokens)?
├─ YES → nomic-embed-text-v1.5 (8K tokens, local)
│        or text-embedding-3-small (8K tokens, API)
└─ NO  → Any model above works

CRITICAL RULE: Use the SAME model for indexing AND querying!
              Never mix models — vectors are incompatible.
```

---

## 9. Embeddings in LangChain

### OpenAI Embeddings

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    # dimensions=512  # optional: reduce dimensions to save space
)

# Embed a single query
query_vector = embeddings.embed_query("What is photosynthesis?")
print(len(query_vector))  # 1536

# Embed multiple documents (more efficient)
texts = ["Photosynthesis uses sunlight", "Plants produce oxygen"]
doc_vectors = embeddings.embed_documents(texts)
print(len(doc_vectors))    # 2
print(len(doc_vectors[0])) # 1536
```

### Google Embeddings

```python
from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004"
)
```

### Local / HuggingFace Embeddings

```python
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},   # or "cuda" for GPU
    encode_kwargs={"normalize_embeddings": True}
)
```

### Visualizing Similarity (Practical Example)

```python
import numpy as np
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()

sentences = [
    "The dog barked at the mailman",
    "A canine howled at the postman",    # similar
    "The cat meowed softly",             # somewhat related
    "The stock market crashed today",    # unrelated
]

vectors = embeddings.embed_documents(sentences)

def cosine_similarity(v1, v2):
    v1, v2 = np.array(v1), np.array(v2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# Compare sentence 0 to all others
for i, sentence in enumerate(sentences[1:], 1):
    sim = cosine_similarity(vectors[0], vectors[i])
    print(f"Similarity with '{sentence[:30]}...': {sim:.4f}")

# Expected output:
# Similarity with 'A canine howled at the postman': 0.9234
# Similarity with 'The cat meowed softly...':        0.7821
# Similarity with 'The stock market crashed today':  0.4123
```

---

## 10. Common Pitfalls

### Pitfall 1 — Mixing Embedding Models

```
WRONG:
  Indexing:  embeddings = OpenAIEmbeddings("text-embedding-ada-002")
  Querying:  embeddings = OpenAIEmbeddings("text-embedding-3-small")

  Result: Completely wrong retrieval! Vectors are in different spaces.

RIGHT:
  Always use the exact same model_name for both phases.
  Store model name in config / environment variable.
```

### Pitfall 2 — Exceeding Max Token Limit

```
text-embedding-3-small max: 8191 tokens
If your chunk = 10,000 tokens → silently truncated to 8191

Result: End of chunk is lost from the embedding

Fix: Ensure chunk_size < model's token limit
     Use token-based chunking (not character-based)
```

### Pitfall 3 — Not Normalizing Vectors

```
If using dot product similarity (e.g., FAISS with IndexFlatIP):
  Vectors must be unit-normalized for correct results

Fix:
  from langchain_huggingface import HuggingFaceEmbeddings
  embeddings = HuggingFaceEmbeddings(
      encode_kwargs={"normalize_embeddings": True}
  )
```

### Pitfall 4 — Embedding Cost Surprise

```
Typical RAG corpus: 1,000 documents × 5 pages × 500 tokens = 2.5M tokens

text-embedding-3-small cost: $0.02 per 1M tokens
Total indexing cost: $0.05  (cheap!)

But: If you re-index every day for a year:
$0.05 × 365 = $18/year

Optimization: Cache embeddings in vector DB — only re-embed new/changed docs
```

### Pitfall 5 — Query vs Document Embedding Mismatch

```
Some models use different encoders for queries vs documents!

WRONG:
  Both query and document embedded with embed_documents()

RIGHT (for asymmetric models like E5):
  Documents: embeddings.embed_documents(docs)   # "passage: " prefix
  Queries:   embeddings.embed_query(query)      # "query: " prefix

LangChain handles this automatically — always use:
  embed_query() for queries
  embed_documents() for documents
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        KEY TAKEAWAYS                             │
│                                                                   │
│  1. Embeddings convert text → vectors that capture meaning       │
│                                                                   │
│  2. Semantically similar text → geometrically nearby vectors     │
│                                                                   │
│  3. Cosine similarity is the standard measure for text search    │
│                                                                   │
│  4. Dense = semantic understanding; Sparse = keyword matching    │
│                                                                   │
│  5. Default pick: text-embedding-3-small (OpenAI) — best value  │
│                                                                   │
│  6. ALWAYS use the same model for indexing AND querying          │
│                                                                   │
│  7. For production: consider local models for privacy/cost       │
└─────────────────────────────────────────────────────────────────┘
```

---

**Previous ←** [02_chunking_strategies.md](02_chunking_strategies.md)
**Next →** [04_vector_databases.md](04_vector_databases.md) — Where embeddings live and how they are searched
