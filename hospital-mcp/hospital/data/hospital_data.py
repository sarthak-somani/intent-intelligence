"""Rich mock data for Hospital Guardian MCP Server."""

from __future__ import annotations

# ── Patients ──────────────────────────────────────────────────────────
PATIENTS: dict[str, dict] = {
    "P001": {
        "id": "P001",
        "name": "Rajesh Kumar",
        "age": 58,
        "gender": "Male",
        "blood_type": "B+",
        "conditions": ["Type 2 Diabetes", "Hypertension", "Chronic Kidney Disease Stage 3"],
        "medications": ["Metformin 500mg", "Amlodipine 5mg", "Losartan 50mg"],
        "allergies": ["Penicillin", "Sulfonamides"],
        "emergency_contact": "+91-9876543210",
        "doctor_id": "DOC001",
    },
    "P002": {
        "id": "P002",
        "name": "Anita Desai",
        "age": 34,
        "gender": "Female",
        "blood_type": "O-",
        "conditions": ["Asthma", "Iron Deficiency Anemia"],
        "medications": ["Salbutamol Inhaler", "Ferrous Sulfate 200mg"],
        "allergies": ["Aspirin"],
        "emergency_contact": "+91-9876543211",
        "doctor_id": "DOC003",
    },
    "P003": {
        "id": "P003",
        "name": "Mohammed Hussain",
        "age": 72,
        "gender": "Male",
        "blood_type": "A+",
        "conditions": ["Coronary Artery Disease", "Atrial Fibrillation", "Osteoarthritis"],
        "medications": ["Warfarin 5mg", "Atorvastatin 20mg", "Metoprolol 50mg"],
        "allergies": [],
        "emergency_contact": "+91-9876543212",
        "doctor_id": "DOC001",
    },
}

# ── Doctors ───────────────────────────────────────────────────────────
DOCTORS: dict[str, dict] = {
    "DOC001": {
        "id": "DOC001",
        "name": "Dr. Vikram Patel",
        "department": "Cardiology",
        "qualification": "MD, DM Cardiology (AIIMS)",
        "available_slots": ["09:00", "10:00", "11:00", "14:00", "15:00"],
    },
    "DOC002": {
        "id": "DOC002",
        "name": "Dr. Meena Iyer",
        "department": "Orthopedics",
        "qualification": "MS Orthopedics (KEM)",
        "available_slots": ["10:00", "11:00", "12:00", "16:00"],
    },
    "DOC003": {
        "id": "DOC003",
        "name": "Dr. Arjun Nair",
        "department": "Neurology",
        "qualification": "MD, DM Neurology (NIMHANS)",
        "available_slots": ["09:00", "10:30", "14:00", "15:30"],
    },
    "DOC004": {
        "id": "DOC004",
        "name": "Dr. Sunita Reddy",
        "department": "General Medicine",
        "qualification": "MD General Medicine (CMC Vellore)",
        "available_slots": ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
    },
    "DOC005": {
        "id": "DOC005",
        "name": "Dr. Rajan Mehta",
        "department": "Pathology",
        "qualification": "MD Pathology (Grant Medical)",
        "available_slots": ["09:00", "11:00", "14:00"],
    },
    "DOC006": {
        "id": "DOC006",
        "name": "Dr. Kavita Joshi",
        "department": "Emergency Medicine",
        "qualification": "MD Emergency Medicine (Sion Hospital)",
        "available_slots": [],  # Always on call
    },
}

# ── Approved Pharmacies ───────────────────────────────────────────────
APPROVED_PHARMACIES: list[str] = [
    "MedPlus",
    "Apollo Pharmacy",
    "Wellness Forever",
    "1mg",
    "PharmEasy",
]

