from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import router as auth_router
from api.voice import router as voice_router

app = FastAPI(title="Arohan Backend API", version="1.0.0")

# Configure CORS for React Native frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(voice_router, prefix="/api/voice", tags=["AI Voice"])

@app.get("/")
def read_root():
    return {"message": "Arohan API Backend is running smoothly!"}
