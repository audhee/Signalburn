import os
import zipfile
import gdown
from pathlib import Path

FILE_ID = "1ntZ65ESAw3R7kER9mqwtq9ptKxBoMq5g"

ZIP_PATH = "/tmp/chroma.zip"
EXTRACT_DIR = "/tmp/chroma"


def ensure_chroma_db():
    db_file = os.path.join(
        EXTRACT_DIR,
        "sashwat_chroma_db",
        "chroma.sqlite3"
    )

    if os.path.exists(db_file):
        print("CHROMA DB ALREADY EXISTS")
        return

    # Local development DB already exists
    local_db = (
        Path(__file__).parent.parent.parent
        / "knowledge_base"
        / "sashwat_chroma_db"
        / "chroma.sqlite3"
    )

    if local_db.exists():
        print("USING LOCAL CHROMA DB")
        return

    os.makedirs(EXTRACT_DIR, exist_ok=True)

    print("DOWNLOADING CHROMA DB")

    gdown.download(
        id=FILE_ID,
        output=ZIP_PATH,
        quiet=False
    )

    print("EXTRACTING CHROMA DB")

    with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
        zip_ref.extractall(EXTRACT_DIR)

    print("CHROMA DB READY")
