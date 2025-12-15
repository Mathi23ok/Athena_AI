# run_index_sync.py
import glob, os, time, traceback
from upload_ingest_faiss import process_and_index_faiss

uploads = glob.glob(os.path.join("uploads","*.pdf"))
if not uploads:
    print("No uploaded PDFs found in ./uploads. Upload a PDF first.")
    raise SystemExit(1)

pdf_path = uploads[-1]
print("Indexing (synchronously):", pdf_path)
start = time.time()
try:
    res = process_and_index_faiss(pdf_path, os.path.basename(pdf_path), "manual-run")
    print("Index result:", res)
except Exception:
    print("Indexing raised an exception — full traceback below:")
    traceback.print_exc()
finally:
    print("Elapsed (s):", time.time() - start)
