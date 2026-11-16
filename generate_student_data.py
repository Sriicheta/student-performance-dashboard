"""
generate_student_data.py
========================

Standalone helper that regenerates ``student_data.csv`` from scratch using the
fixed random seed defined in ``modules/data_manager.py``.

Usage::

    python generate_student_data.py
"""

from modules import data_manager as dm


def main() -> None:
    df = dm.create_sample_dataset(dm.DATA_FILE, seed=42)
    print(f"Created {dm.DATA_FILE.name} with {len(df)} synthetic student records.")


if __name__ == "__main__":
    main()
