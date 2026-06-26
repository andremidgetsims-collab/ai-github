#!/usr/bin/env python3
"""
QA Vector DB Builder
Downloads ISTQB & OWASP PDFs -> Chunks -> Embeds -> Saves -> Tests search.
Run once to build the Senior QA Agent's knowledge base.

Required env vars:
  OPENAI_API_KEY  — used for text-embedding-3-small
"""

import os
import sys
import requests
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# ==========================================
# CONFIGURATION
# ==========================================
PDF_DOWNLOAD_DIR = Path("./qa_pdfs")
VECTOR_DB_DIR = "./qa_vector_db"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_MODEL = "text-embedding-3-small"

PDF_URLS = [
    {
        "url": "https://www.istqb.org/downloads/send/2-foundation-level-documents/9-istqb-foundation-level-syllabus-2018-v4-0.html",
        "filename": "istqb_foundation_syllabus.pdf",
    },
    {
        "url": "https://owasp.org/www-project-top-ten/2021/",
        "filename": "owasp_top_10_2021.pdf",
    },
    {
        "url": "https://github.com/OWASP/wstg/releases/download/v4.2/wstg-v4.2.pdf",
        "filename": "owasp_testing_guide_v4.pdf",
    },
]

REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
REQUEST_TIMEOUT = 30


# ==========================================
# STEPS
# ==========================================
def download_pdfs() -> list[str]:
    """Download all PDFs from PDF_URLS into PDF_DOWNLOAD_DIR."""
    PDF_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = []

    print("STEP 1: Downloading PDFs...")
    for item in PDF_URLS:
        url = item["url"]
        local_path = PDF_DOWNLOAD_DIR / item["filename"]

        if local_path.exists():
            print(f"  Already exists: {local_path.name}")
            downloaded.append(str(local_path))
            continue

        print(f"  Downloading: {local_path.name}...")
        try:
            response = requests.get(
                url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            local_path.write_bytes(response.content)
            print(f"  Downloaded: {local_path.name}")
            downloaded.append(str(local_path))
        except Exception as e:
            print(f"  Failed to download {local_path.name}: {e}")

    print(f"PDFs ready in: {PDF_DOWNLOAD_DIR}\n")
    return downloaded


def chunk_pdfs(pdf_files: list[str]) -> list:
    """Load PDFs and split them into overlapping text chunks."""
    print("STEP 2: Loading and chunking PDFs...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
        length_function=len,
    )
    all_chunks = []

    for pdf_path in pdf_files:
        name = Path(pdf_path).name
        print(f"  Processing: {name}")
        try:
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            chunks = splitter.split_documents(docs)
            for chunk in chunks:
                chunk.metadata["source"] = name
                chunk.metadata["source_full_path"] = pdf_path
            all_chunks.extend(chunks)
            print(f"    Created {len(chunks)} chunks")
        except Exception as e:
            print(f"    Error processing {name}: {e}")

    print(f"Total chunks created: {len(all_chunks)}\n")
    return all_chunks


def create_vector_db(chunks: list, api_key: str) -> Chroma:
    """Embed chunks and persist to Chroma."""
    print("STEP 3: Generating embeddings and building vector database...")
    print("   (This may take a few minutes depending on PDF size)")

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=api_key)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_DIR,
    )
    vectorstore.persist()

    print(f"Vector DB saved to: {VECTOR_DB_DIR}\n")
    return vectorstore


def test_search(api_key: str) -> None:
    """Load the persisted DB from disk and run sample queries."""
    print("STEP 4: Running test search...")

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=api_key)
    store = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)

    queries = [
        "What is boundary value analysis in testing?",
        "How to test for SQL injection vulnerabilities?",
        "What is the difference between verification and validation?",
    ]

    for query in queries:
        print(f"\n  Query: '{query}'")
        results = store.similarity_search(query, k=3)
        if results:
            preview = results[0].page_content[:150].replace("\n", " ")
            print(f"  Top result: {preview}...")
            print(f"  Source: {results[0].metadata.get('source', 'Unknown')}")
        else:
            print("  No results found.")

    print("\nTest search complete. Vector DB is ready.\n")


# ==========================================
# MAIN
# ==========================================
def main() -> None:
    print("=" * 60)
    print("SENIOR QA AGENT — VECTOR DB BUILDER")
    print("=" * 60)

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        print("  export OPENAI_API_KEY=<your-key>")
        sys.exit(1)

    pdf_files = download_pdfs()
    if not pdf_files:
        print("ERROR: No PDFs available. Check URLs or place files in ./qa_pdfs")
        sys.exit(1)

    chunks = chunk_pdfs(pdf_files)
    if not chunks:
        print("ERROR: No chunks generated. Verify PDF files are readable.")
        sys.exit(1)

    create_vector_db(chunks, api_key)
    test_search(api_key)

    print("Done. Load the DB in your agent with:")
    print(f"  Chroma(persist_directory='{VECTOR_DB_DIR}', embedding_function=...)")


if __name__ == "__main__":
    main()
