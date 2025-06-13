from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def load_faiss_index(path):
    try:
        embeddings = OpenAIEmbeddings(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE_URL"),
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        )
        
        index = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
        print(f"✅ Successfully loaded FAISS index from {path}")
        return index
        
    except Exception as e:
        print(f"❌ Failed to load FAISS index from {path}: {e}")
        return None


# ✅ Query documents using RetrievalQA + DeepSeek (via ChatOpenAI)
def query_documents(query: str, path: str = None) -> str:
    vector_path = path or "data/faiss_indexes"
    embeddings = OpenAIEmbeddings(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL"),
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")  # ✅ FIXED
    )
    vectorstore = FAISS.load_local(vector_path, embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    qa_chain = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE_URL"),
            model=os.getenv("OPENAI_API_MODEL")
        ),
        retriever=retriever,
        return_source_documents=False
    )

    return qa_chain.run(query)




