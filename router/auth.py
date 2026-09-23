from fastapi import FastAPI ,APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from datetime import timedelta,datetime,timezone
from sqlalchemy.orm import Session
from typing import Annotated,Optional
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from jose import jwt
from fastapi.responses import JSONResponse

router=APIRouter()

bcrypt_context=CryptContext(schemes=['bcrypt'],deprecated='auto')
OAuth2_bearer=OAuth2PasswordBearer(tokenUrl='login')
SECRET_KEY='1db9723f202bc0dcfe4347b82494095689a3223a1dd94908ddbd2d9177dbfdc5'
ALGORITHM='HS256'


def authenticate_user(username,password,db):
    user=db.query(Users).filter(Users.username==username).first()
    if user is None:
        return False
    if bcrypt_context.verify(password,user.hash_password):
        return user
    return False

def create_access_token(username:str,user_id:int,role:str,expires_delta:timedelta):
    encode={'sub':username,'id':user_id,'role':role}
    expires=datetime.now(timezone.utc)+expires_delta
    encode.update({'exp':expires})
    return jwt.encode(encode,SECRET_KEY,algorithm=ALGORITHM)

def get_current_user(token:Annotated[str,Depends(OAuth2_bearer)]):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username:str=payload.get('sub')
        user_id:int=payload.get('id')
        role:str=payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=404,detail='User not found')
        return {'username':username,'id':user_id,'role':role}
    except:
        raise HTTPException(status_code=404,detail='User not Found')

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency=Annotated[Session,Depends(get_db)] 
user_dependency=Annotated[dict,Depends(get_current_user)]


class CreateUsers(BaseModel):
    email:str
    username:str
    firstname:str
    lastname:str
    password:str
    role:str

class UpdateUser(BaseModel):
    email : Optional[str] = Field(default=None)
    username : Optional[str] = Field(default=None)
    firstname : Optional[str] = Field(default=None)
    lastname : Optional[str]= Field(default=None)
    
class UpdatePassword(BaseModel):
    current_password : str
    new_password: str


@router.post('/createuser')
def create_users(db:db_dependency,new_user:CreateUsers):
    user_model=Users(
        email=new_user.email,
        username=new_user.username,
        firstname=new_user.firstname,
        lastname=new_user.lastname,
        hash_password=bcrypt_context.hash(new_user.password),
        role=new_user.role,
    )
    existing_user = db.query(Users).filter(Users.username == new_user.username).first()
    existing_mail = db.query(Users).filter(Users.email == new_user.email).first()
    
    if existing_user:
        raise HTTPException(
        status_code=400,
        detail="Username already exists"
        )
    if existing_mail:
        raise HTTPException(
        status_code=400,
        detail="Email already exists"
        )
    
    db.add(user_model)
    db.commit()
    return JSONResponse(status_code=201, content={'message' : 'User created successfully'})
    
    

@router.post('/login')
def login_user(db:db_dependency,form_data: Annotated[OAuth2PasswordRequestForm,Depends()]):
    user= authenticate_user(form_data.username,form_data.password,db)

    if not user:
        raise HTTPException(status_code=401,detail="Failed Authentication")
        
    token=create_access_token(user.username,user.id,user.role,timedelta(hours=24))
    return {'access_token':token,'token_type':'bearer'}


@router.put('/edituser')
def update_user(user: user_dependency, db : db_dependency, update_user : UpdateUser):

    if user is None: 
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    user = db.query(Users).filter(Users.id == user.get('id')).first()
    
    update_data = update_user.model_dump(exclude_unset=True)

    for key,value in update_data.items():
        setattr(user,key,value)
    
    db.commit()
    return JSONResponse(status_code=200, content={'message' : 'User updated successfully'})


@router.put('/passwordchange')
def update_password(user: user_dependency, db : db_dependency, update_password : UpdatePassword):

    if user is None: 
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    user = db.query(Users).filter(Users.id == user.get('id')).first()
    
    if not bcrypt_context.verify(update_password.current_password, user.hash_password):
        raise HTTPException(status_code=401, detail='Wrong Password')

    user.hash_password = bcrypt_context.hash(update_password.new_password)

    db.add(user)
    db.commit()
    return JSONResponse(status_code=200, content={'message' : 'Password updated successfully'})


@router.get('/user')
def get_user_details(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    current_user = db.query(Users).filter(Users.id == user.get('id')).first()
    if current_user is None:
        raise HTTPException(status_code=404, detail='User not found')
    
    return {
        'id': current_user.id,
        'email': current_user.email,
        'username': current_user.username,
        'firstname': current_user.firstname,
        'lastname': current_user.lastname,
        'role': current_user.role
    }