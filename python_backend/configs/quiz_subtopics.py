"""
Exhaustive default subtopics for health and biological subjects.
Used when AI-generated subtopics fail or for fallback.
"""
from typing import Dict, List

# Maps subject/profession keywords to subtopic lists. Lowercase keys for matching.
DEFAULT_SUBTOPICS: Dict[str, List[str]] = {
    "general medicine": [
        "Cardiology", "Pulmonology", "Gastroenterology", "Neurology", "Endocrinology",
        "Nephrology", "Rheumatology", "Infectious Diseases", "Dermatology", "Hematology",
        "Oncology", "Emergency Medicine", "Internal Medicine", "Preventive Medicine"
    ],
    "nursing": [
        "Patient Care", "Medication Administration", "Vital Signs", "Wound Care",
        "Patient Assessment", "Critical Care", "Pediatric Nursing", "Mental Health Nursing",
        "Community Health", "Ethics in Nursing", "Infection Control", "Pain Management"
    ],
    "physiotherapy": [
        "Musculoskeletal", "Neurological Rehabilitation", "Cardiopulmonary", "Pediatrics",
        "Geriatrics", "Sports Medicine", "Orthopedics", "Vestibular Rehabilitation",
        "Wound Management", "Amputation Rehabilitation"
    ],
    "pharmacy": [
        "Pharmacology", "Drug Interactions", "Dosage Calculations", "Pharmaceutical Care",
        "Medication Safety", "Clinical Pharmacy", "Pharmacokinetics", "Pharmacodynamics",
        "Drug Development", "Regulatory Affairs"
    ],
    "anatomy": [
        "Gross Anatomy", "Histology", "Embryology", "Neuroanatomy", "Surface Anatomy",
        "Radiological Anatomy", "Clinical Anatomy"
    ],
    "physiology": [
        "Cardiovascular", "Respiratory", "Renal", "Gastrointestinal", "Endocrine",
        "Neurophysiology", "Muscle Physiology", "Reproductive Physiology"
    ],
    "biochemistry": [
        "Metabolism", "Enzymology", "Molecular Biology", "Genetics", "Nutritional Biochemistry",
        "Clinical Biochemistry", "Signal Transduction"
    ],
    "pathology": [
        "General Pathology", "Systemic Pathology", "Clinical Pathology", "Histopathology",
        "Microbiology", "Immunology", "Oncologic Pathology"
    ],
    "pharmacology": [
        "General Pharmacology", "Autonomic Pharmacology", "Cardiovascular Pharmacology",
        "CNS Pharmacology", "Chemotherapy", "Toxicology"
    ],
    "microbiology": [
        "Bacteriology", "Virology", "Parasitology", "Mycology", "Immunology",
        "Medical Microbiology", "Epidemiology"
    ],
    "surgery": [
        "General Surgery", "Trauma", "Anesthesiology", "Surgical Techniques",
        "Preoperative Care", "Postoperative Care", "Minimally Invasive Surgery"
    ],
    "pediatrics": [
        "Neonatology", "Growth and Development", "Pediatric Emergencies",
        "Infectious Diseases", "Congenital Disorders", "Vaccination"
    ],
    "obstetrics": [
        "Antenatal Care", "Labor and Delivery", "Postpartum Care", "High-Risk Pregnancy",
        "Fetal Medicine", "Reproductive Health"
    ],
    "gynecology": [
        "Reproductive Health", "Contraception", "Menopause", "Gynecologic Oncology",
        "Infertility", "Pelvic Disorders"
    ],
    "psychiatry": [
        "Mood Disorders", "Anxiety Disorders", "Psychotic Disorders", "Substance Use",
        "Child Psychiatry", "Geriatric Psychiatry", "Psychopharmacology"
    ],
    "radiology": [
        "Plain Radiography", "CT", "MRI", "Ultrasound", "Nuclear Medicine",
        "Interventional Radiology", "Radiation Safety"
    ],
    "dentistry": [
        "Oral Surgery", "Periodontics", "Endodontics", "Orthodontics", "Prosthodontics",
        "Oral Pathology", "Pediatric Dentistry"
    ],
    "dermatology": [
        "Inflammatory Skin Diseases", "Infectious Skin Diseases", "Skin Cancer",
        "Dermatologic Surgery", "Cosmetic Dermatology"
    ],
    "ophthalmology": [
        "Cataract", "Glaucoma", "Retina", "Cornea", "Pediatric Ophthalmology",
        "Neuro-ophthalmology", "Oculoplastics"
    ],
    "ent": [
        "Otology", "Rhinology", "Laryngology", "Head and Neck Surgery",
        "Audiology", "Facial Plastic Surgery"
    ],
    "orthopedics": [
        "Trauma", "Joint Replacement", "Spine", "Sports Medicine", "Pediatric Orthopedics",
        "Hand Surgery", "Foot and Ankle"
    ],
    "urology": [
        "Oncology", "Reconstructive Urology", "Pediatric Urology", "Andrology",
        "Female Urology", "Endourology"
    ],
    "neurosurgery": [
        "Brain Tumors", "Spine Surgery", "Cerebrovascular", "Pediatric Neurosurgery",
        "Functional Neurosurgery", "Trauma"
    ],
    "cardiology": [
        "Arrhythmias", "Heart Failure", "Coronary Artery Disease", "Valvular Disease",
        "Congenital Heart Disease", "Interventional Cardiology", "Electrophysiology"
    ],
    "pulmonology": [
        "COPD", "Asthma", "Interstitial Lung Disease", "Sleep Medicine",
        "Critical Care", "Pleural Disease", "Lung Cancer"
    ],
    "gastroenterology": [
        "Liver Disease", "IBD", "GI Motility", "Pancreatobiliary", "Endoscopy",
        "Nutrition", "GI Oncology"
    ],
    "nephrology": [
        "Acute Kidney Injury", "CKD", "Dialysis", "Transplantation", "Glomerular Disease",
        "Electrolyte Disorders", "Hypertension"
    ],
    "endocrinology": [
        "Diabetes", "Thyroid", "Adrenal", "Pituitary", "Bone Metabolism",
        "Reproductive Endocrinology", "Obesity"
    ],
    "hematology": [
        "Anemia", "Coagulation", "Leukemia", "Lymphoma", "Myeloma",
        "Stem Cell Transplantation", "Hemoglobinopathies"
    ],
    "oncology": [
        "Medical Oncology", "Radiation Oncology", "Surgical Oncology", "Pediatric Oncology",
        "Palliative Care", "Cancer Screening", "Targeted Therapy"
    ],
    "emergency": [
        "Trauma", "Resuscitation", "Toxicology", "Environmental Emergencies",
        "Pediatric Emergencies", "Disaster Medicine"
    ],
    "public health": [
        "Epidemiology", "Biostatistics", "Health Policy", "Environmental Health",
        "Occupational Health", "Health Promotion", "Disease Prevention"
    ],
    "biology": [
        "Cell Biology", "Genetics", "Evolution", "Ecology", "Physiology",
        "Molecular Biology", "Developmental Biology"
    ],
}

SAFE_DEFAULT = "general medicine"
