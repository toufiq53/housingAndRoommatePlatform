from fastapi import FastAPI,APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from database import SessionLocal
from typing import Annotated,Optional
from sqlalchemy.orm import Session
from router.auth import get_current_user
from models import Property,Room,RentalRecord,Booking,RoommateProfile
from fastapi.responses import JSONResponse
from datetime import datetime,timedelta


router=APIRouter()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency=Annotated[Session,Depends(get_db)] 
user_dependency=Annotated[dict,Depends(get_current_user)]

class CreateProfile(BaseModel):
    gender: str
    age: int
    occupation: str
    renting_location: str
    budget: int
    description: str

class UpdateProfile(BaseModel):
    gender: str
    age: int
    occupation: str
    renting_location: str
    budget: int
    description: str


@router.post('/create/profile')
def create_roommate_profile(db:db_dependency,user:user_dependency,new_roommate:CreateProfile):
    if user is None:
        raise HTTPException(status_code=401,detail='Failed Authentication')

    existing_profile = db.query(RoommateProfile).filter(RoommateProfile.user_id == user.get('id')).first()
    if existing_profile:
        raise HTTPException(status_code=400,detail='Roommate Profile already exists')
    roommate_model=RoommateProfile(**new_roommate.model_dump(),user_id=user.get('id'))
    # return(property_model)

    db.add(roommate_model)
    db.commit()
    return JSONResponse(status_code=201,content={'message':'Roommate Profile Created succesfully'})

@router.get('/profile/my')
def get_my_roommate_profile(db: db_dependency,user: user_dependency):
    if user is None:
      raise HTTPException(status_code=401,detail='Failed Authentication')
    
    roommate_profile = db.query(RoommateProfile).filter(RoommateProfile.user_id == user.get('id')).first()
    if roommate_profile is None:
        raise HTTPException(status_code=404,detail='Roommate Profile not found')
    
    return roommate_profile

@router.get('/profile/all')
def get_all_profile(user: user_dependency,db: db_dependency):
    if user is None:
      raise HTTPException(status_code=401,detail='Failed Authentication')
    
    profile = db.query(RoommateProfile).all()
    if profile is None:
        raise HTTPException(status_code=404,detail=' Profile not found')
    
    return profile


@router.put('/update/profile')
def update_roommate_profile(user: user_dependency,db: db_dependency,update_roommate: UpdateProfile
):
    if user is None:
        raise HTTPException(status_code=401,detail='Failed Authentication')

    roommate_profile = db.query(RoommateProfile).filter(RoommateProfile.user_id == user.get('id')).first()

    if roommate_profile is None:
        raise HTTPException(status_code=404,detail='Roommate Profile not found')

    for key, value in update_roommate.model_dump().items():
        setattr(roommate_profile, key, value)

    db.commit()

    return JSONResponse(status_code=200,content={'message': 'Roommate Profile updated successfully'})

