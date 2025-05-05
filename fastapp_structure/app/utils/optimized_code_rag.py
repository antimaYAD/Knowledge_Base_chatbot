# from langchain.vectorstores import FAISS
# from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
# from langchain.llms import OpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.llms import OpenAI
import os


def load_faiss_index(path):
    embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)


def query_documents(query: str, path: str = None) -> str:
    vector_path = path or "data/faiss_indexes"
    embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    # vectorstore = FAISS.load_local(vector_path, embeddings)
    vectorstore = FAISS.load_local(vector_path, embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
    # result_docs = retriever.invoke(query)


    # retriever = vectorstore.as_retriever()

    qa_chain = RetrievalQA.from_chain_type(
        llm=OpenAI(openai_api_key=os.getenv("OPENAI_API_KEY")),
        retriever=retriever,
        return_source_documents=False
    )

    return qa_chain.run(query)
