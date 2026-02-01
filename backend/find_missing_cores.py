"""Find parts missing core number assignment."""
import pandas as pd
from data_loader import DataLoader

loader = DataLoader()
loader.load_all()

missing = [p for p, d in loader.core_mapping.items() if pd.isna(d.get('core_number'))]

print("\n" + "=" * 70)
print(f"PARTS MISSING CORE NUMBER ASSIGNMENT ({len(missing)} total)")
print("=" * 70)

for p in missing:
    data = loader.core_mapping[p]
    desc = data.get('description', 'N/A')
    rubber = data.get('rubber_type', 'N/A')
    print(f"  {p}: {desc} (Rubber: {rubber})")
