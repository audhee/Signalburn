from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.auth_routes import router as auth_router
from app.api.v1.ai_routes import router as voice_router
from app.api.v1.user_routes import router as user_router

app = FastAPI(title="Arohan Enterprise Backend API", version="2.0.0")

# Configure CORS for React Native frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(voice_router, prefix="/api/v1/ai", tags=["AI Voice"])
app.include_router(user_router, prefix="/api/v1/user", tags=["User Profile"])

@app.get("/")
def read_root():
    return {"message": "Arohan Enterprise API Backend is running smoothly!"}
