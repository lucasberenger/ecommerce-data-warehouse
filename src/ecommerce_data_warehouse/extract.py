from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA = PROJECT_ROOT / "data" / "raw"

def read_csv(filename: str) -> pd.DataFrame:
    return pd.read_csv(RAW_DATA / filename)