from app.db.database import SessionLocal

def get_db():
    """
    Generator function to provide a database session to FastAPI endpoints.
    Ensures that the session is closed cleanly after the payload completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
