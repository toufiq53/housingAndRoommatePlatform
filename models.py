
from database import Base
from sqlalchemy import Column,Integer,Float,String,Boolean,ForeignKey,DateTime
from datetime import datetime



class Users(Base):
    __tablename__='users'

    id=Column(Integer, primary_key=True,index=True)
    username=Column(String,unique=True)
    email=Column(String,unique=True)
    firstname=Column(String)
    lastname=Column(String)
    hash_password=Column(String)
    created_at=Column(DateTime, default=datetime.now())
    role=Column(String)


class Property(Base):
    __tablename__='property'

    id=Column(Integer,primary_key=True,index=True)
    owner_id=Column(Integer,ForeignKey('users.id'))
    title=Column(String)
    description=Column(String)
    type =Column(String)
    total_room=Column(Integer)
    available_room=Column(Integer)
    status=Column(String)           
    created_at=Column(DateTime,default=datetime.now())
    district=Column(String)
    upazila=Column(String)
    address=Column(String)
    cover_img=Column(String,nullable=True)


class Room(Base):
    __tablename__='room'

    id=Column(Integer,primary_key=True,index=True)
    property_id=Column(Integer,ForeignKey('property.id'))
    owner_id = Column(Integer, ForeignKey('users.id'))
    room_number=Column(Integer)
    rent=Column(Integer)
    type=Column(String)
    is_availables=Column(Boolean)
    capacity=Column(Integer)
    current_members=Column(Integer)
    cover_img=Column(String,nullable=True)



class Booking(Base):
    __tablename__='booking'

    id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey('users.id'))
    property_id=Column(Integer,ForeignKey('property.id'))
    room_id=Column(Integer,ForeignKey('room.id'))
    room_number=Column(Integer,ForeignKey('room.room_number'))
    status=Column(String,default='pending')
    payment=Column(Boolean,default=False)
    created_date=Column(DateTime,default=datetime.now)
    move_in_date=Column(DateTime,nullable=True)



class RentalRecord(Base):
    __tablename__='rental_record'

    id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey('users.id'))
    owner_id=Column(Integer,ForeignKey('users.id'))
    property_id=Column(Integer,ForeignKey('property.id'))
    room_id=Column(Integer,ForeignKey('room.id'))
    status=Column(String,default='pending')
    payment=Column(Boolean,default=False)
    created_at=Column(DateTime,default=datetime.now)
    rent_time=Column(DateTime)


class RoommateProfile(Base):
    __tablename__ = 'roommate_profile'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    gender = Column(String)
    age = Column(Integer)
    occupation = Column(String)
    renting_location = Column(String)  
    budget = Column(Integer)
    description = Column(String)
    status = Column(String, default='active')

    

