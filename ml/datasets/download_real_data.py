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

4. UCI Chronic Kidney Disease Dataset
   400 hospital records, 24 features and a CKD/not-CKD class. It is retrieved
   through UCI's supported ``ucimlrepo`` client because the catalogue's direct
   download is RAR-compressed. The prepared data keeps only the numeric,
   patient-enterable fields used by this application.

5. CDC BRFSS 2023
   The annual Behavioral Risk Factor Surveillance System has 433,323 survey
   records. The stroke pipeline keeps only eight survey fields that match the
   assistant questions and uses the participant's response to the question
   about ever being told they had a stroke as the target. It is a screening
   association, not a forecast of a first stroke or a diagnosis.
"""
import os
import urllib.request
import tempfile
import zipfile

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

BRFSS_URL = "https://www.cdc.gov/brfss/annual_data/2023/files/LLCP2023XPT.zip"


def download(filename, url):
    dest = os.path.join(RAW_DIR, filename)
    print(f"Downloading {url} -> {dest}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
        f.write(resp.read())
    size_kb = os.path.getsize(dest) / 1024
    print(f"  Saved {size_kb:.1f} KB")


def download_brfss():
    """Download just the XPT member from CDC's published ZIP archive."""
    destination = os.path.join(RAW_DIR, "brfss_2023.xpt")
    print(f"Downloading BRFSS 2023 source archive -> {destination}")
    request = urllib.request.Request(BRFSS_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=300) as response:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as archive_file:
            archive_path = archive_file.name
            try:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    archive_file.write(chunk)
                with zipfile.ZipFile(archive_path) as archive:
                    member = next(
                        name for name in archive.namelist()
                        if name.rstrip().upper() == "LLCP2023.XPT"
                    )
                    with archive.open(member) as source, open(destination, "wb") as target:
                        while True:
                            chunk = source.read(1024 * 1024)
                            if not chunk:
                                break
                            target.write(chunk)
            finally:
                os.unlink(archive_path)
    print(f"  Saved {os.path.getsize(destination) / 1024 / 1024:.1f} MB")


def download_ckd():
    """Fetch the official UCI data in a flat CSV form used by preparation."""
    try:
        from ucimlrepo import fetch_ucirepo
    except ImportError as exc:
        raise RuntimeError(
            "ucimlrepo is required for the UCI Chronic Kidney Disease download. "
            "Run `pip install -r requirements.txt` first."
        ) from exc

    print("Downloading UCI Chronic Kidney Disease Dataset -> ckd_uci.csv")
    dataset = fetch_ucirepo(id=336)
    df = dataset.data.features.copy()
    df["class"] = dataset.data.targets.iloc[:, 0]
    destination = os.path.join(RAW_DIR, "ckd_uci.csv")
    df.to_csv(destination, index=False)
    print(f"  Saved {df.shape[0]} rows")


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
    for label, func in (("ckd_uci.csv", download_ckd), ("brfss_2023.xpt", download_brfss)):
        try:
            func()
        except Exception as e:
            print(f"  FAILED to download {label}: {e}")
            print(f"  You can manually place {label} in {RAW_DIR} and re-run preparation.")
    print("\nDone. Next, run: python3 ml/datasets/prepare_real_data.py")
