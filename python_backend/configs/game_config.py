import random
from typing import List, Dict

# ============================================
# EXHAUSTIVE PROFESSIONS LIST
# ============================================
PROFESSIONS = [
    # Medical Doctors
    "General Practitioner",
    "Family Medicine Physician",
    "Internal Medicine Specialist",
    "Cardiologist",
    "Pulmonologist",
    "Gastroenterologist",
    "Hepatologist",
    "Nephrologist",
    "Endocrinologist",
    "Rheumatologist",
    "Allergist",
    "Immunologist",
    "Infectious Disease Specialist",
    "Oncologist",
    "Hematologist",
    "Dermatologist",
    "Neurologist",
    "Psychiatrist",
    "Pediatrician",
    "Neonatologist",
    "Geriatrician",
    "Emergency Medicine Physician",
    "Critical Care Physician",
    "Anesthesiologist",
    "Radiologist",
    "Pathologist",
    "Forensic Pathologist",
    "Clinical Pathologist",
    "Anatomic Pathologist",
    "Surgeon",
    "General Surgeon",
    "Cardiothoracic Surgeon",
    "Neurosurgeon",
    "Orthopedic Surgeon",
    "Plastic Surgeon",
    "Reconstructive Surgeon",
    "Burn Surgeon",
    "Trauma Surgeon",
    "Vascular Surgeon",
    "Urologist",
    "Gynecologist",
    "Obstetrician",
    "Ophthalmologist",
    "Otolaryngologist (ENT)",
    "Maxillofacial Surgeon",
    "Oral Surgeon",
    "Dentist",
    "Orthodontist",
    "Periodontist",
    "Endodontist",
    "Prosthodontist",
    
    # Allied Health Professionals
    "Nurse",
    "Registered Nurse (RN)",
    "Licensed Practical Nurse (LPN)",
    "Nurse Practitioner (NP)",
    "Clinical Nurse Specialist",
    "Nurse Anesthetist (CRNA)",
    "Nurse Midwife",
    "Public Health Nurse",
    "School Nurse",
    "Occupational Health Nurse",
    "Auxiliary Nurse",
    "Nursing Assistant",
    
    # Medical Students & Interns
    "Medical Student",
    "Medical Intern",
    "Resident Physician",
    "Fellow",
    
    # Other Healthcare Professionals
    "Pharmacist",
    "Clinical Pharmacist",
    "Hospital Pharmacist",
    "Community Pharmacist",
    "Physiotherapist",
    "Physical Therapist",
    "Occupational Therapist",
    "Speech Therapist",
    "Respiratory Therapist",
    "Medical Laboratory Scientist",
    "Medical Laboratory Technician",
    "Radiologic Technologist",
    "Ultrasound Technologist",
    "MRI Technologist",
    "CT Technologist",
    "Nuclear Medicine Technologist",
    "Medical Technologist",
    "Biomedical Engineer",
    "Biomedical Scientist",
    "Biomedical Technologist",
    "Biomedical Technician",
    "Biochemist",
    "Biologist",
    "Geneticist",
    "Epidemiologist",
    "Public Health Specialist",
    "Health Educator",
    "Community Health Worker",
    "Traditional Birth Attendant",
    "Midwife",
    "Paramedic",
    "Emergency Medical Technician (EMT)",
    "Medical Assistant",
    "Phlebotomist",
    "Medical Coder",
    "Health Information Manager",
    "Medical Social Worker",
    "Clinical Psychologist",
    "Health Psychologist",
    "Nutritionist",
    "Dietitian",
    "Medical Writer",
    "Medical Researcher",
    "Clinical Research Coordinator",
]

