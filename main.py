from fastapi import FastAPI
from pydantic import BaseModel
import matplotlib.pyplot as plt
import random

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.orm import sessionmaker, declarative_base

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- DATABASE ----------
engine = create_engine("sqlite:///./diabetes.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    glucose = Column(Float)
    bmi = Column(Float)
    age = Column(Integer)
    risk = Column(String)

Base.metadata.create_all(bind=engine)

# ---------- MODELS ----------
class UserAuth(BaseModel):
    username: str
    password: str

class PatientData(BaseModel):
    user_id: int
    pregnancies: float
    glucose: float
    blood_pressure: float
    skin_thickness: float
    insulin: float
    bmi: float
    diabetes_pedigree: float
    age: float

class ChatRequest(BaseModel):
    message: str

# ---------- AUTH ----------
@app.post("/signup")
def signup(user: UserAuth):
    db = SessionLocal()
    if db.query(User).filter(User.username == user.username).first():
        return {"msg": "User already exists"}
    db.add(User(username=user.username, password=user.password))
    db.commit()
    return {"msg": "Signup successful"}

@app.post("/login")
def login(user: UserAuth):
    db = SessionLocal()
    u = db.query(User).filter(
        User.username == user.username,
        User.password == user.password
    ).first()
    if not u:
        return {"msg": "Invalid credentials"}
    return {"msg": "Login success", "user_id": u.id}

# ---------- PREDICT ----------
@app.post("/predict")
def predict(data: PatientData):
    score = (data.glucose*0.4 + data.bmi*0.3 + data.age*0.3)/100

    if score < 0.3:
        risk = "Low"
    elif score < 0.7:
        risk = "Medium"
    else:
        risk = "High"

    db = SessionLocal()
    db.add(Patient(
        user_id=data.user_id,
        glucose=data.glucose,
        bmi=data.bmi,
        age=data.age,
        risk=risk
    ))
    db.commit()

    return {"risk_level": risk, "probability": score}

# ---------- GRAPH ----------
@app.post("/graph")
def graph(data: PatientData):
    plt.figure()
    plt.bar(["Glucose","BMI","Age"], [data.glucose,data.bmi,data.age])
    plt.savefig("graph.png")
    plt.close()
    return {"msg":"ok"}

@app.get("/get-graph")
def get_graph():
    return FileResponse("graph.png")

# ---------- SHAP ----------
@app.post("/shap")
def shap(data: PatientData):
    plt.figure()
    plt.barh(["Glucose","BMI","Age"], [data.glucose,data.bmi,data.age])
    plt.savefig("shap.png")
    plt.close()
    return {"msg":"ok"}

@app.get("/get-shap")
def get_shap():
    return FileResponse("shap.png")

# ---------- PIE ----------
@app.get("/risk-chart")
def pie():
    plt.figure()
    plt.pie([30,40,30], labels=["Low","Medium","High"])
    plt.savefig("pie.png")
    plt.close()
    return FileResponse("pie.png")

# ---------- TREND ----------
@app.get("/trend-chart")
def trend():
    db = SessionLocal()
    data = db.query(Patient).all()

    ages = [p.age for p in data]
    glucose = [p.glucose for p in data]

    if len(ages) == 0:
        ages = [10,20,30]
        glucose = [80,120,140]

    plt.figure()
    plt.plot(ages, glucose, marker="o")
    plt.savefig("trend.png")
    plt.close()

    return FileResponse("trend.png")

# ---------- HISTORY ----------
@app.get("/history/{user_id}")
def history(user_id: int):
    db = SessionLocal()
    data = db.query(Patient).filter(Patient.user_id == user_id).all()
    return [
        {"glucose":p.glucose,"bmi":p.bmi,"age":p.age,"risk":p.risk}
        for p in data
    ]

chat_memory = {}

class ChatRequest(BaseModel):
    user_id: int
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    user_id = req.user_id
    msg = req.message.lower()

    if user_id not in chat_memory:
        chat_memory[user_id] = []

    chat_memory[user_id].append(msg)

    # simple replies
    if "hello" in msg:
        return {"reply": "Hello 👋 Ask me about diabetes"}
    elif "diabetes" in msg:
        return {"reply": "Diabetes is high blood sugar condition"}
    elif "glucose" in msg:
        return {"reply": "Normal glucose < 140"}
    elif "bmi" in msg:
        return {"reply": "BMI > 30 increases risk"}
    else:
        return {"reply": "I am working 🙂 Try asking about diabetes, glucose, or BMI"}