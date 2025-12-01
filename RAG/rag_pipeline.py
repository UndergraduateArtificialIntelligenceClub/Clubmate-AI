import os

import chromadb
from google import genai

client = chromadb.Client()
collection = client.get_collection("club_data")
gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)  # In prod, will want to make this happen in a central location but this is just PoC


async def answer(query: str):
    results = collection.query(query_texts=[query], n_results=4)

    docs = results["documents"]

    if not docs or not docs[0]:
        return "Could not retrieve data to answer you :c"

    context = "\n\n".join(docs[0])

    prompt = f"""
    Use ONLY the context to answer the question.
    If you don't know, say you don't know.

    Context:
    {context}

    Question: {query}
    """

    response = await gemini_client.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    return response.text
