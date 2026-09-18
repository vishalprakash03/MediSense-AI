"""
Downloads real, publicly available datasets used to train the MediSense AI
risk models. Run this on a machine with internet access:

    python3 ml/datasets/download_real_data.py

Sources include two long-standing public ML benchmark datasets and official
CDC/NCHS NHANES survey components:

1. Pima Indians Diabetes Dataset
   Originally from the National Institute of Diabetes and Digestive and
   Kidney Diseases (NIDDK). 768 real patient records, 8 clinical features,
   binary diabetes outcome.
   Mirror used: https://github.com/npradaschnor/Pima-Indians-Diabetes-Dataset

2. UCI Heart Disease Dataset (Cleveland subset)
   Originally from the UCI Machine Learning Repository / Cleveland Clinic
   Foundation. 303 real patient records, 13 clinical features, binary
   heart-disease outcome.
   Mirror used: https://github.com/sharmaroshan/Heart-UCI-Dataset

3. NHANES August 2021–August 2023 (CDC/NCHS)
   A nationally representative U.S. health survey. The hypertension pipeline
   joins the official demographic, body-measure, smoking, and blood-pressure
   components. It uses repeated measured blood pressure only to create the
   training label; the model itself uses age, sex, BMI, and smoking history.
   Official data catalogue: https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Demographics&Cycle=2021-2023

The first two mirrors are commonly used, unmodified re-hosts of their
original public datasets. If either URL ever goes down, search for "pima
indians diabetes csv" or "UCI heart disease heart.csv" — any mirror with
the same column names will work as a drop-in replacement. The NHANES files
are retrieved directly from CDC/NCHS and should retain their published names.
"""
import os
import urllib.request

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw")
os.makedirs(RAW_DIR, exist_ok=True)

SOURCES = {
    "diabetes_raw.csv": "https://github.com/npradaschnor/Pima-Indians-Diabetes-Dataset/raw/refs/heads/master/diabetes.csv",
    "heart_raw.csv": "https://github.com/sharmaroshan/Heart-UCI-Dataset/raw/refs/heads/master/heart.csv",
    "nhanes_demographics_2021_2023.xpt": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.XPT",
    "nhanes_body_measures_2021_2023.xpt": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BMX_L.XPT",
    "nhanes_smoking_2021_2023.xpt": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/SMQ_L.XPT",
    "nhanes_blood_pressure_2021_2023.xpt": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BPXO_L.XPT",
}


def download(filename, url):
    dest = os.path.join(RAW_DIR, filename)
    print(f"Downloading {url} -> {dest}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
        f.write(resp.read())
    size_kb = os.path.getsize(dest) / 1024
    print(f"  Saved {size_kb:.1f} KB")


if __name__ == "__main__":
    for filename, url in SOURCES.items():
        try:
            download(filename, url)
        except Exception as e:
            print(f"  FAILED to download {filename}: {e}")
            print(
                "  You can download it manually from the source URL above and "
                f"place it at {os.path.join(RAW_DIR, filename)}"
            )
    print("\nDone. Next, run: python3 ml/datasets/prepare_real_data.py")
