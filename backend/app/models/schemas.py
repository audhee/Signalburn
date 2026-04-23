from pydantic import BaseModel, conint
from typing import List, Optional
from datetime import datetime

# ================================
# Emergency Contact Validations
# ================================
class EmergencyContactBase(BaseModel):
    name: str
    phone_number: str
    relationship: Optional[str] = None

class EmergencyContactCreate(EmergencyContactBase):
    pass

class EmergencyContactResponse(EmergencyContactBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# ================================
# Medical History Validations
# ================================
class MedicalHistoryBase(BaseModel):
    conditions: List[str] = []
    other: Optional[str] = None

class MedicalHistoryCreate(MedicalHistoryBase):
    pass

class MedicalHistoryResponse(MedicalHistoryBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# ================================
# User Validations
# ================================
class UserBase(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None

class UserUpdate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    phone_number: str
    created_at: datetime
    
    # Nested Relationships
    emergency_contacts: List[EmergencyContactResponse] = []
    medical_history: Optional[MedicalHistoryResponse] = None

    class Config:
        from_attributes = True
