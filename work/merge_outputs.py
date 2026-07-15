"""
Merge partial output files into one complete document.
Usage: python merge_outputs.py output_prefix
"""
import os, sys, glob

def merge(prefix="", output_name="merged_complete.md"):
    work_dir = "/workspace/work"
    # Find all part files matching pattern
    pattern = f"{work_dir}/{prefix}part_*.md" if prefix else f"{work_dir}/part_*.md"
    part_files = sorted(glob.glob(pattern))
    
    if not part_files:
        print(f"No part files found: {pattern}")
        return
    
    print(f"Found {len(part_files)} part files:")
    full = []
    for f in part_files:
        with open(f, "r", encoding="utf-8") as fh:
            content = fh.read()
        full.append(content)
        print(f"  {os.path.basename(f)}: {len(content)} chars")
    
    merged = "\n\n".join(full)
    out_path = f"{work_dir}/{output_name}"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(merged)
    print(f"\nMerged: {out_path} ({len(merged)} total chars)")

if __name__ == "__main__":
    prefix = sys.argv[1] if len(sys.argv) > 1 else ""
    out = sys.argv[2] if len(sys.argv) > 2 else "merged_complete.md"
    merge(prefix, out)
