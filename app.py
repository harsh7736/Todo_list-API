from fastapi import FastAPI, HTTPException,Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List
from pydantic import BaseModel
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
import mysql.connector
class Task(BaseModel):
    id: int = None
    title: str
    description: str = None
    done: bool = False

class User(BaseModel):
    username:str
    password:str

app = FastAPI() 

db=mysql.connector.connect(host='localhost',user='root',passwd='',database='todolist')

pwd_context=CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_pass_hash(password):
    return pwd_context.hash(password)

@app.post("/sign_up")
def sign_up(new_user:User):
    cur=db.cursor()
    cur.execute(f"INSERT INTO users(username,password) VALUES('{new_user.username}','{get_pass_hash(new_user.password)}')")
    db.commit()
    cur.close()
    return {"message": "user added sucessfuly","username":new_user.username,"passsword":get_pass_hash(new_user.password)}


oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
def login(form_data :OAuth2PasswordRequestForm=Depends()):
    username=form_data.username
    password=form_data.password
    if authenticate(username,password):
        return {"access_token":username,"token_type":"bearer"}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

@app.get("/")
def home(token: str=Depends(oauth2_scheme)):
    return {"token":token}


def authenticate(username:str,password:str):
    cur=db.cursor()
    cur.execute(f"""select * from users where username='{username}' ;""",)
    user=cur.fetchall()
    if len(user)==0:
        return False
    else:
        cur.execute(f"""select password from users where username='{username}'""")
        passwd=cur.fetchall()
        cur.close()
        if pwd_context.verify(password,passwd[0][0]):
            return True
        else:
            return False


@app.post("/tasks")
def create_task(task: Task): 
    task_dict = task.dict()
    cur=db.cursor()
    cur.execute(f'''INSERT INTO task (title, description, done) VALUES ('{task_dict["title"]}','{task_dict["description"]}','{task_dict["done"]}')''')
    db.commit()
    cur.close()
    return JSONResponse(content=jsonable_encoder(task), status_code=201)

@app.get("/tasks")
def read_tasks():
    cur=db.cursor()
    cur.execute("SELECT id, title, description, done FROM tasks")
    tasks=cur.fetchall()
    return JSONResponse(content=jsonable_encoder(tasks), status_code=200)
    

@app.get("/tasks/{task_id}", response_model=Task)
def read_task(task_id: int):
    cur=db.cursor()
    cur.execute(f"SELECT id, title, description, done FROM tasks WHERE id={task_id}")
    task=cur.fetchall()
    cur.close()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return JSONResponse(content=jsonable_encoder(task), status_code=200)

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task: Task):
    task_dict = task.dict()
    cur=db.cursor()
    cur.execute(f'''UPDATE tasks SET title='{task_dict["title"]}', description='{task_dict["description"]}', done='{task_dict["done"]}' WHERE id={task_id}''')
    db.commit()
    cur.close()
    return task

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    try:
        cur=db.cursor()
        cur.execute(f'''DELETE FROM tasks WHERE id={task_id}''')
        db.commit()
    except:
        raise HTTPException(status_code=404, detail="Task not found")
    return JSONResponse(content={"message": "Task deleted"}, status_code=200)
        
