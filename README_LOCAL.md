# OCR-PII-Extraction-Pipeline
An end-to-end OCR pipeline designed to process handwritten medical documents. It uses OpenCV and EasyOCR to extract text and automatically redact sensitive PII (Patient Names, Doctor Signatures, Dates, and IDs).

---
# OCR Pipeline: Handwritten Document PII Extraction
 ---
##  Project Overview
This project is an end-to-end Optical Character Recognition (OCR) pipeline designed to process **handwritten medical documents**. The system takes raw JPEG images as input, performs image pre-processing to handle noise and tilt, extracts text using Deep Learning models, and automatically detects and redacts **Personally Identifiable Information (PII)**.

----

##  Objective
The goal was to build a robust solution that works on:
*   **Handwritten forms** (which are harder to read than printed text).
*   **Slightly tilted images** (common in mobile scans).
*   **Medical notes** containing sensitive data like Patient Names, Dates, Doctor Signatures, and IDs.

----

##  Tech Stack
*   **Language:** Python 3.x
*   **Image Processing:** OpenCV (`cv2`), NumPy
*   **OCR Engine:** EasyOCR (Deep Learning-based text recognition)
*   **Pattern Matching:** Regular Expressions (Regex)

----

## ✨ Key Features

### 1. Advanced Pre-processing
*   **Deskewing:** The pipeline detects if an image is tilted (rotated) and automatically corrects the alignment to ensure text is horizontal.
*   **Adaptive Thresholding:** Converts noisy, shadowed images into clean, high-contrast binary images, significantly improving OCR accuracy on handwriting.

### 2. Deep Learning OCR
*   Utilizes **EasyOCR** to extract text coordinates (bounding boxes) and content. This was chosen over Tesseract for its superior performance on cursive and irregular handwriting.

### 3. Context-Aware PII Redaction
Instead of simple keyword matching, the system uses intelligent logic:
*   **Dates:** Detects various formats (e.g., `15/4/25`, `15.04.2025`).
*   **Doctor Names:** Identifies signatures using prefixes (e.g., `Dr.`, `Dn.`, `Prof.`) while ignoring medical terms like "Drug" or "Dose".
*   **Dynamic Patient Name Redaction:** Recognizes headers like "Patient Name:" or "IPD No:" and **automatically expands the redaction box** to the right. This ensures the handwritten name/number next to the printed label is fully covered.

##  Project Structure
```text
OCR-Pipeline/
│
├── images/               # Input folder for raw .jpg/.jpeg files
├── output/               # Output folder for processed & redacted images
├── pipeline.py           # Main source code
├── requirements.txt      # List of dependencies
└── README.md             # Project documentation

```
---
## setup and usage 

### 1. Install Dependencies
Make sure you have Python installed. Run the following command to install the required libraries:
```bash
pip install -r requirements.txt
```

### 2. Add Input Images
Place your handwritten document images (JPEG format) inside the **images/** folder.

### 3. Run the Pipeline
Execute the python script:
```bash
python pipeline.py
```
### 4. View Results
The script will process every image in the input folder. Check the **output/** directory for the results. File names will be prefixed with redacted_.

----

## Methodology (How it works)

* Image Loading: Reads images from the directory.
* Noise Removal: Applies dilation and adaptive Gaussian thresholding to separate ink from paper texture.
* Inference: Runs EasyOCR to generate a list of bounding boxes and text strings.
* Logic Filtering: Iterates through the detected text:
* If it looks like a Date (Regex match) → Redact.
* If it looks like a Doctor (Prefix check) → Redact.
* If it is a Header (e.g., "Patient Name") → Redact & Expand Box rightward.
* Drawing: Uses OpenCV to draw filled black rectangles over the calculated coordinates on the original image.
* Export: Saves the final images to the output directory.

---

## Requirements
* opencv-python
* easyocr
* numpy
