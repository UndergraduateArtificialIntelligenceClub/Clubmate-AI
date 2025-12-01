import os

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from pypdf import PdfReader

client = chromadb.PersistentClient(path="./chroma_db")

"""
## collection ideas:

constitution / website # for if the user asks what the club is about

policies

"""


def load_pdf(path: str):
    reader = PdfReader(path)
    return "\n".join(page.extract_text() for page in reader.pages)


def chunk(text: str, size=512, overlap=100):
    # I think 512 is pretty conservative idk could change this. 2,048 is the context size of text-embedding-004 and that's like 1536 tokens

    words = text.split()
    words_len = len(words)

    if words_len <= 512:
        return " ".join(words)

    step = size - overlap

    return [" ".join(words[i : i + size]) for i in range(0, words_len, step)]


def ingest():

    load_dotenv()

    genai_api_key = os.getenv("GENAI_API_KEY")

    if genai_api_key == None:
        raise ValueError("need the genai api key in .env folder")

    google_embedding_function = embedding_functions.GoogleGenaiEmbeddingFunction(
        api_key_env_var=genai_api_key, model_name="text-embedding-004"
    )

    collection = client.get_or_create_collection(
        "club_data", embedding_function=google_embedding_function
    )

    text = load_pdf("./club_data/constitution.pdf")

    chunks = chunk(text)

    for i, ch in enumerate(chunks):
        collection.add(documents=[ch], ids=[f"chunk-{i}"])

    print("ingestion complete")


if __name__ == "__main__":
    ingest()