# ── Lab Reports ───────────────────────────────────────────────────────
LAB_REPORTS: dict[str, dict] = {
    "LAB001": {
        "id": "LAB001",
        "patient_id": "P001",
        "test_type": "HbA1c",
        "status": "completed",
        "result": "7.8%",
        "normal_range": "4.0-5.6%",
        "interpretation": "Indicates poorly controlled diabetes",
        "doctor_id": "DOC001",
        "lab": "SRL Diagnostics",
        "date": "2025-01-15",
    },
    "LAB002": {
        "id": "LAB002",
        "patient_id": "P001",
        "test_type": "Serum Creatinine",
        "status": "completed",
        "result": "1.8 mg/dL",
        "normal_range": "0.7-1.3 mg/dL",
        "interpretation": "Elevated — consistent with CKD Stage 3",
        "doctor_id": "DOC001",
        "lab": "SRL Diagnostics",
        "date": "2025-01-15",
    },
    "LAB003": {
        "id": "LAB003",
        "patient_id": "P002",
        "test_type": "Complete Blood Count",
        "status": "completed",
        "result": "Hemoglobin: 9.2 g/dL",
        "normal_range": "12.0-15.5 g/dL",
        "interpretation": "Low hemoglobin — iron deficiency anemia",
        "doctor_id": "DOC003",
        "lab": "Metropolis Healthcare",
        "date": "2025-01-20",
    },
    "LAB004": {
        "id": "LAB004",
        "patient_id": "P003",
        "test_type": "INR / PT",
        "status": "completed",
        "result": "INR: 2.5",
        "normal_range": "2.0-3.0 (therapeutic on Warfarin)",
        "interpretation": "Within therapeutic range for anticoagulation",
        "doctor_id": "DOC001",
        "lab": "Thyrocare",
        "date": "2025-02-01",
    },
    "LAB005": {
        "id": "LAB005",
        "patient_id": "P003",
        "test_type": "Lipid Profile",
        "status": "pending",
        "result": None,
        "normal_range": None,
        "interpretation": None,
        "doctor_id": "DOC001",
        "lab": "SRL Diagnostics",
        "date": "2025-02-05",
    },
}

# ── Labs ──────────────────────────────────────────────────────────────
LABS: dict[str, dict] = {
    "SRL": {"name": "SRL Diagnostics", "turnaround_hours": 24, "accredited": True},
    "Metropolis": {"name": "Metropolis Healthcare", "turnaround_hours": 12, "accredited": True},
    "Thyrocare": {"name": "Thyrocare", "turnaround_hours": 48, "accredited": True},
}

# ── Drug Interaction Database ─────────────────────────────────────────
DRUG_INTERACTIONS: list[dict] = [
    {
        "drug_a": "Warfarin",
        "drug_b": "Aspirin",
        "severity": "HIGH",
        "description": "Increased risk of bleeding. Avoid combination or monitor INR closely.",
    },
    {
        "drug_a": "Metformin",
        "drug_b": "Contrast Dye",
        "severity": "HIGH",
        "description": "Risk of lactic acidosis. Discontinue Metformin 48h before contrast procedures.",
    },
    {
        "drug_a": "Amlodipine",
        "drug_b": "Simvastatin",
        "severity": "MODERATE",
        "description": "Increased Simvastatin levels. Limit Simvastatin to 20mg/day.",
    },
    {
        "drug_a": "Losartan",
        "drug_b": "Potassium Supplements",
        "severity": "MODERATE",
        "description": "Risk of hyperkalemia. Monitor serum potassium.",
    },
    {
        "drug_a": "Metoprolol",
        "drug_b": "Verapamil",
        "severity": "HIGH",
        "description": "Risk of severe bradycardia and heart block. Avoid combination.",
    },
    {
        "drug_a": "Salbutamol",
        "drug_b": "Propranolol",
        "severity": "HIGH",
        "description": "Beta-blocker antagonizes bronchodilator effect. Use cardioselective beta-blocker.",
    },
    {
        "drug_a": "Warfarin",
        "drug_b": "Amiodarone",
        "severity": "HIGH",
        "description": "Amiodarone inhibits Warfarin metabolism. Reduce Warfarin dose by 30-50%.",
    },
    {
        "drug_a": "Atorvastatin",
        "drug_b": "Clarithromycin",
        "severity": "HIGH",
        "description": "Increased risk of rhabdomyolysis. Avoid combination.",
    },
    {
        "drug_a": "Metformin",
        "drug_b": "Alcohol",
        "severity": "MODERATE",
        "description": "Increased risk of lactic acidosis and hypoglycemia.",
    },
    {
        "drug_a": "Ferrous Sulfate",
        "drug_b": "Tetracycline",
        "severity": "MODERATE",
        "description": "Iron reduces tetracycline absorption. Separate doses by 2-3 hours.",
    },
]

