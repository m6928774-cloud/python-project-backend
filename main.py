from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import numpy as np
import os

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# DB
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base

# Auth
from passlib.context import CryptContext

# Graph & SHAP
import matplotlib.pyplot as plt
import shap

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# ---------------------------
# APP
# ---------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# DATABASE
# ---------------------------
DATABASE_URL = "sqlite:///./diabetes.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ---------------------------
# MODELS
# ---------------------------
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

# ---------------------------
# AUTH
# ---------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------
# MODEL
# ---------------------------
model = pickle.load(open("model.pkl", "rb"))
explainer = shap.Explainer(model)

# ---------------------------
# INPUT
# ---------------------------
class PatientData(BaseModel):
    pregnancies: int
    glucose: float
    blood_pressure: float
    skin_thickness: float
    insulin: float
    bmi: float
    diabetes_pedigree: float
    age: int

# ---------------------------
# HOME
# ---------------------------
@app.get("/")
def home():
    return {"message": "API running"}

# ---------------------------
# SIGNUP
# ---------------------------
@app.post("/signup")
def signup(username: str, password: str):
    db = SessionLocal()

    hashed = pwd_context.hash(password)
    user = User(username=username, password=hashed)

    db.add(user)
    db.commit()

    return {"message": "User created"}

# ---------------------------
# LOGIN
# ---------------------------
@app.post("/login")
def login(username: str, password: str):
    db = SessionLocal()

    user = db.query(User).filter(User.username == username).first()

    if not user or not pwd_context.verify(password, user.password):
        return {"error": "Invalid credentials"}

    return {"message": "Login success", "user_id": user.id}

# ---------------------------
# PREDICT
# ---------------------------
@app.post("/predict")
def predict(data: PatientData):
    db = SessionLocal()

    input_data = np.array([[ 
        data.pregnancies,
        data.glucose,
        data.blood_pressure,
        data.skin_thickness,
        data.insulin,
        data.bmi,
        data.diabetes_pedigree,
        data.age
    ]])

    prediction = model.predict(input_data)[0]
    probability = model.predict_proba(input_data)[0][1]

    # Risk
    if probability < 0.3:
        risk = "Low"
    elif probability < 0.7:
        risk = "Medium"
    else:
        risk = "High"

    # Save history
    patient = Patient(
        user_id=1,
        glucose=data.glucose,
        bmi=data.bmi,
        age=data.age,
        risk=risk
    )
    db.add(patient)
    db.commit()

    return {
        "prediction": int(prediction),
        "risk_level": risk,
        "probability": float(probability)
    }

# ---------------------------
# HISTORY
# ---------------------------
@app.get("/history")
def history():
    db = SessionLocal()
    data = db.query(Patient).all()

    return [
        {
            "glucose": p.glucose,
            "bmi": p.bmi,
            "age": p.age,
            "risk": p.risk
        } for p in data
    ]

# ---------------------------
# GRAPH
# ---------------------------
@app.post("/graph")
def graph(data: PatientData):
    plt.figure()
    plt.bar(["Glucose", "BMI", "Age"], [data.glucose, data.bmi, data.age])
    plt.savefig("graph.png")
    plt.close()
    return {"msg": "graph done"}

@app.get("/get-graph")
def get_graph():
    return FileResponse("graph.png")

# ---------------------------
# SHAP
# ---------------------------
@app.post("/shap")
def shap_explain(data: PatientData):
    input_data = np.array([[ 
        data.pregnancies,
        data.glucose,
        data.blood_pressure,
        data.skin_thickness,
        data.insulin,
        data.bmi,
        data.diabetes_pedigree,
        data.age
    ]])

    shap_values = explainer(input_data)

    plt.figure()
    shap.plots.waterfall(shap_values[0], show=False)
    plt.savefig("shap_plot.png", bbox_inches='tight')
    plt.close()

    return {"msg": "shap done"}

@app.get("/get-shap")
def get_shap():
    return FileResponse("shap_plot.png")

# ---------------------------
# PDF
# ---------------------------
@app.post("/generate-report")
def pdf(data: PatientData):
    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    content = [
        Paragraph("Diabetes Report", styles['Title']),
        Paragraph(f"Age: {data.age}", styles['Normal']),
        Paragraph(f"BMI: {data.bmi}", styles['Normal']),
        Paragraph(f"Glucose: {data.glucose}", styles['Normal'])
    ]

    doc.build(content)

    return {"msg": "pdf done"}

@app.get("/get-report")
def get_pdf():
    return FileResponse("report.pdf")