from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.models.schemas import UserResponse, UserUpdate, EmergencyContactCreate, EmergencyContactResponse, MedicalHistoryCreate, MedicalHistoryResponse
from typing import List
from app.services.user.user_service import UserService
from app.api.dependencies import get_current_user
from app.models.db_models import User

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch the complete nested profile of the currently logged-in user."""
    return UserService.get_user_by_id(db, current_user.id)

@router.patch("/profile", response_model=UserResponse)
def update_my_profile(profile_data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update basic user profile details (Name, Age, Blood Type)."""
    return UserService.update_profile(db, current_user.id, profile_data)

@router.post("/contacts", response_model=EmergencyContactResponse)
def add_new_contact(contact_data: EmergencyContactCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Add a new emergency contact to the list."""
    return UserService.add_emergency_contact(db, current_user.id, contact_data)

@router.put("/contacts", response_model=List[EmergencyContactResponse])
def set_all_contacts(contacts_data: List[EmergencyContactCreate], current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Overwrite all emergency contacts for the user with a fresh list."""
    return UserService.set_emergency_contacts(db, current_user.id, contacts_data)

@router.put("/medical", response_model=MedicalHistoryResponse)
def set_my_medical_history(medical_data: MedicalHistoryCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Upsert the 1:1 medical history record."""
    return UserService.set_medical_history(db, current_user.id, medical_data)
