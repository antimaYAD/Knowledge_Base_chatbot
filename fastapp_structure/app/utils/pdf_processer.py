
import os
import re
from typing import List
from pathlib import Path

# from dotenv import load_dotenv
from pypdf import PdfReader
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
# from langchain_openai import OpenAIEmbeddings
from langchain.embeddings import OpenAIEmbeddings  # ✅
from dotenv import load_dotenv
import os
import openai

load_dotenv()


# Dynamically resolve base project directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Function to parse PDF and extract text content
def parse_pdf(file_path: str) -> List[str]:
    with open(file_path, 'rb') as file:
        pdf = PdfReader(file)
        output = []
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)  # Merge hyphenated words
            text = re.sub(r"(?<!\n\s)\n(?!\s\n)", " ", text.strip())  # Fix newlines
            text = re.sub(r"\n\s*\n", "\n\n", text)  # Remove multiple newlines
            output.append(text)
        return output

# Function to convert text content into documents
def text_to_docs(text: List[str], source: str) -> List[Document]:
    page_docs = [Document(page_content=page) for page in text]
    for i, doc in enumerate(page_docs):
        doc.metadata["page"] = i + 1
        doc.metadata["source_pdf"] = source

    doc_chunks = []
    for doc in page_docs:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            chunk_overlap=0,
        )
        chunks = text_splitter.split_text(doc.page_content)
        for i, chunk in enumerate(chunks):
            chunk_doc = Document(
                page_content=chunk,
                metadata={
                    "page": doc.metadata["page"],
                    "chunk": i,
                    "source_pdf": doc.metadata["source_pdf"],
                    "source": f"{doc.metadata['source_pdf']} (Page {doc.metadata['page']}-{i})"
                },
            )
            doc_chunks.append(chunk_doc)
    return doc_chunks

# Save processed PDF to FAISS index directory
def save_pdf_to_faiss(file_path: str, api_key: str, faiss_folder: str):
    file_path = Path(file_path)
    faiss_folder = Path(faiss_folder)

    file_name = file_path.name
    faiss_path = faiss_folder / file_name.replace(".pdf", "")
    
    print(f"\n📄 Processing: {file_name}")

    try:
        text = parse_pdf(str(file_path))
        doc_chunks = text_to_docs(text, source=file_name)

        if doc_chunks:
            print(f"✅ Loaded {len(doc_chunks)} chunks from {file_name}")

            # embeddings = OpenAIEmbeddings(openai_api_key=api_key,model = "gpt-3.5turbo")
            # embeddings = OpenAIEmbeddings() 
            embeddings = OpenAIEmbeddings(openai_api_key=api_key, model=os.getenv("OPENAI_API_MODEL")

,base_url=os.getenv("OPENAI_API_BASE_URL"))
            index = FAISS.from_documents(doc_chunks, embeddings)

            faiss_path.mkdir(parents=True, exist_ok=True)
            index.save_local(str(faiss_path))

            print(f"💾 Saved FAISS index for {file_name} to {faiss_path}\n")
        else:
            print(f"⚠️ No chunks generated for {file_name}")

    except Exception as e:
        import traceback
        print(f"❌ Error processing {file_name}:\n{traceback.format_exc()}")

# Main function to process all PDFs in a folder
def process_all_pdfs(pdf_folder: str, faiss_folder: str, api_key: str):
    pdf_folder = Path(pdf_folder)
    faiss_folder = Path(faiss_folder)
    faiss_folder.mkdir(parents=True, exist_ok=True)

    for file_path in pdf_folder.glob("*.pdf"):
        save_pdf_to_faiss(str(file_path), api_key, str(faiss_folder))

# Run script
if __name__ == "__main__":
    PDF_FOLDER_PATH = BASE_DIR / "data" / "pdfs"
    FAISS_FOLDER_PATH = BASE_DIR / "data" / "faiss_indexes"

    PDF_FOLDER_PATH.mkdir(parents=True, exist_ok=True)
    FAISS_FOLDER_PATH.mkdir(parents=True, exist_ok=True)
    openai.api_key = "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"


    # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # openai= "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"
   

    process_all_pdfs(PDF_FOLDER_PATH, FAISS_FOLDER_PATH, openai.api_key)




