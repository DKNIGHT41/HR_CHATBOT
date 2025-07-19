import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from docx import Document  
from pathlib import Path
# Initialize model and client
model = SentenceTransformer("all-MiniLM-L6-v2")
# model = SentenceTransformer("multi-qa-mpnet-base-dot-v1")

# client = QdrantClient(":memory:")
# client = QdrantClient(path="qdrant_local_db/")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # This points to chatbot_app/
QDRANT_PATH = os.path.join(BASE_DIR, "qdrant_local_db")

client = QdrantClient(path=QDRANT_PATH)

COLLECTION_NAME = "hr_docs"


BASE_DIR = Path(__file__).resolve().parent.parent  # Goes to hr_chatbot/
# DOCUMENT_DIR = os.path.join(BASE_DIR, "hr_documents")
DOCUMENT_DIR = os.path.join(BASE_DIR, "Policies")



from docx import Document
import os

from docx import Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table
from docx.text.paragraph import Paragraph

def load_documents(directory=DOCUMENT_DIR):
    docs = []

    for filename in os.listdir(directory):
        if not filename.endswith(".docx") or filename.startswith("~$"):
            continue
        
        filepath = os.path.join(directory, filename)
        doc = Document(filepath)

        last_heading = ""
        for block in doc.element.body:
            if isinstance(block, CT_P):
                para = Paragraph(block, doc)
                text = para.text.strip()
                if text:
                    if para.style.name.startswith("Heading") or text.endswith(":"):
                        last_heading = text
                    else:
                        chunk = f"{last_heading}\n{text}" if last_heading else text
                        docs.append((filename, chunk))

            elif isinstance(block, CT_Tbl):
                table = Table(block, doc)
                rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
                rows = [row for row in rows if any(cell for cell in row)]

                if not rows:
                    continue

                headers = rows[0]
                for row in rows[1:]:
                    parts = []

                    # ✅ Try matching header → value if lengths match
                    if len(row) == len(headers):
                        parts = [
                            f"{header.strip()} is {value.strip()}"
                            for header, value in zip(headers, row)
                            if value.strip()
                        ]
                    elif len(row) == 2:  # 🛡️ fallback for 2-column tables with no header
                        key, val = row
                        if key.strip() and val.strip():
                            parts = [f"{key.strip()} is {val.strip()}"]

                    if parts:
                        sentence = " and ".join(parts) + "."
                        if last_heading:
                            sentence = f"{last_heading}: {sentence}"

                        docs.append((filename, sentence))

                        # 🟡 Print only if the file is "Leave Policy.docx"
                        if filename == "Work Shift Management Policy.docx":
                            print("-------- converted sentences----------")
                            print(sentence)

    return docs



#     return docs

from docx import Document as DocxDocument
# def load_documents(directory=DOCUMENT_DIR):
#     docs = []

#     for filename in os.listdir(directory):
#         if not filename.endswith(".docx") or filename.startswith("~$"):
#             continue

#         filepath = os.path.join(directory, filename)
#         doc = Document(filepath)

#         last_heading = ""
#         for block in doc.element.body:
#             if isinstance(block, CT_P):
#                 para = Paragraph(block, doc)
#                 text = para.text.strip()
#                 if text:
#                     if para.style.name.startswith("Heading") or text.endswith(":"):
#                         last_heading = text
#                     else:
#                         chunk = f"{last_heading}\n{text}" if last_heading else text
#                         docs.append((filename, chunk))

#             elif isinstance(block, CT_Tbl):
#                 table = Table(block, doc)
#                 rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
#                 rows = [row for row in rows if any(cell for cell in row)]

#                 if not rows:
#                     continue

#                 headers = rows[0]
#                 for row in rows[1:]:
#                     parts = []

#                     # ✅ Try matching header → value if lengths match
#                     if len(row) == len(headers):
#                         parts = [
#                             f"{header.strip()} is {value.strip()}"
#                             for header, value in zip(headers, row)
#                             if value.strip()
#                         ]
#                     elif len(row) == 2:  # 🛡️ fallback for 2-column tables with no header
#                         key, val = row
#                         if key.strip() and val.strip():
#                             parts = [f"{key.strip()} is {val.strip()}"]

#                     if parts:
#                         sentence = " and ".join(parts) + "."
#                         if last_heading:
#                             sentence = f"{last_heading}: {sentence}"
#                         docs.append((filename, sentence))

#     return docs


from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client.http.models import PointStruct, VectorParams

def index_documents():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')  

    # 🔄 Recreate collection to ensure clean state
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance="Cosine")
    )

    docs = load_documents()
    points = []
    idx = 0  # Global index across all documents and chunks

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    for filename, text in docs:
        # Get clean chunks
        chunks = text_splitter.split_text(text)

        for chunk_id, chunk in enumerate(chunks):
            if not chunk.strip():
                continue  # Skip empty chunks

            vector = model.encode(chunk).tolist()
            if len(vector) != 384:
                raise ValueError(f"Expected vector of size 384, got {len(vector)}")

            points.append(PointStruct(
                id=idx,
                vector=vector,
                payload={
                    "filename": filename,
                    "text": chunk,
                    "chunk_id": chunk_id,
                    "total_chunks": len(chunks)
                }
            ))
            idx += 1

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    # Inspect some chunks manually
    # for point in points:
    #     if "medical" in point.payload["text"].lower() or "leave" in point.payload["text"].lower():
    #         print(f"\n📄 Indexed Chunk (ID: {point.id})")
    #         print(f"File: {point.payload['filename']}")
    #         print(point.payload["text"])
    #         print("=" * 80)

    print(f"✅ Indexed {len(points)} chunks into Qdrant.")


def retrieve_top_k(query, k=20):
    vector = model.encode(query).tolist()
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=k
    )

    # Show detailed chunk information
    for i, result in enumerate(results):
        payload = result.payload
        score = result.score  # Relevance score from Qdrant
        print(f"Result {i+1}:")
        print(f"Filename   : {payload['filename']}")
        print(f"Chunk ID   : {payload.get('chunk_id', 'N/A')} of {payload.get('total_chunks', 'N/A')}")
        print(f"Score      : {score:.4f}")
        print(f"Chunk Text : {payload['text'][:300]}...")  # Preview first 300 chars
        print("=" * 80)

    return results



if __name__ == "__main__":
    load_documents()
    # index_documents()
    # for filename in os.listdir(DOCUMENT_DIR):
    #     print(f"Found file: '{filename}'")  # ← add this

    print("\n🔍 Testing Retrieval...")
    results = retrieve_top_k("How many medical leaves are allowed in a year?", k=20)
    # results = retrieve_top_k("how many medical leaves do we get in a year?", k=10)

    for i, hit in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"From file: {hit.payload['filename']}")
        print("Content retrieved:\n", hit.payload["text"])  # <-- print full text
