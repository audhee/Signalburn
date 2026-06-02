import logging
from typing import List
from sqlalchemy.orm import Session
from app.models.db_models import User, EmergencyContact, MedicalHistory
from app.models.schemas import UserUpdate, EmergencyContactCreate, MedicalHistoryCreate

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def get_user_by_phone(db: Session, phone_number: str) -> User | None:
        return db.query(User).filter(User.phone_number == phone_number).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def upsert_user(db: Session, formatted_phone: str) -> User:
        """Ghost provisions a new user upon OTP login if they do not exist."""
        try:
            user = UserService.get_user_by_phone(db, formatted_phone)
            if not user:
                user = User(phone_number=formatted_phone)
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info(f"Ghost Provisioning: Created new user for {formatted_phone}")
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to upsert user {formatted_phone}: {str(e)}")
            raise

    @staticmethod
    def update_profile(db: Session, user_id: int, profile_data: UserUpdate) -> User | None:
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        update_data = profile_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
            
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def add_emergency_contact(db: Session, user_id: int, contact_data: EmergencyContactCreate) -> EmergencyContact:
        contact = EmergencyContact(
            user_id=user_id,
            name=contact_data.name,
            phone_number=contact_data.phone_number,
            relationship=contact_data.relationship
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact

    @staticmethod
    def set_emergency_contacts(db: Session, user_id: int, contacts: List[EmergencyContactCreate]) -> List[EmergencyContact]:
        db.query(EmergencyContact).filter(EmergencyContact.user_id == user_id).delete()
        new_contacts = [
            EmergencyContact(
                user_id=user_id,
                name=c.name,
                phone_number=c.phone_number,
                relationship=c.relationship
            ) for c in contacts
        ]
        db.add_all(new_contacts)
        db.commit()
        return db.query(EmergencyContact).filter(EmergencyContact.user_id == user_id).all()

    @staticmethod
    def set_medical_history(db: Session, user_id: int, medical_data: MedicalHistoryCreate) -> MedicalHistory:
        """Upserts a 1:1 Medical History record."""
        history = db.query(MedicalHistory).filter(MedicalHistory.user_id == user_id).first()
        
        if not history:
            history = MedicalHistory(user_id=user_id)
            db.add(history)
            
        update_data = medical_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(history, key, value)
            
        db.commit()
        db.refresh(history)
        return history
