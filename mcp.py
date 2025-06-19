from fastapi import FastAPI
from model import Registration
import csv
import os

app = FastAPI()
CSV_FILE = "registrations.csv"

@app.post("/register")
def register_user(reg: Registration):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Name", "Email", "DOB"])
        writer.writerow([reg.name, reg.email, reg.dob])
    return {"message": "Registration successful"}

@app.get("/registrations")
def get_registrations():
    if not os.path.isfile(CSV_FILE):
        return []
    with open(CSV_FILE, mode="r") as file:
        reader = csv.DictReader(file)
        return list(reader)