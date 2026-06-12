import os
import zipfile
from pathlib import Path

CHROMA_DIR = "/tmp/chroma"
ZIP_FILE = "/tmp/chroma.zip"

# Local paths where the chroma DB may already exist
LOCAL_KB_DIR = Path(__file__).parent.parent.parent / "knowledge_base" / "sashwat_chroma_db"
LOCAL_ZIP = Path(__file__).parent.parent.parent.parent / "sashwat_chroma_db.zip"

def ensure_chroma_db() -> str:
    """Ensure the Chroma DB is available.

    Priority:
      1. Already downloaded to /tmp/chroma/sashwat_chroma_db
      2. Local knowledge_base/sashwat_chroma_db (bundled with repo)
      3. Local sashwat_chroma_db.zip (extract to /tmp/chroma)
      4. Download from CHROMA_DB_URL env var (Railway / cloud)

    Returns the path to the chroma DB directory.
    """
    # 1. Already present in /tmp
    tmp_db = f"{CHROMA_DIR}/sashwat_chroma_db/chroma.sqlite3"
    if os.path.exists(tmp_db):
        print("Chroma DB already exists at /tmp/chroma")
        return f"{CHROMA_DIR}/sashwat_chroma_db"

    # 2. Local knowledge_base copy
    local_kb = LOCAL_KB_DIR / "chroma.sqlite3"
    if local_kb.exists():
        print(f"Using local Chroma DB from {LOCAL_KB_DIR}")
        return str(LOCAL_KB_DIR)

    # 3. Local zip file
    if LOCAL_ZIP.exists():
        print(f"Extracting local zip: {LOCAL_ZIP}")
        os.makedirs(CHROMA_DIR, exist_ok=True)
        with zipfile.ZipFile(str(LOCAL_ZIP), "r") as zip_ref:
            zip_ref.extractall(CHROMA_DIR)
        if os.path.exists(tmp_db):
            print("Chroma DB extracted from local zip")
            return f"{CHROMA_DIR}/sashwat_chroma_db"

    # 4. Download from URL
    url = os.getenv("CHROMA_DB_URL")
    if not url:
        print("WARNING: CHROMA_DB_URL not set and no local Chroma DB found. "
              "RAG will not function.")
        return ""

    try:
        import requests
        print("Downloading Chroma DB from URL...")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        os.makedirs(CHROMA_DIR, exist_ok=True)
        with open(ZIP_FILE, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        print("Extracting Chroma DB...")
        with zipfile.ZipFile(ZIP_FILE, "r") as zip_ref:
            zip_ref.extractall(CHROMA_DIR)

        print("Chroma DB ready")
        return f"{CHROMA_DIR}/sashwat_chroma_db"
    except Exception as exc:
        print(f"ERROR downloading Chroma DB: {exc}")
        return ""