# ============================================
# SUBJECT MAPPING - Maps professions to medical school subjects
# ============================================
SUBJECT = {
    # Core Medical Subjects (All doctors take these)
    "General Practitioner": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "microbiology", "internal medicine", "surgery", "pediatrics", "obstetrics", "gynecology", "psychiatry", "community medicine", "public health"],
    "Family Medicine Physician": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "microbiology", "internal medicine", "pediatrics", "obstetrics", "gynecology", "psychiatry", "community medicine", "public health", "preventive medicine"],
    "Internal Medicine Specialist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "microbiology", "internal medicine", "cardiology", "pulmonology", "gastroenterology", "nephrology", "endocrinology", "rheumatology", "hematology", "oncology"],
    "Cardiologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "cardiology", "internal medicine", "radiology", "surgery"],
    "Pulmonologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "pulmonology", "internal medicine", "radiology", "critical care"],
    "Gastroenterologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "gastroenterology", "internal medicine", "surgery", "radiology"],
    "Hepatologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "hepatology", "gastroenterology", "internal medicine"],
    "Nephrologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "nephrology", "internal medicine", "surgery"],
    "Endocrinologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "endocrinology", "internal medicine"],
    "Rheumatologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "rheumatology", "internal medicine"],
    "Allergist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "immunology", "allergy", "internal medicine"],
    "Immunologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "immunology", "microbiology"],
    "Infectious Disease Specialist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "microbiology", "infectious diseases", "internal medicine", "epidemiology"],
    "Oncologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "oncology", "hematology", "internal medicine", "radiology", "surgery"],
    "Hematologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "hematology", "oncology", "internal medicine"],
    "Dermatologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "dermatology", "surgery"],
    "Neurologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "neurology", "neurosurgery", "radiology"],
    "Psychiatrist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "psychiatry", "psychology", "neurology"],
    "Pediatrician": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "pediatrics", "neonatology", "internal medicine", "surgery"],
    "Neonatologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "neonatology", "pediatrics", "obstetrics"],
    "Geriatrician": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "geriatrics", "internal medicine", "psychiatry"],
    "Emergency Medicine Physician": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "emergency medicine", "trauma", "critical care", "surgery", "internal medicine"],
    "Critical Care Physician": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "critical care", "anesthesiology", "internal medicine", "surgery"],
    "Anesthesiologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "anesthesiology", "surgery", "critical care"],
    "Radiologist": ["anatomy", "physiology", "biochemistry", "pathology", "radiology", "imaging", "nuclear medicine"],
    "Pathologist": ["anatomy", "physiology", "biochemistry", "pathology", "microbiology", "histopathology", "cytopathology"],
    "Forensic Pathologist": ["anatomy", "physiology", "biochemistry", "pathology", "forensic medicine", "toxicology"],
    "Clinical Pathologist": ["anatomy", "physiology", "biochemistry", "pathology", "microbiology", "laboratory medicine"],
    "Anatomic Pathologist": ["anatomy", "physiology", "biochemistry", "pathology", "histopathology", "cytopathology"],
    "Surgeon": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "surgery", "anesthesiology"],
    "General Surgeon": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "surgery", "trauma"],
    "Cardiothoracic Surgeon": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "cardiac surgery", "thoracic surgery", "surgery"],
    "Neurosurgeon": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "neurosurgery", "neurology", "surgery"],
    "Orthopedic Surgeon": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "orthopedics", "surgery"],
    "Plastic Surgeon": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "plastic surgery", "surgery"],
    "Reconstructive Surgeon": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "reconstructive surgery", "plastic surgery", "surgery"],
    "Burn Surgeon": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "burn surgery", "plastic surgery", "surgery"],
    "Trauma Surgeon": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "trauma surgery", "emergency medicine", "surgery"],
    "Vascular Surgeon": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "vascular surgery", "surgery"],
    "Urologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "urology", "surgery"],
    "Gynecologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "gynecology", "obstetrics", "surgery"],
    "Obstetrician": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "obstetrics", "gynecology", "surgery"],
    "Ophthalmologist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "ophthalmology", "surgery"],
    "Otolaryngologist (ENT)": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "otolaryngology", "surgery"],
    "Maxillofacial Surgeon": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "maxillofacial surgery", "oral surgery", "surgery"],
    "Oral Surgeon": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "oral surgery", "dentistry"],
    "Dentist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "dentistry", "oral medicine"],
    "Orthodontist": ["anatomy", "physiology", "biochemistry", "pathology", "dentistry", "orthodontics"],
    "Periodontist": ["anatomy", "physiology", "biochemistry", "pathology", "dentistry", "periodontics"],
    "Endodontist": ["anatomy", "physiology", "biochemistry", "pathology", "dentistry", "endodontics"],
    "Prosthodontist": ["anatomy", "physiology", "biochemistry", "pathology", "dentistry", "prosthodontics"],
    
    # Nursing
    "Nurse": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "nursing", "medical-surgical nursing"],
    "Registered Nurse (RN)": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "nursing", "medical-surgical nursing", "critical care"],
    "Licensed Practical Nurse (LPN)": ["anatomy", "physiology", "pathology", "pharmacology", "nursing"],
    "Nurse Practitioner (NP)": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "nursing", "internal medicine", "pediatrics"],
    "Clinical Nurse Specialist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "nursing", "specialty area"],
    "Nurse Anesthetist (CRNA)": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "anesthesiology", "nursing"],
    "Nurse Midwife": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "obstetrics", "gynecology", "nursing"],
    "Public Health Nurse": ["anatomy", "physiology", "pathology", "pharmacology", "public health", "epidemiology", "community medicine", "nursing"],
    "School Nurse": ["anatomy", "physiology", "pathology", "pharmacology", "pediatrics", "public health", "nursing"],
    "Occupational Health Nurse": ["anatomy", "physiology", "pathology", "pharmacology", "occupational medicine", "public health", "nursing"],
    "Auxiliary Nurse": ["anatomy", "physiology", "pathology", "nursing"],
    "Nursing Assistant": ["anatomy", "physiology", "nursing"],
    
    # Medical Students & Interns
    "Medical Student": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "microbiology", "internal medicine", "surgery", "pediatrics", "obstetrics", "gynecology", "psychiatry", "community medicine"],
    "Medical Intern": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "microbiology", "internal medicine", "surgery", "pediatrics", "obstetrics", "gynecology", "psychiatry", "emergency medicine"],
    "Resident Physician": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "microbiology", "specialty-specific subjects"],
    "Fellow": ["specialty-specific advanced subjects"],
    
    # Pharmacy
    "Pharmacist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "pharmacy", "pharmaceutical chemistry", "pharmaceutics"],
    "Clinical Pharmacist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "clinical pharmacy", "internal medicine"],
    "Hospital Pharmacist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "hospital pharmacy", "critical care"],
    "Community Pharmacist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "community pharmacy", "public health"],
    
    # Therapy & Rehabilitation
    "Physiotherapist": ["anatomy", "physiology", "biochemistry", "pathology", "physiotherapy", "kinesiology", "biomechanics"],
    "Physical Therapist": ["anatomy", "physiology", "biochemistry", "pathology", "physiotherapy", "kinesiology", "biomechanics"],
    "Occupational Therapist": ["anatomy", "physiology", "pathology", "occupational therapy", "psychology"],
    "Speech Therapist": ["anatomy", "physiology", "pathology", "speech therapy", "neurology"],
    "Respiratory Therapist": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "respiratory therapy", "pulmonology"],
    
    # Laboratory & Technology
    "Medical Laboratory Scientist": ["anatomy", "physiology", "biochemistry", "pathology", "microbiology", "laboratory medicine", "hematology"],
    "Medical Laboratory Technician": ["anatomy", "physiology", "biochemistry", "pathology", "microbiology", "laboratory medicine"],
    "Radiologic Technologist": ["anatomy", "physiology", "radiology", "imaging"],
    "Ultrasound Technologist": ["anatomy", "physiology", "radiology", "ultrasound"],
    "MRI Technologist": ["anatomy", "physiology", "radiology", "magnetic resonance imaging"],
    "CT Technologist": ["anatomy", "physiology", "radiology", "computed tomography"],
    "Nuclear Medicine Technologist": ["anatomy", "physiology", "radiology", "nuclear medicine"],
    "Medical Technologist": ["anatomy", "physiology", "biochemistry", "pathology", "microbiology", "laboratory medicine"],
    "Biomedical Engineer": ["anatomy", "physiology", "biochemistry", "biomedical engineering", "biomechanics"],
    "Biomedical Scientist": ["anatomy", "physiology", "biochemistry", "pathology", "microbiology", "biomedical science"],
    "Biomedical Technologist": ["anatomy", "physiology", "biochemistry", "biomedical technology"],
    "Biomedical Technician": ["anatomy", "physiology", "biomedical technology"],
    "Biochemist": ["anatomy", "physiology", "biochemistry", "molecular biology"],
    "Biologist": ["anatomy", "physiology", "biochemistry", "biology", "molecular biology"],
    "Geneticist": ["anatomy", "physiology", "biochemistry", "genetics", "molecular biology"],
    
    # Public Health & Community
    "Epidemiologist": ["anatomy", "physiology", "biochemistry", "pathology", "microbiology", "epidemiology", "public health", "statistics"],
    "Public Health Specialist": ["anatomy", "physiology", "pathology", "public health", "epidemiology", "community medicine"],
    "Health Educator": ["anatomy", "physiology", "pathology", "public health", "health education"],
    "Community Health Worker": ["anatomy", "physiology", "pathology", "public health", "community medicine"],
    "Traditional Birth Attendant": ["anatomy", "physiology", "obstetrics", "midwifery"],
    "Midwife": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "obstetrics", "gynecology", "midwifery"],
    
    # Emergency Services
    "Paramedic": ["anatomy", "physiology", "pathology", "pharmacology", "emergency medicine", "trauma"],
    "Emergency Medical Technician (EMT)": ["anatomy", "physiology", "pathology", "pharmacology", "emergency medicine"],
    
    # Support Roles
    "Medical Assistant": ["anatomy", "physiology", "pathology", "pharmacology"],
    "Phlebotomist": ["anatomy", "physiology", "pathology"],
    "Medical Coder": ["anatomy", "physiology", "pathology", "medical coding"],
    "Health Information Manager": ["anatomy", "physiology", "pathology", "health information systems"],
    "Medical Social Worker": ["anatomy", "physiology", "pathology", "psychology", "social work"],
    
    # Psychology & Mental Health
    "Clinical Psychologist": ["anatomy", "physiology", "biochemistry", "pathology", "psychology", "psychiatry"],
    "Health Psychologist": ["anatomy", "physiology", "pathology", "psychology", "public health"],
    
    # Nutrition
    "Nutritionist": ["anatomy", "physiology", "biochemistry", "pathology", "nutrition"],
    "Dietitian": ["anatomy", "physiology", "biochemistry", "pathology", "nutrition", "dietetics"],
    
    ##
    "Psychiatrist": ["anatomy", "physiology", "biochemistry", "pathology", "psychology", "psychiatry"],
    "Psychologist": ["anatomy", "physiology", "biochemistry", "pathology", "psychology"],
    "Psychotherapist": ["anatomy", "physiology", "biochemistry", "pathology", "psychology", "psychotherapy"],
    "Psychologist": ["anatomy", "physiology", "biochemistry", "pathology", "psychology"],
    "Psychologist": ["anatomy", "physiology", "biochemistry", "pathology", "psychology"],
    
    # Community health workers
    "Community Health Worker": ["anatomy", "physiology", "pathology", "public health", "community medicine"],
    
    # Traditional Birth Attendant
    "Traditional Birth Attendant": ["anatomy", "physiology", "obstetrics", "midwifery"],
    
    # Midwife
    "Midwife": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "obstetrics", "gynecology", "midwifery"],
    
    # Paramedic
    "Paramedic": ["anatomy", "physiology", "pathology", "pharmacology", "emergency medicine", "trauma"],
    
    # Emergency Medical Technician (EMT)
    "Emergency Medical Technician (EMT)": ["anatomy", "physiology", "pathology", "pharmacology", "emergency medicine"],
    
    # Medical Assistant
    "Medical Assistant": ["anatomy", "physiology", "pathology", "pharmacology"],
    
    # Phlebotomist
    "Phlebotomist": ["anatomy", "physiology", "pathology"],
    
    # Medical Coder
    "Medical Coder": ["anatomy", "physiology", "pathology", "medical coding"],
    
    # Health Information Manager
    "Health Information Manager": ["anatomy", "physiology", "pathology", "health information systems"],
    
    # Medical Social Worker
    "Medical Social Worker": ["anatomy", "physiology", "pathology", "psychology", "social work"],
    
    # Clinical Psychologist
    "Clinical Psychologist": ["anatomy", "physiology", "biochemistry", "pathology", "psychology", "psychiatry"],
    
    # Health Psychologist
    "Health Psychologist": ["anatomy", "physiology", "pathology", "psychology", "public health"],
    
    # Nutritionist
    "Nutritionist": ["anatomy", "physiology", "biochemistry", "pathology", "nutrition"],
    
    # Dietitian
    "Dietitian": ["anatomy", "physiology", "biochemistry", "pathology", "nutrition", "dietetics"],
    
    # Medical Writer
    "Medical Writer": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "medical writing"],
    
    # Medical Researcher
    "Medical Researcher": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "research methodology"],
    
    # Clinical Research Coordinator
    "Clinical Research Coordinator": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "clinical research"],

    # Research & Writing
    "Medical Writer": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "medical writing"],
    "Medical Researcher": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "research methodology"],
    "Clinical Research Coordinator": ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "clinical research"],
}

