import csv
import io
import json


def extract_text(file_bytes):
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text = ""
            for p in pdf.pages:
                text += (p.extract_text() or "") + "\n"
            if text.strip():
                return text
    except Exception:
        pass
    return file_bytes.decode("utf-8", errors="ignore")


def process_file(file_bytes):
    text = extract_text(file_bytes)
    records = []
    try:
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        if rows:
            for i, row in enumerate(rows):
                title = row.get("description") or row.get("title") or row.get("name") or f"Record {i + 1}"
                details = {k: v for k, v in row.items() if v}
                records.append({
                    "title": title[:255],
                    "status": "Valid:good",
                    "details": json.dumps(details),
                    "due_date": None,
                })
            summary = f"Processed {len(records)} rows from CSV"
            return records, summary
    except Exception:
        pass
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines[:500]):
        records.append({
            "title": line[:255],
            "status": "Valid:good",
            "details": json.dumps({"line": i + 1, "content": line[:1000]}),
            "due_date": None,
        })
    summary = f"Processed {len(records)} records from text"
    return records, summary
