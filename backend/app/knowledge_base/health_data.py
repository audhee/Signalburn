# This is the knowledge base for the Arohan AI health assistant.
# Add more documents here as the project grows.
# Each string is one "document" that gets embedded and stored in ChromaDB.

HEALTH_KNOWLEDGE_BASE = [

    # --- Blood Pressure ---
    "Normal blood pressure is 120/80 mmHg. High blood pressure (hypertension) is above 130/80 mmHg. Low blood pressure (hypotension) is below 90/60 mmHg. Hypertension increases risk of heart attack and stroke.",

    "If blood pressure reading is above 180/120 mmHg, this is a hypertensive crisis and requires immediate emergency medical attention. Call ambulance immediately.",

    "Symptoms of high blood pressure include severe headache, chest pain, dizziness, difficulty breathing, nausea, and blurred vision.",

    "To manage blood pressure: reduce salt intake, exercise regularly, avoid smoking and alcohol, take prescribed medications, and monitor regularly with a wearable device.",

    # --- Heart Rate ---
    "Normal resting heart rate for adults is 60 to 100 beats per minute (BPM). Athletes may have a lower resting heart rate of 40 to 60 BPM.",

    "A heart rate above 100 BPM at rest is called tachycardia. A heart rate below 60 BPM at rest is called bradycardia. Both can indicate cardiac issues.",

    "If heart rate suddenly rises above 150 BPM or drops below 40 BPM, seek emergency medical help immediately. These are critical thresholds.",

    "Symptoms of abnormal heart rate include palpitations, dizziness, shortness of breath, chest pain, and fainting.",

    # --- Blood Sugar ---
    "Normal fasting blood sugar is 70 to 100 mg/dL. Pre-diabetes is 100 to 125 mg/dL. Diabetes is diagnosed when fasting blood sugar is 126 mg/dL or above.",

    "Low blood sugar (hypoglycemia) is below 70 mg/dL. Symptoms include shakiness, sweating, confusion, rapid heartbeat, and fainting. Eat sugar or glucose tablets immediately.",

    "High blood sugar (hyperglycemia) above 300 mg/dL is dangerous. Symptoms include extreme thirst, frequent urination, fatigue, and blurred vision. Seek medical attention.",

    "Diabetic patients should monitor blood sugar regularly. Maintain a balanced diet, exercise, and take insulin or medications as prescribed by the doctor.",

    # --- SpO2 / Oxygen Levels ---
    "Normal blood oxygen saturation (SpO2) is 95% to 100%. Readings below 90% indicate hypoxemia and require immediate medical attention.",

    "Low SpO2 symptoms include shortness of breath, confusion, rapid breathing, bluish color of lips or fingertips, and chest pain. Call emergency services immediately.",

    # --- CPR Emergency ---
    "CPR steps: 1. Check if person is conscious by tapping and shouting. 2. Call emergency services (112 in India). 3. Place heel of hand on center of chest. 4. Push hard and fast 30 times at 100-120 per minute. 5. Give 2 rescue breaths. 6. Continue until help arrives.",

    "For CPR in elderly patients, be firm but careful. Rib fractures can occur during CPR but saving the life is the priority. Do not stop compressions until emergency services arrive.",

    # --- General Emergency ---
    "In any medical emergency in India, call 112 (national emergency) or 108 (ambulance service). Keep calm and provide your exact location to the operator.",

    "Warning signs of a heart attack: chest pain or pressure, pain radiating to left arm or jaw, shortness of breath, cold sweat, nausea. Call emergency immediately and chew one aspirin if available.",

    "Warning signs of a stroke: sudden numbness or weakness in face, arm, or leg especially on one side of body, confusion, trouble speaking, severe headache, loss of balance. Remember FAST — Face drooping, Arm weakness, Speech difficulty, Time to call emergency.",

    # --- Elderly Specific ---
    "Elderly patients are at higher risk of falls, dehydration, medication side effects, and sudden cardiac events. Regular monitoring of vitals is critical for early detection.",

    "Dehydration in elderly patients can cause confusion, rapid heart rate, low blood pressure, and dizziness. Encourage regular fluid intake and monitor vitals.",
]