# ============================================
# IMPROVED ERAS
# ============================================
ERAS = [
    "Prehistoric Era",
    "Ancient Era (3000 BCE - 500 CE)",
    "Medieval Era (500 CE - 1500 CE)",
    "Renaissance Era (1400 CE - 1600 CE)",
    "Early Modern Era (1500 CE - 1800 CE)",
    "Industrial Revolution (1760 CE - 1840 CE)",
    "19th Century (1800 CE - 1900 CE)",
    "Early 20th Century (1900 CE - 1945 CE)",
    "Post-War Era (1945 CE - 1980 CE)",
    "Late 20th Century (1980 CE - 2000 CE)",
    "21st Century (2000 CE - Present)",
    "Near Future (2025 CE - 2050 CE)",
    "Distant Future (2050 CE+)",
    "Alternate History",
    "Steampunk Era",
    "Cyberpunk Era",
    "Post-Apocalyptic Era",
    "Space Age",
]

# ============================================
# IMPROVED NATURAL CONDITIONS
# ============================================
NATURAL_CONDITIONS = [
    # Normal Conditions
    "Normal",
    "Mild Weather",
    "Seasonal Conditions",
    
    # Natural Disasters
    "Earthquake",
    "Tsunami",
    "Volcanic Eruption",
    "Hurricane",
    "Cyclone",
    "Typhoon",
    "Tornado",
    "Flooding",
    "Flash Flood",
    "Drought",
    "Wildfire",
    "Blizzard",
    "Avalanche",
    "Landslide",
    "Mudslide",
    "Dust Storm",
    "Sandstorm",
    "Heat Wave",
    "Cold Wave",
    "Ice Storm",
    
    # Accidents & Incidents
    "Fire Accident",
    "Building Collapse",
    "Bridge Collapse",
    "Car Accident",
    "Train Accident",
    "Plane Crash",
    "Shipwreck",
    "Industrial Accident",
    "Chemical Spill",
    "Nuclear Incident",
    "Power Outage",
    "Water Contamination",
    
    # Health Emergencies
    "Pandemic",
    "Epidemic",
    "Outbreak",
    "Bioterrorism",
    "Mass Poisoning",
    "Foodborne Illness Outbreak",
    
    # Social & Political
    "Civil Unrest",
    "War Zone",
    "Refugee Crisis",
    "Mass Migration",
    "Economic Crisis",
    "Famine",
    
    # Space & Sci-Fi
    "Solar Flare",
    "Meteor Impact",
    "Alien Contact",
    "Technological Singularity",
]

