import csv
import importlib.util
from pathlib import Path
import pytest

SAMPLE_CSV_ROWS = [
    # period, ward, category, budgeted_amount, actual_spend, notes
    # Ward 1 — Roads series (include base months to produce the reference MoM values)
    ("2024-06", "Ward 1 – Kasba", "Roads & Pothole Repair", "0", "14.81", ""),
    ("2024-07", "Ward 1 – Kasba", "Roads & Pothole Repair", "0", "19.70", ""),
    ("2024-08", "Ward 1 – Kasba", "Roads & Pothole Repair", "0", "18.50", ""),
    ("2024-09", "Ward 1 – Kasba", "Roads & Pothole Repair", "0", "20.09", ""),
    ("2024-10", "Ward 1 – Kasba", "Roads & Pothole Repair", "0", "13.10", ""),
    # The five deliberate NULL rows (actual_spend empty) with notes
    ("2024-03", "Ward 2 – Shivajinagar", "Drainage & Flooding", "0", "", "Survey pending"),
    ("2024-07", "Ward 4 – Warje", "Roads & Pothole Repair", "0", "", "Contractor delay"),
    ("2024-11", "Ward 1 – Kasba", "Waste Management", "0", "", "Data not reported"),
    ("2024-08", "Ward 3 – Kothrud", "Parks & Greening", "0", "", "Site closed"),
    ("2024-05", "Ward 5 – Hadapsar", "Streetlight Maintenance", "0", "", "Meter failure"),
    # Some extra filler rows to ensure parsing/order correctness
    ("2024-01", "Ward 1 – Kasba", "Roads & Pothole Repair", "0", "10.00", ""),
    ("2024-02", "Ward 1 – Kasba", "Roads & Pothole Repair", "0", "12.00", ""),
]

def write_sample_csv(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["period", "ward", "category", "budgeted_amount", "actual_spend", "notes"])
        writer.writerows(SAMPLE_CSV_ROWS)

def load_app_module(app_path: Path):
    spec = importlib.util.spec_from_file_location("uc0c_app", str(app_path))
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)  # type: ignore
    return app

def test_five_null_rows_flagged_and_reference_values(tmp_path):
    # Arrange: write CSV
    csv_path = tmp_path / "ward_budget.csv"
    write_sample_csv(csv_path)

    # Load app.py from the UC-0C directory (assumes app.py exists next to tests folder parent)
    repo_dir = Path(__file__).resolve().parents[1]
    app_path = repo_dir / "app.py"
    assert app_path.exists(), f"Expected app.py at {app_path} (create it if missing)."

    app = load_app_module(app_path)

    # Act: load dataset
    df = app.load_dataset(str(csv_path))

    # Assert 1: exactly five NULL actual_spend rows present
    null_count = int(df["actual_spend"].isna().sum())
    assert null_count == 5, f"Expected 5 NULL actual_spend rows, found {null_count}"

    # Act: compute MoM growth for Ward 1 – Kasba / Roads & Pothole Repair
    out = app.compute_growth(df, "Ward 1 – Kasba", "Roads & Pothole Repair", "MoM")

    # Helper to extract numeric growth from formula string ("MoM: (... ) = 0.3310")
    def extract_growth_from_formula(formula: str) -> float:
        # formula contains "=" followed by numeric value
        rhs = formula.split("=")[-1].strip()
        return float(rhs)

    # Assert 2: reference month 2024-07 -> ~+33.1% (0.331)
    row_jul = out[out["period"] == "2024-07"].iloc[0]
    growth_jul = extract_growth_from_formula(row_jul["formula"])
    assert pytest.approx(0.331, rel=1e-3) == growth_jul

    # Assert 3: reference month 2024-10 -> ~-34.8% (-0.348)
    row_oct = out[out["period"] == "2024-10"].iloc[0]
    growth_oct = extract_growth_from_formula(row_oct["formula"])
    assert pytest.approx(-0.348, rel=1e-3) == growth_oct