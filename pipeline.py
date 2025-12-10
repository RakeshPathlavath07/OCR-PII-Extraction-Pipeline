import cv2
import numpy as np
import easyocr
import os
import re
import json
import matplotlib.pyplot as plt
from thefuzz import process

# Initialize EasyOCR Reader (loads model once)
reader = easyocr.Reader(['en'])

# Configuration
INPUT_FOLDER = 'images'
OUTPUT_FOLDER = 'output'

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

print("Libraries loaded. Output folder ready.")

# --- 1. IMAGE PRE-PROCESSING ---
def get_clean_image(image_path):
    img = cv2.imread(image_path)
    if img is None: return None, None
    
    # Convert to Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Increase contrast (helps with faint handwriting)
    alpha = 1.5 # Contrast control
    beta = 0    # Brightness control
    contrasted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
    
    # Adaptive Thresholding (The "Magic" for handwriting)
    # Converts to strict Black & White based on local pixel neighborhood
    thresh = cv2.adaptiveThreshold(contrasted, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 31, 15)
    
    return img, thresh

# --- 2. TEXT CLEANING HELPER ---
class TextCleaner:
    def __init__(self):
        # Map messy OCR output to expected headers
        self.corrections = {
            "Patient Name": ["Palicnt Name", "Pailent Nama", "PatientName", "Name:"],
            "Age": ["Agc", "Aqe"],
            "Sex": ["Scx", "Sox"],
            "IPD No": ["IPdNo", "IPDNo", "1PD No"],
            "UHID No": ["UHHD No", "UHID", "UHI D"],
            "Date": ["Da te", "Dale", "Dote"],
            "Dr.": ["Drsk", "Dn.", "Dn", "0r.", "Dr "]
        }
        
    def fix_text(self, text):
        # Simple cleanup
        clean_text = text.replace(";", "").replace(":", "").replace("_", "").strip()
        
        # Fuzzy matching against known headers
        best_match, score = process.extractOne(clean_text, self.corrections.keys())
        if score > 85:
            return best_match
        return text

cleaner = TextCleaner()

# --- 3. PII DETECTION LOGIC ---
def is_pii(text, cleaned_text):
    label = None
    
    # A. Check Dates (Regex)
    # Matches: 14/04/25, 14.4.25, 14-04-2025
    clean_date = text.replace(" ", "").replace("-", ".").replace("/", ".")
    clean_date = clean_date.replace('l', '1').replace('I', '1').replace('O', '0').replace('S', '5')
    if re.search(r'\d{1,2}\.\d{1,2}\.\d{2,4}', clean_date):
        return "DATE"

    # B. Check Doctor Names (Prefixes)
    lower_text = text.lower()
    if lower_text.startswith(('dr', 'dn', 'mr', 'ms', 'prof')):
        # Ignore medical terms starting with d
        if "drug" not in lower_text and "dose" not in lower_text:
            return "DOCTOR"

    # C. Check Patient Identifiers (Headers)
    # We check the "Corrected" text here for better accuracy
    if cleaned_text in ["Patient Name", "Age", "Sex", "IPD No", "UHID No"]:
        return "PATIENT_INFO"

    # D. Check IDs (Long numbers)
    if text.isdigit() and len(text) > 6:
        return "ID_NUM"

    return None

# --- 4. MAIN PIPELINE ---
def process_and_display(filename):
    path = os.path.join(INPUT_FOLDER, filename)
    if not os.path.exists(path):
        print(f"File not found: {filename}")
        return

    print(f"Processing: {filename}...")
    original, processed = get_clean_image(path)
    
    # Run OCR
    results = reader.readtext(processed, detail=1)
    
    output_img = original.copy()
    height, width, _ = original.shape
    extracted_data = []

    for (bbox, text, prob) in results:
        # 1. Clean Text
        cleaned_header = cleaner.fix_text(text)
        
        # 2. Detect PII
        pii_type = is_pii(text, cleaned_header)
        
        extracted_data.append({
            "text": text,
            "cleaned": cleaned_header,
            "pii_type": pii_type
        })

        # 3. Redact if PII found
        if pii_type:
            top_left = list(map(int, bbox[0]))
            bottom_right = list(map(int, bbox[2]))
            
            # Dynamic Box Expansion for Headers (e.g., "Patient Name")
            # Extends the black box to the right to cover the handwritten name
            if pii_type == "PATIENT_INFO":
                box_w = bottom_right[0] - top_left[0]
                new_x2 = min(width, bottom_right[0] + int(box_w * 2.5))
                bottom_right[0] = new_x2
            
            # Draw Black Box
            cv2.rectangle(output_img, tuple(top_left), tuple(bottom_right), (0, 0, 0), -1)

    # Save Redacted Image
    save_path = os.path.join(OUTPUT_FOLDER, 'redacted_' + filename)
    cv2.imwrite(save_path, output_img)
    
    # Display Result in Notebook
    plt.figure(figsize=(10,10))
    plt.imshow(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB))
    plt.title(f"Redacted: {filename}")
    plt.axis('off')
    plt.show()
    
    return extracted_data

# --- RUN ON ALL IMAGES ---
all_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
full_report = {}

for f in all_files:
    data = process_and_display(f)
    full_report[f] = data

# Save JSON Report
with open(os.path.join(OUTPUT_FOLDER, 'extraction_report.json'), 'w') as json_file:
    json.dump(full_report, json_file, indent=4)

print("Pipeline execution complete. JSON report saved.")