from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

data_path = "./data"
DB_FAISS_PATH = "vectorstores/db_faiss"

# Hugging Face token for accessing private models
hf_token = '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'  # Replace with your actual token

# # Load Llama 3 model and tokenizer
#

# Creating vector database
def create_vector_db():
    # Load PDF documents from the directory
    loader = DirectoryLoader(data_path, glob='*.pdf', loader_cls=PyPDFLoader)
    documents = loader.load()

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    text = text_splitter.split_documents(documents)

    # Load the HuggingFace embeddings model
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device': 'cpu'})

    # Create a FAISS vector store from the documents and embeddings
    db = FAISS.from_documents(text, embeddings)

    # Save the FAISS vector store locally
    db.save_local(DB_FAISS_PATH)

if __name__ == '__main__':
    create_vector_db()

    # # Example usage of Llama 3 for generating responses
    # prompt = "Explain the IVF process in simple terms."
    # response = generate_llama3_response(prompt)
    # print(response)
