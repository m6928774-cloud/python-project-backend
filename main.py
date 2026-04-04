from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import numpy as np
import os

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# Graphs
import matplotlib.pyplot as plt

# SHAP
import shap

app = FastAPI()

# Load model
model = pickle.load(open("model.pkl", "rb"))

# SHAP explainer
explainer = shap.Explainer(model)

# Input schema
class PatientData(BaseModel):
    pregnancies: int
    glucose: float
    blood_pressure: float
    skin_thickness: float
    insulin: float
    bmi: float
    diabetes_pedigree: float
    age: int

# Home
@app.get("/")
def home():
    return {"message": "Advanced Diabetes Prediction API Running"}

# -------------------------------
# 🔥 PREDICTION + ANALYSIS
# -------------------------------
@app.post("/predict")
def predict(data: PatientData):
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

    # Risk level
    if probability < 0.3:
        risk = "Low"
    elif probability < 0.7:
        risk = "Medium"
    else:
        risk = "High"

    # Risk factors
    factors = []
    if data.glucose > 140:
        factors.append("High glucose")
    if data.bmi > 30:
        factors.append("High BMI")
    if data.age > 45:
        factors.append("Age risk")

    # Advice
    if risk == "High":
        advice = "Consult doctor immediately"
        medicines = ["Metformin", "Insulin therapy"]
    elif risk == "Medium":
        advice = "Improve lifestyle and monitor"
        medicines = ["Lifestyle changes"]
    else:
        advice = "Healthy lifestyle"
        medicines = ["No medication needed"]

    return {
        "prediction": int(prediction),
        "risk_level": risk,
        "probability": float(probability),
        "risk_factors": factors,
        "advice": advice,
        "possible_treatments": medicines
    }

# -------------------------------
# 📄 PDF REPORT
# -------------------------------
@app.post("/generate-report")
def generate_report(data: PatientData):
    file_path = "report.pdf"

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph("Diabetes Risk Report", styles['Title']))
    content.append(Paragraph(f"Age: {data.age}", styles['Normal']))
    content.append(Paragraph(f"BMI: {data.bmi}", styles['Normal']))
    content.append(Paragraph(f"Glucose: {data.glucose}", styles['Normal']))

    content.append(Paragraph(" ", styles['Normal']))
    content.append(Paragraph("Maintain healthy lifestyle and consult doctor.", styles['Normal']))

    doc.build(content)

    return {"message": "PDF generated"}

# -------------------------------
# 📊 GRAPH
# -------------------------------
@app.post("/graph")
def generate_graph(data: PatientData):
    values = [data.glucose, data.bmi, data.age]
    labels = ["Glucose", "BMI", "Age"]

    plt.figure()
    plt.bar(labels, values)
    plt.title("Health Indicators")
    plt.savefig("graph.png")

    return {"message": "Graph generated"}

# -------------------------------
# 🧬 SHAP EXPLAINABILITY
# -------------------------------
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

    return {"message": "SHAP explanation generated"}

# -------------------------------
# 📂 VIEW FILES INFO (DEBUG)
# -------------------------------
@app.get("/files")
def list_files():
    return {"files": os.listdir()}