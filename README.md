\# Multi-PDF AI Knowledge Assistant — V2



A production-oriented \*\*Retrieval-Augmented Generation (RAG)\*\* system that allows users to upload PDF documents and ask questions grounded in their content, while also supporting general-knowledge queries.



\---



\## Overview



Version 2 rebuilds the original PDF chatbot into a structured RAG pipeline focused on:



\- Better retrieval quality

\- Document grounding

\- Source tracking

\- Workspace isolation

\- Semantic chunking

\- PDF text cleanup

\- Retrieval diagnostics

\- Performance benchmarking



The system processes uploaded PDFs into semantic chunks, generates embeddings using Sentence Transformers, indexes them with FAISS, retrieves the most relevant chunks using similarity search, and uses Gemini to generate the final response.



\---



\## V2 Architecture



```text

&#x20;                   User Question

&#x20;                        |

&#x20;                        v

&#x20;                 Query Embedding

&#x20;                        |

&#x20;                        v

&#x20;                  FAISS Retrieval

&#x20;                        |

&#x20;                        v

&#x20;              Similarity Threshold

&#x20;                     (0.45)

&#x20;                        |

&#x20;               +--------+--------+

&#x20;               |                 |

&#x20;               v                 v

&#x20;       Relevant Chunks      No Relevant

&#x20;               |                 |

&#x20;               v                 v

&#x20;       Document Context     General Query

&#x20;               |                 |

&#x20;               v                 v

&#x20;             Gemini <------------+

&#x20;               |

&#x20;               v

&#x20;             Answer

&#x20;               |

&#x20;               v

&#x20;       Sources / Page Metadata

Retrieval-First Flow

Question

&#x20;  |

&#x20;  v

FAISS Retrieval

&#x20;  |

&#x20;  +---- Relevant ----> Document RAG + Gemini

&#x20;  |

&#x20;  +---- Not Relevant -> General Gemini



V2 uses retrieval-first routing instead of making an additional LLM call just to classify the query.



This reduces unnecessary API usage and keeps query routing deterministic.



Key Features

1\. PDF Processing

PDF text extraction using PyPDF

Page-level document representation

Text normalization and cleanup

Detection and removal of repeated PDF artifacts

Removal of repeated headers and page-number noise

Preservation of meaningful document content

Semantic sentence-based chunking

Configurable chunk size and sentence overlap

2\. Semantic Chunking



V2 uses semantic sentence-based chunking instead of relying only on fixed character boundaries.



Default Configuration

Parameter	Value

Target chunk size	1500 characters

Sentence overlap	2 sentences



Each chunk stores metadata including:



Document ID

Filename

Page number

Chunk index

Character count

Sentence count

3\. Vector Retrieval



V2 uses Sentence Transformers and FAISS for semantic document retrieval.



Retrieval Pipeline

Document Chunks

&#x20;     |

&#x20;     v

Sentence Transformer

&#x20;     |

&#x20;     v

Embeddings

&#x20;     |

&#x20;     v

L2 Normalization

&#x20;     |

&#x20;     v

FAISS IndexFlatIP

&#x20;     |

&#x20;     v

Similarity Search

&#x20;     |

&#x20;     v

Threshold Filtering

&#x20;     |

&#x20;     v

Top-K Results

Retrieval Configuration

Parameter	Value

Embedding model	all-MiniLM-L6-v2

FAISS index	IndexFlatIP

Default Top-K	5

Maximum Top-K	20

Similarity threshold	0.45



Embeddings are L2-normalized before FAISS search, allowing inner-product similarity to act as cosine similarity.



4\. Retrieval-First RAG



V2 does not use an LLM request solely for query classification.



Instead, retrieval itself determines whether relevant document context exists.



Question

&#x20;  |

&#x20;  v

FAISS Retrieval

&#x20;  |

&#x20;  +-------------------+

&#x20;  |                   |

&#x20;  v                   v

Relevant             Not Relevant

Chunks               Chunks

&#x20;  |                   |

&#x20;  v                   v

Document RAG        General Gemini

&#x20;  |

&#x20;  v

Gemini

&#x20;  |

&#x20;  v

Answer



This approach:



Avoids an additional LLM routing request

Reduces API usage

Reduces unnecessary latency

Keeps routing deterministic

Uses retrieval confidence as the routing signal

5\. Document Grounding



When relevant document chunks are retrieved:



Gemini receives the retrieved document context.

Outside knowledge is explicitly disallowed.

Unsupported information should not be invented.

The system provides a fallback when sufficient information cannot be found in the uploaded documents.



The document context includes:



Filename

Page number

Similarity score

Retrieved chunk text



This makes the generation process traceable to retrieved document content.



6\. General Knowledge Handling



When no document chunks pass the similarity threshold, the system can answer the question using Gemini without document context.



Example:



Question:

What is the capital of Japan?



Retrieved chunks:

0



Sources:

\[]



Answer:

Tokyo



This allows the assistant to handle both document-based and general-knowledge questions.



7\. Source Tracking



Responses include document source metadata such as:



filename - Page number



For example:



fastapi\_tutorial.pdf - Page 6

fastapi\_tutorial.pdf - Page 8



This makes generated answers traceable to the uploaded document.



8\. Workspace Isolation



Each chat/workspace maintains its own document and FAISS state.



The system uses a chat\_id to associate uploaded documents and retrieval state with a specific workspace.



This prevents documents from different workspaces from being mixed during retrieval.



9\. Duplicate Document Handling



Existing documents are removed before re-indexing the same document ID.



This prevents duplicate chunks from being created when a document is reprocessed.



Tech Stack

Backend

Technology	Purpose

Python	Core backend language

FastAPI	API framework

Uvicorn	ASGI server

PyPDF	PDF text extraction

Sentence Transformers	Text embeddings

FAISS	Vector similarity search

Pydantic	Data validation and models

NLTK	Sentence tokenization

Google Gemini API	LLM generation

Frontend

Technology	Purpose

React	Frontend framework

TypeScript	Type-safe frontend development

Vite	Frontend build and development tooling

Project Structure

Multi-PDF AI Knowledge Assistant

│

├── backend/

│   │

│   ├── app/

│   │   ├── api/

│   │   │

│   │   ├── chunking/

│   │   │   ├── base\_chunker.py

│   │   │   └── semantic\_chunker.py

│   │   │

│   │   ├── config/

│   │   │   └── settings.py

│   │   │

│   │   ├── models/

│   │   │

│   │   ├── services/

│   │   │   ├── embedding\_services.py

│   │   │   ├── pdf\_service.py

│   │   │   ├── rag\_services.py

│   │   │   └── work\_spacemanager.py

│   │   │

│   │   └── utils/

│   │       └── text\_utils.py

│   │

│   ├── benchmark\_baseline.py

│   ├── retrieval\_calibration.py

│   ├── retrieval\_diagnostic.py

│   ├── main.py

│   └── requirements.txt

│

├── frontend/

│

└── README.md

API



The backend is built with FastAPI.



Main Endpoints

GET  /

GET  /documents

POST /upload

POST /query



The API uses a chat\_id to isolate documents and retrieval state between workspaces.



Health Check

GET /



Returns the API status and version information.



List Documents

GET /documents?chat\_id=<CHAT\_ID>



Returns documents associated with a workspace.



Upload PDF

POST /upload?chat\_id=<CHAT\_ID>



Uploads and indexes PDF documents for a specific workspace.



Query Documents

POST /query?chat\_id=<CHAT\_ID>



Processes a user question through the retrieval-first RAG pipeline.



Running Locally

Prerequisites



Make sure the following are installed:



Python

Node.js

npm

Git

Backend Setup



Navigate to the backend directory:



cd backend



Install Python dependencies:



pip install -r requirements.txt



Create a .env file in the backend directory:



GEMINI\_API\_KEY=your\_api\_key\_here



Start the FastAPI server:



uvicorn main:app --reload



The backend runs at:



http://127.0.0.1:8000

Frontend Setup



Open another terminal and navigate to the frontend directory:



cd frontend



Install dependencies:



npm install



Start the development server:



npm run dev



The frontend will be available at the URL provided by Vite.



Retrieval Diagnostics



V2 includes dedicated scripts for evaluating retrieval quality and system performance.



Retrieval Diagnostic



Run:



python retrieval\_diagnostic.py --pdf "path/to/file.pdf" --question "Your question"



The diagnostic reports:



PDF page count

Extracted chunk count

Query embedding time

FAISS search time

Similarity scores

Retrieved chunks

Chunk metadata

Retrieval ranking



Example:



python retrieval\_diagnostic.py --pdf "C:\\path\\fastapi\_tutorial.pdf" --question "How do I create a FastAPI application?"

Retrieval Calibration



The calibration utility is used to evaluate retrieval behavior and similarity scores across documents and queries.



Example:



python retrieval\_calibration.py --fastapi-pdf "path/to/fastapi.pdf" --javascript-pdf "path/to/javascript.pdf"



The calibration process helps determine an appropriate similarity threshold for retrieval.



V2 uses a similarity threshold of:



0.45

Baseline Benchmark



The baseline benchmark measures ingestion and query performance.



Example:



python benchmark\_baseline.py --pdf "path/to/file.pdf" --chat-id "CHAT\_ID" --queries "Question 1" "Question 2"



The benchmark measures:



PDF ingestion time

Memory usage

Query latency

Average latency

Median latency

P95 latency

Minimum latency

Maximum latency

V2 Benchmark



The final V2 benchmark was performed using:



PDF:

fastapi\_tutorial.pdf



Number of queries:

5

Ingestion Performance

Metric	Result

Chunks indexed	117

Ingestion time	12.116 sec

Memory before	32.94 MB

Memory after	37.00 MB

Memory increase	4.06 MB

Query Latency

Metric	Result

Average	5.832 sec

Median	6.552 sec

P95	6.967 sec

Minimum	2.664 sec

Maximum	7.860 sec



Note: The benchmark contains only five queries, so the P95 value should be treated as a reported benchmark statistic rather than a statistically robust production percentile.



Benchmark Queries

Query 1

According to the uploaded document, what is FastAPI?

Result



Successfully retrieved relevant document sources and generated a document-grounded answer.



Query 2

What are the main features of FastAPI?

Result



Successfully retrieved relevant document sources and generated a document-grounded answer.



Query 3

What is Uvicorn used for?

Result



Successfully retrieved relevant document sources and generated a document-grounded answer.



Query 4

How do I create a FastAPI application?

Result



Successfully retrieved relevant document sources and generated a document-grounded answer.



Query 5

What is the capital of Japan?

Result



No document chunks passed the similarity threshold.



Sources:

\[]



Answer:

Tokyo



This demonstrates the general-knowledge fallback when the uploaded documents do not contain relevant information.



Benchmark Summary



The benchmark demonstrated that V2 can handle both document-grounded and general-knowledge queries using a retrieval-first architecture.



Document Questions



The four FastAPI-related questions successfully retrieved relevant document chunks and returned answers grounded in the uploaded PDF.



General Question



The unrelated question about Japan did not retrieve document sources and was answered through the general Gemini path.



Document Query

&#x20;     |

&#x20;     v

Relevant FAISS Results

&#x20;     |

&#x20;     v

Document Context

&#x20;     |

&#x20;     v

Gemini

&#x20;     |

&#x20;     v

Grounded Answer

General Query

&#x20;     |

&#x20;     v

No Relevant FAISS Results

&#x20;     |

&#x20;     v

General Gemini

&#x20;     |

&#x20;     v

General Answer

Performance Characteristics



V2 diagnostic measurements showed that vector retrieval contributes very little to overall query latency compared with LLM generation.



Typical retrieval measurements during testing were approximately:



Operation	Typical Time

Query embedding	\~30–35 ms

FAISS search	<1 ms



The primary latency contribution comes from Gemini response generation rather than FAISS retrieval.



Configuration



Important V2 configuration values include:



Configuration	Value

Embedding model	all-MiniLM-L6-v2

Target chunk size	1500 characters

Sentence overlap	2 sentences

Default Top-K	5

Maximum Top-K	20

Similarity threshold	0.45

Gemini model	gemini-3.6-flash

Version 2 Improvements



Compared with the initial prototype, V2 introduces:



Multi-PDF document handling

Workspace isolation

Semantic chunking

Improved PDF text cleanup

Repeated PDF artifact detection

FAISS vector search

L2-normalized embeddings

Calibrated similarity threshold

Retrieval diagnostics

Source/page tracking

Document-grounded generation

General knowledge fallback

Retrieval-first query routing

Duplicate document handling

Performance benchmarking

Memory measurement

Latency measurement

Security



Do not commit API keys or environment files.



Use a local .env file:



.env



Example:



GEMINI\_API\_KEY=your\_api\_key\_here



Keep .env excluded from Git.



Never hardcode API keys directly into source code.



Limitations



The current V2 implementation has some limitations:



FAISS indexes are maintained in memory.

Restarting the backend clears the in-memory retrieval index.

The current benchmark contains only five queries.

P95 latency is therefore not statistically robust.

PDF extraction quality depends on the structure of the source PDF.

Complex tables and image-based PDFs may require specialized extraction.

Gemini API availability and latency can affect total response time.

Future Improvements



Potential future improvements include:



Persistent vector storage

Hybrid keyword + semantic retrieval

Reranking

Better table extraction

OCR support for scanned PDFs

Streaming responses

Improved citation presentation

Production deployment

Automated evaluation datasets

Retrieval quality metrics

Answer quality evaluation

Persistent workspace storage

Version

Version: 2.0.0



License

This project is intended for educational, experimentation, and portfolio purposes.


