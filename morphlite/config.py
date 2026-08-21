"""Central configuration for MorphLite dataset workspace and source roots."""
from pathlib import Path

BRANDMORPH_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = BRANDMORPH_ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"
METADATA_DIR = DATA_DIR / "metadata"
EXTRACTED_DIR = DATA_DIR / "extracted"
PAIRS_DIR = DATA_DIR / "pairs"

# Sorted buckets inside data/source/
BUCKET_PAIRED_RAW = SOURCE_DIR / "paired" / "raw"
BUCKET_PAIRED_BRANDED = SOURCE_DIR / "paired" / "branded"
BUCKET_ALTERNATING = SOURCE_DIR / "alternating"
BUCKET_RAW_ONLY = SOURCE_DIR / "raw_only"
BUCKET_BRANDED_ONLY = SOURCE_DIR / "branded_only"
BUCKET_TEMPLATE = SOURCE_DIR / "template"
BUCKET_REVIEW = SOURCE_DIR / "review"

# Source dataset roots (read-only; originals are never modified).
# Each entry: (batch_id, path, convention)
#   convention controls how raw/clean roles are detected:
#     filename_raw_suffix : "<name> raw.pptx" <-> "<name>.pptx" in same dir
#     folder_pair         : Raw\<name>.pptx <-> Updated\<name> v1.pptx
#     clean_only          : assumed branded reference decks
DOCUMENT_ROOTS = [
    ("10Dec", r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\10 Dec", "clean_only"),
    ("11June", r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\11 June", "clean_only"),
    ("12Dec", r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\12 Dec", "filename_raw_suffix"),
    ("21Jan", r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\21 Jan", "folder_pair"),
    ("25Oct", r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\25 Oct", "filename_raw_suffix"),
]

# Decks whose raw/branded slides alternate INSIDE a single deck (Category B).
ALTERNATING_CONFIRMED_SUBSTRINGS = [
    "it infrastructure",
    "network engineering",
]
# Whole subtrees whose decks are Category B candidates pending slide-level validation.
ALTERNATING_CANDIDATE_PATH_PARTS = [
    r"case study initiative\old",
]

# Known brand template assets.
TEMPLATE_HINTS = ["akkodis new ppt template", "akkodis_guidelines"]
TEMPLATE_EXACT = {"template.pptx"}

# Parent-folder names that indicate a role (folder_pair convention).
RAW_FOLDER_NAMES = {"raw"}
CLEAN_FOLDER_NAMES = {"updated", "cleaned", "clean", "branded"}

# OneDrive download trees that duplicate other roots: verify before trusting role heuristics.
DUPLICATE_CHECK_PATH_PARTS = [
    r"onedrive_2025-11-26",
    r"onedrive_3_10-21-2025",
]