# ============================================
# OTHER CONFIGURATIONS (Unchanged)
# ============================================
NATIONS = ["Developed", "High-Tech", "Underdeveloped", "Developing", "Emerging", "Post-Industrial"]
ECONOMIC_ADVANTAGES = ["Crude Oil", "Gold", "Metals", "Rare Metals", "Human Capital", "Agriculture", "Technology", "Tourism", "Manufacturing", "Services", "Finance", "Renewable Energy"]
CONTINENTS = ["Africa", "North America", "South America", "Europe", "Asia", "Australia", "Antarctica"]
MODES = [
    "Outpatient",
    "Emergency",
    "ICU",
    "Cellular",
    "Inpatient",
    "Trauma",
    "Telemedicine",
    "Home Visit",
    "Ambulance",
    "Helicopter",
    "Air Ambulance",
    "Burn Unit",
    "Neonatal",
    "Pediatric",
    "Geriatric",
    "Operating Room",
    "Recovery Room",
    "Isolation Ward",
    "Quarantine Facility",
]
AREAS = [
    "Rural",
    "Urban",
    "Countryside",
    "Semi-Urban",
    "Coastal",
    "Forest Area",
    "Village",
    "Town",
    "Industrial Area",
    "Desert",
    "Mountainous Region",
    "Island",
    "Suburban",
    "Remote Area",
    "Slum",
    "Metropolitan Area",
    "In-Vivo",
    "In-Vitro",
    "In-Situ",
    "Ex-Vivo",
    "Ex-Situ",
    "Ex-Plant",
    "Ex-Organ",
    "Ex-Tissue",
    "Ex-Cellular",
    "Ex-Molecular",
    "Laboratory",
    "Field Hospital",
    "Mobile Clinic",
]

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_subjects_for_profession(profession: str) -> List[str]:
    """Get the list of subjects for a given profession."""
    return SUBJECT.get(profession, ["anatomy", "physiology", "biochemistry", "pathology", "pharmacology", "microbiology"])

def get_random_profession() -> str:
    """Get a random profession."""
    return random.choice(PROFESSIONS)

def get_random_era() -> str:
    """Get a random era."""
    return random.choice(ERAS)

def get_random_natural_condition() -> str:
    """Get a random natural condition."""
    return random.choice(NATURAL_CONDITIONS)

def get_random_attributes(profession: str= None, subject: str= None) -> Dict[str, str]:
    """
    Get a dictionary of random attributes for game configuration.
    
    Returns:
        Dictionary with random values for:
        - profession
        - clinical_setting
        - subject (based on profession)
        - era
        - natural_conditions
        - nation_type
        - economic_advantage
    """
    profession = profession or get_random_profession()
    pool = get_subjects_for_profession(profession)
    if subject and subject in pool:
        chosen_subject = subject
    else:
        chosen_subject = random.choice(pool) if pool else "general medicine"

    return {
        "profession": profession,
        "clinical_setting": random.choice(MODES),
        "subject": chosen_subject,
        "era": get_random_era(),
        "natural_conditions": get_random_natural_condition(),
        "nation_type": random.choice(NATIONS),
        "economic_advantage": random.choice(ECONOMIC_ADVANTAGES)
    }
