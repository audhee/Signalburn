print("👋 RUNNING MAIN.PY SUCCESSFULLY!")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
import anthropic
import torch
from transformers import AutoTokenizer, AutoModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🧠 Step 2: Loading clean Transformers model into memory...")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
print("✅ Step 2 SUCCESS: Model loaded successfully!")

print("📂 Step 3: Connecting to ChromaDB...")
client = chromadb.PersistentClient(path="./medical_db")
collection = client.get_or_create_collection("medical_knowledge")
print("✅ Step 3 SUCCESS: Connected to ChromaDB collection!")

print("🔑 Step 4: Initializing Anthropic client backend...")
# REMEMBER: Replace the text below with your actual secret Claude API key string!
claude = anthropic.Anthropic(api_key="YOUR_ANTHROPIC_API_KEY")
print("✅ Step 4 SUCCESS: Anthropic client ready!")


# Helper function to generate embeddings without sentence_transformers
def get_embedding(text: str):
    inputs = tokenizer(text, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        model_output = model(**inputs)
    # Mean Pooling
    attention_mask = inputs['attention_mask']
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    embedding = (sum_embeddings / sum_mask).tolist()[0]
    return embedding


class Query(BaseModel):
    question: str


@app.post("/chat")
def chat(query: Query):
    user_question = query.question.lower().strip()

    # 1. IMMEDIATE GUARDRAIL: Intercept chronic/out-of-bounds queries
    chronic_conditions = ["cancer", "diabetes", "tumor", "chemotherapy", "heart disease", "stroke treatment"]
    if any(disease in user_question for disease in chronic_conditions):
        return {"answer": "⚠️ This condition falls outside of immediate trekker first-aid. No verified emergency guidelines found in our knowledge base."}

    # 2. Vector DB Query matching using clean embedding function
    embedding = get_embedding(query.question)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=5
    )

    # 3. STRICT BOUNDARY CHECK: Check the match distance score
    if results["distances"] and results["distances"][0][0] > 1.2:
        return {"answer": "⚠️ This condition falls outside of immediate trekker first-aid. No verified emergency guidelines found in our knowledge base."}

    # If it passes the checks, prepare context for Claude
    context = "\n\n".join(results["documents"][0])

    # 4. Generate the structured output from verified documents only
    response = claude.messages.create(
        model="claude-3-5-sonnet-20241022", 
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""You are a medical first aid assistant.
Answer the question using ONLY the context below.
If not found, say 'I don't have information on that, please consult a doctor.'

Context:
{context}

Question: {query.question}"""
        }]
    )
    return {"answer": response.content[0].text}


# --- WEB SERVER ENGINE ---
if __name__ == "__main__":
    print("🚀 ALL SYSTEMS CLEAR! BOOTING UP UVICORN WEB SERVER NOW...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)