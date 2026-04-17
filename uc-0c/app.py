"""
UC-0C app.py — Budget Growth Calculator
Implements RICE framework with agents.md and skills.md enforcement rules.

Enforcement:
- Granular per-ward, per-category (never aggregate across wards/categories)
- Null-aware: flag every null actual_spend before calculation with reason from notes
- Formula-transparent: show exact formula in every output row
- Mode-explicit: growth_type (MoM or YoY) required from user, never assumed
- Refuse aggregation requests, missing growth_type, invalid ward/category
"""

import argparse
import csv
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

REQUIRED_COLUMNS = {"period", "ward", "category", "budgeted_amount", "actual_spend", "notes"}


class DatasetLoader:
    """Load and validate the budget CSV dataset."""
    
    def __init__(self, csv_file: str):
        self.filename = csv_file
        self.data = []
        self.columns = []
        self.validation_status = "FAIL"
        self.null_rows = []
        self.null_count = 0
        self.available_wards = set()
        self.available_categories = set()
        
    def load(self) -> Dict:
        """Load and validate the CSV file."""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.columns = reader.fieldnames if reader.fieldnames else []
                
                if not self.columns:
                    print(f"ERROR: CSV file is empty or has no header", file=sys.stderr)
                    sys.exit(1)
                
                # Validate required columns
                missing_cols = REQUIRED_COLUMNS - set(self.columns)
                if missing_cols:
                    print(f"ERROR: Missing required columns: {missing_cols}", file=sys.stderr)
                    sys.exit(1)
                
                # Read data rows
                row_num = 2  # Start at 2 (header is row 1)
                for row in reader:
                    self.data.append(row)
                    
                    # Track wards and categories
                    if row.get("ward"):
                        self.available_wards.add(row["ward"])
                    if row.get("category"):
                        self.available_categories.add(row["category"])
                    
                    # Identify null rows
                    actual_spend_str = row.get("actual_spend", "").strip()
                    if not actual_spend_str:
                        self.null_rows.append({
                            "period": row.get("period"),
                            "ward": row.get("ward"),
                            "category": row.get("category"),
                            "notes": row.get("notes", "No reason provided")
                        })
                        self.null_count += 1
                    
                    row_num += 1
        
        except FileNotFoundError:
            print(f"ERROR: File not found: {self.filename}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Failed to read CSV: {e}", file=sys.stderr)
            sys.exit(1)
        
        self.validation_status = "PASS"
        return self.to_dict()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary output format."""
        return {
            "filename": self.filename,
            "total_rows": len(self.data),
            "columns": self.columns,
            "validation_status": self.validation_status,
            "required_columns": list(REQUIRED_COLUMNS),
            "null_count": self.null_count,
            "null_rows": self.null_rows,
            "data": self.data,
            "available_wards": sorted(list(self.available_wards)),
            "available_categories": sorted(list(self.available_categories)),
            "load_timestamp": datetime.now().isoformat()
        }


class GrowthCalculator:
    """Calculate growth metrics for a ward+category combination."""
    
    def __init__(self, dataset: Dict, ward: str, category: str, growth_type: str):
        self.dataset = dataset
        self.ward = ward
        self.category = category
        self.growth_type = growth_type
        self.growth_rows = []
        self.null_flagged_periods = []
        self.computation_status = "FAILED"
        
    def validate_inputs(self) -> bool:
        """Validate ward, category, and growth_type."""
        # Validate growth_type
        if not self.growth_type:
            print(f"ERROR: growth_type required. Specify --growth-type MoM or --growth-type YoY", file=sys.stderr)
            return False
        
        if self.growth_type not in ["MoM", "YoY"]:
            print(f"ERROR: Invalid growth_type: {self.growth_type}. Must be 'MoM' or 'YoY'", file=sys.stderr)
            return False
        
        # Validate ward
        available_wards = self.dataset.get("available_wards", [])
        if self.ward not in available_wards:
            print(f"ERROR: Ward not found: {self.ward}", file=sys.stderr)
            print(f"Available wards: {', '.join(available_wards)}", file=sys.stderr)
            return False
        
        # Validate category
        available_categories = self.dataset.get("available_categories", [])
        if self.category not in available_categories:
            print(f"ERROR: Category not found: {self.category}", file=sys.stderr)
            print(f"Available categories: {', '.join(available_categories)}", file=sys.stderr)
            return False
        
        return True
    
    def compute(self) -> Dict:
        """Compute growth for the specified ward and category."""
        if not self.validate_inputs():
            sys.exit(1)
        
        # Filter data for this ward+category
        filtered_data = [
            row for row in self.dataset.get("data", [])
            if row.get("ward") == self.ward and row.get("category") == self.category
        ]
        
        if not filtered_data:
            print(f"ERROR: No data found for ward={self.ward} category={self.category}", file=sys.stderr)
            sys.exit(1)
        
        # Sort by period
        filtered_data.sort(key=lambda r: r.get("period", ""))
        
        # Identify null rows in this subset and flag them upfront
        null_periods_in_subset = {}
        for row in filtered_data:
            actual_spend_str = row.get("actual_spend", "").strip()
            if not actual_spend_str:
                null_periods_in_subset[row.get("period")] = row.get("notes", "No reason provided")
                self.null_flagged_periods.append({
                    "period": row.get("period"),
                    "reason": row.get("notes", "")
                })
        
        # Report nulls before calculation
        if self.null_flagged_periods:
            print(f"\nWARNING: Null values detected in {self.ward} / {self.category}:", file=sys.stderr)
            for null_row in self.null_flagged_periods:
                print(f"  {null_row['period']}: {null_row['reason']}", file=sys.stderr)
            print()
        
        # Build lookup of actual_spend by period
        spend_by_period = {}
        for row in filtered_data:
            period = row.get("period")
            actual_spend_str = row.get("actual_spend", "").strip()
            if actual_spend_str:
                try:
                    spend_by_period[period] = float(actual_spend_str)
                except ValueError:
                    print(f"WARNING: Invalid actual_spend value in {period}: {actual_spend_str}", file=sys.stderr)
        
        # Compute growth for each period
        computable_count = 0
        non_computable_count = 0
        
        for row in filtered_data:
            period = row.get("period")
            actual_spend = None
            
            # Parse current period's actual_spend
            actual_spend_str = row.get("actual_spend", "").strip()
            if actual_spend_str:
                try:
                    actual_spend = float(actual_spend_str)
                except ValueError:
                    pass
            
            # Determine previous period
            previous_period = self._get_previous_period(period)
            previous_spend = spend_by_period.get(previous_period)
            
            # Compute growth
            growth_percent = None
            formula_applied = ""
            flags = []
            
            if actual_spend is None:
                # Current period is null
                growth_percent = "N/A"
                reason = null_periods_in_subset.get(period, "Unknown")
                flags.append(f"#FLAG: NULL DATA in current period: {reason}")
                non_computable_count += 1
            elif previous_spend is None:
                # Previous period is null or missing
                if previous_period in null_periods_in_subset:
                    reason = null_periods_in_subset[previous_period]
                    flags.append(f"#FLAG: Cannot compute growth — NULL in required previous period: {reason}")
                else:
                    flags.append(f"#FLAG: No prior period available ({previous_period})")
                growth_percent = "N/A"
                non_computable_count += 1
            else:
                # Compute growth
                growth_val = (actual_spend - previous_spend) / previous_spend * 100
                growth_percent = round(growth_val, 1)
                formula_applied = f"({actual_spend} − {previous_spend}) / {previous_spend} × 100 = {growth_percent}%"
                computable_count += 1
            
            self.growth_rows.append({
                "period": period,
                "actual_spend": actual_spend if actual_spend is not None else None,
                "previous_period": previous_period,
                "previous_spend": previous_spend,
                "growth_percent": growth_percent,
                "formula_applied": formula_applied,
                "flags": " | ".join(flags) if flags else ""
            })
        
        # Determine computation status
        if computable_count == 0:
            self.computation_status = "FAILED"
        elif non_computable_count == 0:
            self.computation_status = "SUCCESS"
        else:
            self.computation_status = "PARTIAL"
        
        return self.to_dict()
    
    def _get_previous_period(self, period: str) -> str:
        """Get the previous period (for MoM or YoY)."""
        try:
            year, month = map(int, period.split("-"))
            
            if self.growth_type == "MoM":
                # Month-over-Month: previous month
                month -= 1
                if month == 0:
                    month = 12
                    year -= 1
            else:  # YoY
                # Year-over-Year: same month previous year
                year -= 1
            
            return f"{year:04d}-{month:02d}"
        except:
            return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary output format."""
        return {
            "ward": self.ward,
            "category": self.category,
            "growth_type": self.growth_type,
            "calculation_formula": f"{self.growth_type}: (current_spend − previous_spend) / previous_spend × 100",
            "growth_rows": self.growth_rows,
            "null_flagged_periods": self.null_flagged_periods,
            "computation_status": self.computation_status
        }


