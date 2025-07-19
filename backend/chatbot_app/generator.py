import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema.document import Document
from .retriever import retrieve_top_k  # Your function from retriever.py
# from retriever import retrieve_top_k
# ✅ Load environment variables
load_dotenv()

# ✅ Gemini LLM setup
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.3,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# ✅ Format Qdrant results to LangChain-compatible documents
def format_retrieved_docs(retrieved_chunks):
    return [
        Document(
            page_content=hit.payload["text"],
            metadata={"source": hit.payload["filename"]}
        )
        for hit in retrieved_chunks
    ]

# # ✅ Use Gemini to answer using context from retrieved chunks
# def generate_answer(query, retrieved_chunks):
#     documents = format_retrieved_docs(retrieved_chunks)

#     # Join all document text to pass as context
#     context = "\n\n".join([doc.page_content for doc in documents])
#     print("\n📚 Provided Context:\n", context)

#     # Create a custom prompt
#     prompt = f"""
# You are an experienced HR professional at our company. You are confident, conversational, and helpful. Answer the employee's question as if you know the HR policy personally(although you will be taking reference from the documents), without mentioning or referring to any documents. Always be clear, friendly, and informative. 
# Keep the responses short and precise(3-4 lines). check the context carfully and if you are asked numeric data then give appropriate data as listed in the context.
# Context:
# {context}

# Question: {query}
# Answer:"""

#     # Get response from Gemini
#     response = llm.invoke(prompt)
#     print(context)
#     return response, documents  # Return both answer and source documents

def generate_answer(query, retrieved_chunks):
    # Step 1: Rank and format top chunks
    query_keywords = query.lower().split()

    def score(c): return sum(1 for w in query_keywords if w in c.payload["text"].lower())
    # top_chunks = sorted(retrieved_chunks, key=score, reverse=True)[:5]
    documents = format_retrieved_docs(retrieved_chunks)

    # Step 2: Combine chunks into a single context block
    context = "\n\n".join(doc.page_content for doc in documents)
    print(context)
    # Step 3: Compose improved prompt
    prompt = f"""
You are an HR expert. Use ONLY the context below to answer the question.
be polite , clear and concise your answer. answer as if you are the hr yourself and not as if you are reading the document.
in case specific data in numbers is provided , provide the data in your response . in case the query does'nt explicitly mentions the words like category or type use your basic knowledge to navigate through the context.

give the response like an hr is answering . Make sure that the response is not longer than 4 lines.
---
📚 Context:
{context}
---
🧾 Question:
{query}
---
✅ Answer:
"""

    # Step 4: Invoke Gemini (or other LLM)
    response = llm.invoke(prompt)

    # Optional debug:
    print("🧠 Prompt sent to Gemini:\n", prompt)
    print("🧠 Gemini's response:\n", response)

    return response, documents



if __name__ == "__main__":
    query = "what is the lodging rate for hod ?"
    retrieved_docs = retrieve_top_k(query)
    response, sources = generate_answer(query, retrieved_docs)
    print("\n\n------------------------------------------\n\n")
    print("\n🧠 Gemini Response:\n", response)
    print("\n📄 Source documents:")
    for doc in sources:
        print("🔗", doc.metadata['source'])
