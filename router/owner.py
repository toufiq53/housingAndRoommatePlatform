from fastapi import FastAPI,APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from database import SessionLocal
from typing import Annotated,Optional
from sqlalchemy.orm import Session
from router.auth import get_current_user
from models import Property,Room,RentalRecord,Booking
from fastapi.responses import JSONResponse
from datetime import datetime,timedelta


router=APIRouter()


class PropertyCreate(BaseModel):
    title:str
    description:str=Field(default='',max_length=200)
    type:str
    total_room:int=Field(default=1,ge=1)
    status:str
    district:str
    upazila:str
    address:str

class PropertyUpdate(BaseModel):
    title:Optional[str]=Field(default=None)
    description:Optional[str]=Field(default=None)
    type:Optional[str]=Field(default=None)
    total_room:Optional[int]=Field(default=None)
    available_room:Optional[int]=Field(default=None)
    status:Optional[str]=Field(default=None)
    district:Optional[str]=Field(default=None)
    upazila:Optional[str]=Field(default=None)
    address:Optional[str]=Field(default=None)

class RentalRecords(BaseModel):
    booking_id:int


def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency=Annotated[Session,Depends(get_db)] 
user_dependency=Annotated[dict,Depends(get_current_user)]

@router.get('/owner/my_property')
def my_property(user:user_dependency,db:db_dependency):
    if user is None or user.get('role')!='owner':
        raise HTTPException(status_code=401,detail='Failed Authentication')
    my_property=db.query(Property).filter(Property.owner_id==user.get('id')).all()
    return my_property

@router.get('/owner/specific_property/{property_id}')
def my_specific_property(user:user_dependency,db:db_dependency,property_id:int):
    if user is None or user.get('role')!='owner':
        raise HTTPException(status_code=401,detail='Failed Authentication')
    my_property=db.query(Property).filter(Property.owner_id==user.get('id')).filter(Property.id==property_id).first()
    if my_property is None:
        raise HTTPException(status_code=404,detail='Property Not Found')
    return my_property


    
@router.post('/owner/create_property')
def create_property(db:db_dependency,user:user_dependency,new_property:PropertyCreate):
    if user is None or user.get('role')!='owner':
        raise HTTPException(status_code=401,detail='Failed Authentication')

    # existing_property = db.query(Property).filter( Property.owner_id == user.get('id')).first()

    # if existing_property is not None:
    #     raise HTTPException(status_code=400,detail='You already have a property')
    
    property_model=Property(**new_property.model_dump(),owner_id=user.get('id'),available_room=new_property.total_room)
    # return(property_model)
    db.add(property_model)
    db.commit()

    return JSONResponse(status_code=201,content={'message':'Property Created succesfully'})

@router.put('/owner/update_property/{property_id}')
def update_property(user:user_dependency,db:db_dependency,update_property:PropertyUpdate,property_id:int):
    if user is None or user.get('role')!='owner':
        raise HTTPException(status_code=401,detail='Failed Authentication')

    property=db.query(Property).filter(Property.owner_id==user.get('id')).filter(Property.id==property_id).first()
    if property is None:
        raise HTTPException(status_code=404,detail='Property Not Found')

    update_data=update_property.model_dump(exclude_unset=True)

    for key,value in update_data.items():
        setattr(property,key,value)

    db.commit()
    return JSONResponse(status_code=200,content={'message':'Property Updated Succesfully'})


@router.delete('/owner/delete_property/{property_id}')
def delete_property(user:user_dependency,db:db_dependency,property_id:int):
    if user is None or user.get('role') not in ['admin', 'owner']:
        raise HTTPException(status_code=401,detail='Failed Authentication')
    if user.get('role') == 'admin':
        property = db.query(Property).filter(Property.id == property_id).first()

    else:
        property = db.query(Property).filter(Property.owner_id == user.get('id')).filter(Property.id == property_id).first()

    if property is None:
        raise HTTPException(status_code=404,detail='Property Not Found')

    db.delete(property)
    db.commit()
    return JSONResponse(status_code=200,content={'message':'Property delated Succesfully'})

@router.get('/owner/bookings')
def their_bookings(
    user: user_dependency,
    db: db_dependency
):
    if user is None:
        raise HTTPException( status_code=401, detail='Failed Authentication' )

    properties = db.query(Property).filter( Property.owner_id == user.get('id')).all()

    property_ids = [item.id for item in properties]

    bookings = db.query(Booking).filter( Booking.property_id.in_(property_ids)).all()

    return bookings

@router.post('/owner/create_Records')
def create_records(db:db_dependency,user:user_dependency,rent_rqst:RentalRecords):
    if user is None or user.get('role')!='owner':
        raise HTTPException(status_code=401,detail='Failed Authentication')

    booking=db.query(Booking).filter(
        Booking.id==rent_rqst.booking_id,
        Booking.status=='pending'
    ).first()
    if  booking is None:
        raise HTTPException(status_code=400,detail='Pending booking not found')

    if not booking.payment:
        raise HTTPException(
            status_code=400,
            detail='Payment is required before accepting booking'
        )    

    room=db.query(Room).filter(Room.id==booking.room_id).first()
    if room is None:
        raise HTTPException(status_code=404,detail='Room Not found')
    property=db.query(Property).filter(Property.id==booking.property_id).first()
    if property is None:
        raise HTTPException(status_code=404,detail='property not found')
    if room.owner_id != user.get('id'):
        raise HTTPException(status_code=403,detail='its not your properties room')

    if room.current_members>=room.capacity :
        room.is_availables=False
        raise HTTPException(status_code=400,detail='Room full')
    

    if property.available_room<=0:
        raise HTTPException(status_code=404,detail='room not available')

    rent_days=30
    create_date=datetime.now()

    request_model=RentalRecord(
        user_id=booking.user_id,
        owner_id=user.get('id'),
        property_id=booking.property_id,
        room_id=booking.room_id,
        status='rented',
        payment=True,
        created_at=create_date,
        rent_time=create_date + timedelta(days=rent_days)
    )
    if booking is not None:
        booking.status='accepted'
    room.current_members+=1  
    if room.current_members == 1:
        property.available_room -= 1   
    
    db.add(request_model)
    db.commit()

    return JSONResponse(status_code=201,content={'message':'Room Rent succesfully'})
    