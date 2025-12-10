import cv2
import numpy as np
import easyocr
import os
import re

# --- CONFIGURATION ---
INPUT_FOLDER = 'images'
OUTPUT_FOLDER = 'output'

if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)

# --- 1. PRE-PROCESSING ---
def get_clean_image(image_path):
    img = cv2.imread(image_path)
    if img is None: return None, None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    kernel = np.ones((1, 1), np.uint8)
    dilated = cv2.dilate(gray, kernel, iterations=1)
    thresh = cv2.adaptiveThreshold(dilated, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 31, 15)
    return img, thresh

# --- 2. PII DETECTION LOGIC ---
def is_date(text):
    clean = text.replace(" ", "").replace("-", ".").replace("/", ".")
    clean = clean.replace('l', '1').replace('I', '1').replace('O', '0').replace('S', '5')
    if re.search(r'\d{1,2}\.\d{1,2}\.\d{2,4}', clean): return True
    return False

def is_doctor_name(text):
    t = text.lower()
    if "drug" in t or "dose" in t or "date" in t or "sign" in t: return False
    prefixes = ['dr', 'dn', 'mr', 'ms', 'prof']
    for p in prefixes:
        if t.startswith(p) and len(t) > 3: return True
    if t in ['dr.', 'dr', 'dn.', 'dn']: return True
    return False

def is_patient_identifier(text):
    t = text.lower()
    keywords = ['patient', 'name:', 'ipd', 'uhid', 'bed no', 'age:', 'sex:']
    for k in keywords:
        if k in t: return True
    return False

# --- 3. MAIN PROCESS (UPDATED) ---
def process_all_images():
    print(f"Scanning folder: {INPUT_FOLDER}...")
    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not files:
        print("No images found!"); return

    print("Loading AI Model...")
    reader = easyocr.Reader(['en'])

    for filename in files:
        path = os.path.join(INPUT_FOLDER, filename)
        print(f"\nProcessing: {filename}")
        original, processed = get_clean_image(path)
        if original is None: continue

        results = reader.readtext(processed, detail=1)
        output_img = original.copy()
        redaction_count = 0
        height, width, _ = original.shape

        for (bbox, text, prob) in results:
            should_redact = False
            label = ""

            if is_date(text):
                should_redact = True; label = "DATE"
            elif is_doctor_name(text):
                should_redact = True; label = "DOCTOR"
            elif is_patient_identifier(text):
                should_redact = True; label = "PATIENT_INFO"
            elif text.isdigit() and len(text) > 6:
                should_redact = True; label = "ID_NUM"

            if should_redact:
                redaction_count += 1
                
                # Get coordinates
                top_left = list(map(int, bbox[0]))
                bottom_right = list(map(int, bbox[2]))
                
                # --- SAFETY EXPANSION ---
                # If it's a Header (like "Patient Name:"), extend the black box 
                # to the right to cover the handwritten value next to it.
                if label == "PATIENT_INFO":
                    # Calculate box width
                    box_w = bottom_right[0] - top_left[0]
                    # Extend to the right by 2x the width (or until edge of image)
                    new_x2 = min(width, bottom_right[0] + int(box_w * 2.5))
                    bottom_right[0] = new_x2
                    print(f"  -> Redacting (Expanded): {text}")
                else:
                    print(f"  -> Redacting: {text}")

                cv2.rectangle(output_img, tuple(top_left), tuple(bottom_right), (0, 0, 0), -1)

        save_path = os.path.join(OUTPUT_FOLDER, 'redacted_' + filename)
        cv2.imwrite(save_path, output_img)
        print(f"  Saved to {save_path}")

if __name__ == "__main__":
    process_all_images()