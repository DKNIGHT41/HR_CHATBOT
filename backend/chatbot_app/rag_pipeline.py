from .retriever import retrieve_top_k
from .generator import generate_answer

def answer_user_query(query):
    retrieved_docs = retrieve_top_k(query)
    final_answer, sources = generate_answer(query, retrieved_docs)
    return final_answer, sources