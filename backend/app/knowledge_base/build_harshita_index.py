"""
Run once to build Harshita's FAISS index from her first_aid_data.json
Run from: D:\intern\Arohan\backend
Command:  python app/knowledge_base/build_harshita_index.py
"""

import json
import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


def get_first(item, keys, default="Not specified"):
    for k in keys:
        if k in item and item[k]:
            return item[k]
    return default


def list_to_text(value):
    if isinstance(value, list):
        return "\n".join([f"- {v}" for v in value])
    return str(value)


if __name__ == "__main__":
    print("Building Harshita FAISS index...")

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    json_path = os.path.join(os.path.dirname(__file__), "harshita_first_aid.json")
    with open(json_path, "r") as f:
        data = json.load(f)

    documents = []
    for item in data:
        steps_raw = get_first(item, ["steps", "step", "procedure", "immediate_steps"])
        avoid_raw = get_first(item, ["avoid", "avoid_steps", "dont"])

        content = f"""Title: {get_first(item, ['title'])}
Identify: {get_first(item, ['identify'])}
Steps:
{list_to_text(steps_raw)}
Avoid:
{list_to_text(avoid_raw)}
Emergency: {get_first(item, ['emergency'])}
Source: {get_first(item, ['source'])}"""

        documents.append(Document(page_content=content.strip()))

    save_path = os.path.join(os.path.dirname(__file__), "harshita_faiss_index")
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(save_path)

    print(f"✅ Harshita FAISS index built — {len(documents)} docs → {save_path}")