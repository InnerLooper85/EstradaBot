"""Find cores in mapping but not in inventory."""
import pandas as pd
from data_loader import DataLoader

loader = DataLoader()
loader.load_all()

# Get all core numbers from mapping
mapped_cores = set()
for part, data in loader.core_mapping.items():
    core_num = data.get('core_number')
    if core_num and not pd.isna(core_num):
        try:
            mapped_cores.add(int(float(core_num)))
        except:
            pass

# Get inventory cores
inventory_cores = set(loader.core_inventory.keys())

# Find missing
missing = sorted(mapped_cores - inventory_cores)

print("\n" + "=" * 70)
print(f"CORES IN MAPPING BUT NOT IN INVENTORY ({len(missing)} total)")
print("=" * 70)

# Count how many parts use each missing core
core_usage = {}
for part, data in loader.core_mapping.items():
    core_num = data.get('core_number')
    if core_num and not pd.isna(core_num):
        try:
            core_num = int(float(core_num))
            if core_num in missing:
                core_usage[core_num] = core_usage.get(core_num, 0) + 1
        except:
            pass

print("\nCore Number | Parts Using | Sample Description")
print("-" * 70)
for core in missing:
    # Find a sample part using this core
    sample_desc = ""
    for part, data in loader.core_mapping.items():
        c = data.get('core_number')
        if c and not pd.isna(c):
            try:
                if int(float(c)) == core:
                    sample_desc = str(data.get('description', ''))[:40]
                    break
            except:
                pass

    usage = core_usage.get(core, 0)
    print(f"  {core:>6}    | {usage:>5} parts | {sample_desc}")
