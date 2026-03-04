#!/usr/bin/env python3
"""Script to inspect the Scavolini transcodification table structure."""

from BE.scavolini_loader import ScavoliniTranscodificationLoader

def main():
    loader = ScavoliniTranscodificationLoader()
    
    print("=" * 80)
    print("SCAVOLINI TRANSCODIFICATION TABLE STRUCTURE")
    print("=" * 80)
    print()
    
    # Get column names only (fast, doesn't load full data)
    print("📋 Loading column names...")
    columns = loader.load_columns_only()
    
    print(f"\n✅ Found {len(columns)} columns:\n")
    for i, col in enumerate(columns, 1):
        print(f"  {i:2d}. {col}")
    
    print("\n" + "=" * 80)
    print("COLUMN DATA TYPES (from first 10 rows)")
    print("=" * 80)
    print()
    
    column_info = loader.get_column_info()
    for col, dtype in column_info.items():
        print(f"  {col:40s} → {dtype}")
    
    print("\n" + "=" * 80)
    print("KEY COLUMNS FOR TRANSCODIFICATION")
    print("=" * 80)
    print()
    
    # Identify key columns based on XML structure
    key_columns = [
        "COD_ART_CLIENTE",
        "C_MATPIANO",
        "C_COLPIANO", 
        "C_FINPIANO",
        "C_PROFPIANO"
    ]
    
    print("Expected key columns from XML:")
    for col in key_columns:
        if col in columns:
            print(f"  ✅ {col} - FOUND")
        else:
            print(f"  ❌ {col} - NOT FOUND")
    
    print("\n" + "=" * 80)
    print("MAGO4 CODE COLUMN")
    print("=" * 80)
    print()
    
    # Try to identify the Mago4 code column
    mago_candidates = [col for col in columns if 'mago' in col.lower() or 'codice' in col.lower()]
    
    if mago_candidates:
        print("Possible Mago4 code columns:")
        for col in mago_candidates:
            print(f"  • {col}")
    else:
        print("⚠️  No obvious Mago4 code column found")
        print("    All columns:")
        for col in columns:
            print(f"    • {col}")

if __name__ == "__main__":
    main()
