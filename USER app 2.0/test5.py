import os

folder = r"C:\Users\123\Downloads\traffic"

files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]

# Phase 1
for i, f in enumerate(files):
    base, ext = os.path.splitext(f)
    os.rename(
        os.path.join(folder, f),
        os.path.join(folder, f"__temp__{i}{ext}")
    )

# Phase 2
counter = 1
for f in sorted(os.listdir(folder)):
    base, ext = os.path.splitext(f)
    os.rename(
        os.path.join(folder, f),
        os.path.join(folder, f"{counter}{ext}")
    )
    counter += 1
