"""
Fast, resumable MIT-BIH downloader (parallel). Uses PhysioNet's official public Amazon S3 mirror,
which is much faster than physionet.org. Run once:  python download_mitdb.py [target_folder]
Only needs the Python standard library. Re-run any time: finished files are skipped.
"""
import os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = os.environ.get("MITDB_BASE", "https://physionet-open.s3.amazonaws.com/mitdb/1.0.0/")
OUT = sys.argv[1] if len(sys.argv) > 1 else "mitdb"

DS1 = [101,106,108,109,112,114,115,116,118,119,122,124,201,203,205,207,208,209,215,220,223,230]
DS2 = [100,103,105,111,113,117,121,123,200,202,210,212,213,214,219,221,222,228,231,232,233,234]
FILES = [f"{r}.{e}" for r in DS1 + DS2 for e in ("hea", "dat", "atr")]

def fetch(name):
    dest = os.path.join(OUT, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return name, "skipped"
    for attempt in range(1, 9):
        try:
            with urllib.request.urlopen(BASE + name, timeout=60) as r:
                data = r.read()
                expected = r.headers.get("Content-Length")
            if expected and len(data) != int(expected):
                raise IOError(f"incomplete: {len(data)}/{expected} bytes")
            tmp = dest + ".part"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, dest)          # file appears only when fully downloaded
            return name, "ok"
        except Exception as e:
            time.sleep(min(2 * attempt, 15))
    return name, "FAILED"

os.makedirs(OUT, exist_ok=True)
done = 0
with ThreadPoolExecutor(max_workers=8) as ex:
    for name, status in ex.map(fetch, FILES):
        done += 1
        print(f"[{done}/{len(FILES)}] {name}: {status}", flush=True)
        if status == "FAILED":
            print("   (will report at the end)")
bad = [f for f in FILES if not os.path.exists(os.path.join(OUT, f))]
print("\nAll files present." if not bad else f"\nMissing {len(bad)} files, re-run the script: {bad[:5]}...")
