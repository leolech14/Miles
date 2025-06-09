#!/usr/bin/env python3
"""
PDF to CSV processing script for all PDFs in the all_pdfs/ directory.
This script will process each PDF and create a corresponding CSV file.
"""

import glob
import os
from pathlib import Path
from typing import Any

import pandas as pd


def find_pdf_files(directory: str = "all_pdfs") -> list[str]:
    """Find all PDF files in the specified directory."""
    pdf_pattern = os.path.join(directory, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)
    return pdf_files


def process_pdf_to_csv(pdf_path: str) -> str:
    """
    Process a single PDF file and create a CSV file.
    This is a placeholder - implement your specific PDF parsing logic here.
    """
    pdf_name = Path(pdf_path).stem
    csv_path = os.path.join(os.path.dirname(pdf_path), f"{pdf_name}.csv")

    # Placeholder data - replace with actual PDF parsing logic
    placeholder_data = {
        "pdf_source": [pdf_path],
        "processed_date": [pd.Timestamp.now()],
        "status": ["placeholder_data"],
        "note": ["Replace this with actual PDF parsing logic"],
    }

    df = pd.DataFrame(placeholder_data)
    df.to_csv(csv_path, index=False, sep=";")

    return csv_path


def process_all_pdfs() -> dict[str, Any]:
    """Process all PDFs in the directory and return summary statistics."""

    # Check if directory exists
    if not os.path.exists("all_pdfs"):
        print("Creating all_pdfs/ directory...")
        os.makedirs("all_pdfs", exist_ok=True)
        return {
            "status": "directory_created",
            "message": "all_pdfs/ directory created. Add PDF files and run again.",
            "pdfs_found": 0,
            "csvs_created": 0,
        }

    # Find PDF files
    pdf_files = find_pdf_files()

    if not pdf_files:
        return {
            "status": "no_pdfs_found",
            "message": "No PDF files found in all_pdfs/ directory.",
            "pdfs_found": 0,
            "csvs_created": 0,
        }

    # Process each PDF
    csvs_created = []
    errors = []

    for pdf_path in pdf_files:
        try:
            csv_path = process_pdf_to_csv(pdf_path)
            csvs_created.append(csv_path)
            print(f"✅ Processed: {pdf_path} -> {csv_path}")
        except Exception as e:
            errors.append(f"❌ Error processing {pdf_path}: {e!s}")
            print(f"❌ Error processing {pdf_path}: {e!s}")

    return {
        "status": "completed",
        "pdfs_found": len(pdf_files),
        "csvs_created": len(csvs_created),
        "errors": len(errors),
        "csv_files": csvs_created,
        "error_details": errors,
    }


def main():
    """Main function to process all PDFs."""
    print("🔄 Processing PDFs in all_pdfs/ directory...")

    result = process_all_pdfs()

    print("\n📊 Summary:")
    print(f"   Status: {result['status']}")
    print(f"   PDFs found: {result['pdfs_found']}")
    print(f"   CSVs created: {result['csvs_created']}")

    if result.get("errors", 0) > 0:
        print(f"   Errors: {result['errors']}")
        for error in result.get("error_details", []):
            print(f"     {error}")

    if result["status"] == "completed" and result["csvs_created"] > 0:
        print("\n✅ All CSV files created in all_pdfs/ directory")
        print("   Next steps:")
        print("   1. Review the generated CSV files")
        print("   2. Set up DuckDB MCP server to analyze the data")
        print("   3. Import CSVs into DuckDB for analysis")


if __name__ == "__main__":
    main()