def main():
    """Main entry point for budget growth calculation."""
    parser = argparse.ArgumentParser(
        description="UC-0C Budget Growth Calculator — Compute ward/category-level spending growth metrics"
    )
    parser.add_argument("--input", required=True, help="Path to ward_budget.csv")
    parser.add_argument("--ward", required=True, help="Ward name (exact match required)")
    parser.add_argument("--category", required=True, help="Budget category (exact match required)")
    parser.add_argument("--growth-type", required=True, help="MoM (Month-over-Month) or YoY (Year-over-Year)")
    parser.add_argument("--output", required=True, help="Path to write growth output CSV")
    
    args = parser.parse_args()
    
    # Check for aggregation attempts
    if args.ward.lower() == "all" or args.category.lower() == "all":
        print(f"ERROR: Growth calculation per-ward, per-category only. Please specify ward and category.", file=sys.stderr)
        sys.exit(1)
    
    # Step 1: Load dataset
    print(f"Loading dataset from {args.input}...", file=sys.stderr)
    loader = DatasetLoader(args.input)
    dataset = loader.load()
    
    print(f"Loaded {dataset['total_rows']} rows with {dataset['null_count']} null values.", file=sys.stderr)
    
    # Step 2: Compute growth
    print(f"Computing {args.growth_type} growth for {args.ward} / {args.category}...", file=sys.stderr)
    calculator = GrowthCalculator(dataset, args.ward, args.category, args.growth_type)
    growth_result = calculator.compute()
    
    # Step 3: Write output
    try:
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                "period", "actual_spend", "previous_period", "previous_spend",
                "growth_percent", "formula_applied", "flags"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(growth_result["growth_rows"])
        
        print(f"Growth calculation written to {args.output}", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: Failed to write output file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Step 4: Report summary
    print(f"\n=== GROWTH CALCULATION SUMMARY ===", file=sys.stderr)
    print(f"Ward: {args.ward}", file=sys.stderr)
    print(f"Category: {args.category}", file=sys.stderr)
    print(f"Growth Type: {args.growth_type}", file=sys.stderr)
    print(f"Total periods: {len(growth_result['growth_rows'])}", file=sys.stderr)
    print(f"Null flagged periods: {len(growth_result['null_flagged_periods'])}", file=sys.stderr)
    
    if growth_result["null_flagged_periods"]:
        print(f"Flagged nulls:", file=sys.stderr)
        for null_row in growth_result["null_flagged_periods"]:
            print(f"  {null_row['period']}: {null_row['reason']}", file=sys.stderr)
    
    print(f"Computation status: {growth_result['computation_status']}", file=sys.stderr)
    print(f"Formula: {growth_result['calculation_formula']}", file=sys.stderr)
    
    if growth_result["computation_status"] == "FAILED":
        print(f"\nERROR: No growth could be computed (computation_status=FAILED)", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\n✓ Growth calculation complete", file=sys.stderr)


if __name__ == "__main__":
    main()
