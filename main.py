from fastapi import FastAPI,Depends,HTTPException
from sqlalchemy.orm import Session
from models import Users,Property,Room,Booking
from database import engine ,SessionLocal
from typing import Annotated
from pydantic import BaseModel
from datetime import date
from router import auth,owner,room,roommate
from router.auth import get_current_user
import models
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI()



models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(owner.router)
app.include_router(room.router)
app.include_router(roommate.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency=Annotated[Session,Depends(get_db)] 
user_dependency=Annotated[dict,Depends(get_current_user)]

class PaymentRequest(BaseModel):
    payment: bool

@app.get('/property/all')
def get_all_property(db:db_dependency):
    properties=db.query(Property).all()
    return properties


@app.get('/specific_property/{property_id}')
def specific_property(user:user_dependency,db:db_dependency,property_id:int):
    if user is None:
        raise HTTPException(status_code=401,detail='Failed Authentication')
    property=db.query(Property).filter(Property.id==property_id).first()
    if property is None:
        raise HTTPException(status_code=404,detail='Property Not Found')
    return property


@app.get('/specific_room/{room_id}')
def specific_room(user:user_dependency,db:db_dependency,room_id:int):
    if user is None:
        raise HTTPException(status_code=401,detail='Failed Authentication')
    room=db.query(Room).filter(Room.id==room_id).first()
    if room is None:
        raise HTTPException(status_code=404,detail='Room Not Found')
    return room

@app.post('/booking_room/{room_id}')
def booking_room(user:user_dependency,db:db_dependency,room_id:int):
    if user is None:
        raise HTTPException(status_code=401,detail='failed authentication')
    room=db.query(Room).filter(Room.id==room_id).first()
    if room is None:
        raise HTTPException(status_code=404,detail='Room Not Found')
    if not room.is_availables:raise HTTPException(status_code=400, detail='Room is not available')
    existing_booking=db.query(Booking).filter(Booking.room_id==room_id).first()
    if existing_booking:
        raise HTTPException(status_code=401,detail='You Already Book this room')


    if room.current_members >= room.capacity:
        raise HTTPException(status_code=400, detail='Room full')

    booking_model=Booking(
       room_id=room_id,
       property_id=room.property_id,
       user_id=user.get('id'),
       status='pending',
       payment=False,
       room_number=room.room_number
    )
    db.add(booking_model)
    db.commit()
    return JSONResponse(status_code=201,content={'message':'Room Booking succesfully'})

@app.get('/booking/my')
def my_booking(user:user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=404,detail='Booking not found')
    booking=db.query(Booking).filter(Booking.user_id==user.get('id')).all()
    return booking


@app.delete('/booking_room/cancel/{booking_id}')
def cancel_booking_room(user:user_dependency,db:db_dependency,booking_id:int):
    if user is None:
        raise HTTPException(status_code=401,detail='failed authentication')
    booking=db.query(Booking).filter(Booking.id==booking_id).first()
    if booking is None:
        raise HTTPException(status_code=404,detail='Booking Not Found')
    booking.status='cancelled'
    db.delete(booking) 
    db.commit()   
    return JSONResponse(status_code=201,content={'message':'Booking cancel succesfully'})



@app.put('/booking/payment/{booking_id}')
def booking_payment(user:user_dependency,db:db_dependency,booking_id:int):
    if user is None:
        raise HTTPException(status_code=401,detail='Failed Authentication')

    booking=db.query(Booking).filter( Booking.id==booking_id,Booking.user_id==user.get('id') ).first()

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail='Booking Not Found'
        )

    if booking.status!='pending':
        raise HTTPException(status_code=400,detail='Payment already Done')
    if booking.payment:
        raise HTTPException(status_code=400, detail='Payment already Done')
    booking.payment=True

    db.commit()

    return JSONResponse(status_code=200,
        content={'message':'Payment successful'}
    )



@app.get('/rooms/sort')
def sort_room_by_price( property_id: int,order: str,db: db_dependency):

    if order=="asc":
        rooms=db.query(Room).filter(
            Room.property_id==property_id).order_by(Room.rent.asc()).all()

    elif order=="desc":
        rooms=db.query(Room).filter(Room.property_id == property_id).order_by(Room.rent.desc()).all()

    else:
        raise HTTPException(status_code=400,detail="Invalid order")

    return rooms


@app.get('/properties/search')
def search_property(address: str,db: db_dependency):
    properties = db.query(Property).filter(Property.address.ilike(f"%{address}%")).all()

    return properties



