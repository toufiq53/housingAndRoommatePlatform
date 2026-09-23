from fastapi import FastAPI,APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from database import SessionLocal
from typing import Annotated,Optional
from sqlalchemy.orm import Session
from router.auth import get_current_user
from models import Property,Room
from fastapi.responses import JSONResponse


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency=Annotated[dict,Depends(get_current_user)]

class CreateRoom(BaseModel):
    property_id:int
    room_number:int
    rent:int
    type:str
    is_availables:bool
    capacity:int=Field(default=1,gt=0)
    current_members:int

class UpdateRoom(BaseModel):
    room_number:Optional[int]=Field(default=None)
    rent:Optional[int]=Field(default=None)
    type:Optional[str]=Field(default=None)
    is_availables:Optional[bool]=Field(default=None)
    capacity:Optional[int]=Field(default=None)
    current_members:Optional[int]=Field(default=None)  
      


@router.get('/owner/my/specific_room/{room_id}')
def my_specific_room(user:user_dependency,db:db_dependency,room_id:int):
    if user is None or user.get('role')!='owner':
        raise HTTPException(status_code=401,detail='Failed Authentication')
    my_room=db.query(Room).filter(Room.owner_id==user.get('id')).filter(Room.id==room_id).first()
    if my_room is None:
        raise HTTPException(status_code=404,detail='Room Not Found')
    return my_room

    

    
    
@router.post('/owner/create_room')
def create_room(user:user_dependency,db:db_dependency,new_room:CreateRoom):
    if user is None or user.get('role')!='owner':
        raise HTTPException(status_code=401,detail='Failed Authentication')
    property=db.query(Property).filter(Property.id==new_room.property_id).first()
    
    if property.owner_id!=user.get('id'):
        raise HTTPException(status_code=401,detail='Failed Authentication')
    room_model=Room(**new_room.model_dump(),owner_id=user.get('id'))
    db.add(room_model)
    db.commit()
    return JSONResponse(status_code=201,content={'message':'Room Created succesfully'})


@router.put('/owner/update_room/{room_id}')
def update_room(user:user_dependency,db:db_dependency,update_room:UpdateRoom,room_id:int):
    if user is None or user.get('role')!='owner':
        raise HTTPException(status_code=401,detail='Failed Authentication')

    room=db.query(Room).filter(Room.id==room_id).first()
    if room is None:
        raise HTTPException(status_code=404,detail='Room Not Found')
    property=db.query(Property).filter(Property.id==room.property_id).first()

    if property.owner_id!=user.get('id'):
        raise HTTPException(status_code=401,detail='Failed Authentication')

    update_data=update_room.model_dump(exclude_unset=True)

    for key,value in update_data.items():
        setattr(room,key,value)

    db.commit()
    return JSONResponse(status_code=200,content={'message':'Room updated Succesfully'})

@router.delete('/owner/delete_room/{room_id}')
def delete_room(user:user_dependency,db:db_dependency,room_id:int):
    if user is None or user.get('role') not in['owner','admin']:
        raise HTTPException(status_code=401,detail='Failed Authentication')
    room=db.query(Room).filter(Room.id==room_id).first()
    if room is None:
        raise HTTPException(status_code=404,detail='Room Not Found')

    property=db.query(Property).filter(Property.id==room.property_id).first()
  
    if property.owner_id!=user.get('id'):
        raise HTTPException(status_code=401,detail='Failed Authentication')

    db.delete(room) 
    db.commit()     

@router.get('/specific_properties/{property_id}/all_room')
def specific_properties_all_room(db:db_dependency,property_id:int,type:str = None):

    rooms=db.query(Room).filter(Room.property_id==property_id)

    if type:
        rooms = rooms.filter(Room.type.ilike(type))
    return rooms.all()