# ── Emergency Contacts ────────────────────────────────────────────────
EMERGENCY_CONTACTS: list[dict] = [
    {"service": "Ambulance", "number": "108", "response_time": "8-12 minutes"},
    {"service": "Hospital Emergency", "number": "+91-22-2345-6789", "response_time": "Immediate"},
    {"service": "Poison Control", "number": "+91-11-2658-9391", "response_time": "Immediate"},
    {"service": "Blood Bank", "number": "+91-22-2345-6790", "response_time": "30 minutes"},
    {"service": "Police", "number": "100", "response_time": "10-15 minutes"},
]

# ── Prescriptions (for refill tool) ──────────────────────────────────
PRESCRIPTIONS: dict[str, dict] = {
    "RX001": {
        "id": "RX001",
        "patient_id": "P001",
        "medication": "Metformin 500mg",
        "dosage": "Twice daily",
        "quantity": 60,
        "refills_remaining": 3,
        "doctor_id": "DOC001",
        "cost_per_refill": 250.0,
    },
    "RX002": {
        "id": "RX002",
        "patient_id": "P001",
        "medication": "Amlodipine 5mg",
        "dosage": "Once daily",
        "quantity": 30,
        "refills_remaining": 5,
        "doctor_id": "DOC001",
        "cost_per_refill": 180.0,
    },
    "RX003": {
        "id": "RX003",
        "patient_id": "P002",
        "medication": "Ferrous Sulfate 200mg",
        "dosage": "Once daily",
        "quantity": 30,
        "refills_remaining": 2,
        "doctor_id": "DOC003",
        "cost_per_refill": 120.0,
    },
    "RX004": {
        "id": "RX004",
        "patient_id": "P003",
        "medication": "Warfarin 5mg",
        "dosage": "Once daily",
        "quantity": 30,
        "refills_remaining": 6,
        "doctor_id": "DOC001",
        "cost_per_refill": 350.0,
    },
}

# ── Appointments (existing) ──────────────────────────────────────────
APPOINTMENTS: dict[str, dict] = {
    "APT001": {
        "id": "APT001",
        "patient_id": "P001",
        "doctor_id": "DOC001",
        "department": "Cardiology",
        "date": "2025-02-10",
        "time": "10:00",
        "reason": "Follow-up: Blood pressure review",
        "status": "confirmed",
    },
    "APT002": {
        "id": "APT002",
        "patient_id": "P003",
        "doctor_id": "DOC001",
        "department": "Cardiology",
        "date": "2025-02-12",
        "time": "14:00",
        "reason": "INR monitoring and medication adjustment",
        "status": "confirmed",
    },
}

# ── Medication Catalog (for ordering) ─────────────────────────────────
MEDICATION_CATALOG: dict[str, dict] = {
    "Metformin 500mg": {"unit_price": 4.5, "category": "Antidiabetic", "controlled": False},
    "Amlodipine 5mg": {"unit_price": 6.0, "category": "Antihypertensive", "controlled": False},
    "Losartan 50mg": {"unit_price": 8.0, "category": "Antihypertensive", "controlled": False},
    "Warfarin 5mg": {"unit_price": 12.0, "category": "Anticoagulant", "controlled": True},
    "Atorvastatin 20mg": {"unit_price": 10.0, "category": "Statin", "controlled": False},
    "Metoprolol 50mg": {"unit_price": 7.5, "category": "Beta-blocker", "controlled": False},
    "Salbutamol Inhaler": {"unit_price": 150.0, "category": "Bronchodilator", "controlled": False},
    "Ferrous Sulfate 200mg": {"unit_price": 4.0, "category": "Supplement", "controlled": False},
    "Paracetamol 500mg": {"unit_price": 2.0, "category": "Analgesic", "controlled": False},
    "Amoxicillin 500mg": {"unit_price": 8.0, "category": "Antibiotic", "controlled": False},
}
