from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.auth_routes import router as auth_router
from app.api.v1.ai_routes import router as voice_router
from app.api.v1.user_routes import router as user_router
from app.api import api_routers

app = FastAPI(title="Arohan Enterprise Backend API", version="2.0.0")

# Configure CORS for React Native frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "http://localhost:8082", "http://localhost:8083", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Answer-Text", "X-Severity", "X-Language-Code", "X-Session-Id",
                    "X-Media-Type", "X-Media-Filename", "X-Chat-Count", "X-Transcription"],
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(voice_router, prefix="/api/v1/ai", tags=["AI Voice"])
app.include_router(user_router, prefix="/api/v1/user", tags=["User Profile"])

# Include additional API routers
for router in api_routers:
    app.include_router(router, prefix="/api", tags=["Test"])

@app.get("/")
def read_root():
    return {"message": "Arohan Enterprise API Backend is running smoothly!"}
