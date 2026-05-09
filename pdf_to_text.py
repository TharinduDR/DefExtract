from pathlib import Path
import pytesseract
from pdf2image import convert_from_path
from tqdm import tqdm
from huggingface_hub import snapshot_download

# ── CONFIG ──────────────────────────────────────────────
repo_id = "tharindu/textbooks"
language = "Sinhala"          # change to "English" or "Tamil" later
ocr_lang = "sin"              # tesseract code: sin / eng / tam
output_root = Path("/content/epub_txt")   # local path
dpi = 200
overwrite = False             # set True to redo files that already have output
# ────────────────────────────────────────────────────────

# 1. Download all PDFs for the chosen language in one go.
print(f"Downloading {language} PDFs from {repo_id} ...")
local_dir = Path(snapshot_download(
    repo_id=repo_id,
    repo_type="dataset",
    allow_patterns=[f"{language}/**/*.pdf"],
))
print(f"Downloaded to {local_dir}")

# 2. Walk every PDF and OCR it.
pdf_paths = sorted((local_dir / language).rglob("*.pdf"))
print(f"Found {len(pdf_paths)} {language} PDF(s)")

errors = []
for pdf_path in tqdm(pdf_paths, desc=f"{language} PDFs"):
    # Mirror the language/grade/... structure under output_root.
    rel = pdf_path.relative_to(local_dir)          # e.g. Sinhala/Grade_10/foo.pdf
    out_path = (output_root / rel).with_suffix(".txt")

    if out_path.exists() and out_path.stat().st_size > 0 and not overwrite:
        continue

    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        images = convert_from_path(str(pdf_path), dpi=dpi)
    except Exception as e:
        errors.append((rel, f"convert_from_path failed: {e}"))
        continue

    tmp_path = out_path.with_suffix(out_path.suffix + ".part")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            for i, image in enumerate(tqdm(images, desc=pdf_path.name, leave=False)):
                try:
                    text = pytesseract.image_to_string(image, lang=ocr_lang)
                except Exception as e:
                    text = f"[OCR error on page {i+1}: {e}]"
                f.write(f"Page {i + 1}\n{text}\n")
                f.write("=" * 50 + "\n")
        tmp_path.replace(out_path)
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        errors.append((rel, f"write failed: {e}"))
    finally:
        del images

print(f"\nDone. {len(pdf_paths) - len(errors)} succeeded, {len(errors)} failed.")
for p, msg in errors:
    print(f"  FAIL: {p}  -> {msg}")