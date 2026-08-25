import json
import os
import time
from datetime import datetime, timezone

import requests

import processor

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
PRODUCT_ID = os.environ["PRODUCT_ID"]
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

REST_URL = "https://njyvnmczoydsaewvfhyq.supabase.co/rest/v1"
NOTIFICATIONS_URL = f"{REST_URL}/notifications"


def headers():
    return {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "apikey": SUPABASE_SERVICE_KEY,
        "Content-Type": "application/json",
    }


def download_file(bucket, file_path):
    if file_path.startswith(bucket + "/"):
        file_path = file_path[len(bucket) + 1:]
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{file_path}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}", "apikey": SUPABASE_SERVICE_KEY})
    resp.raise_for_status()
    return resp.content


def upload_result(bucket, file_path, content):
    if file_path.startswith(bucket + "/"):
        file_path = file_path[len(bucket) + 1:]
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{file_path}"
    resp = requests.post(url, headers={"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}", "apikey": SUPABASE_SERVICE_KEY}, data=content)
    resp.raise_for_status()
    return resp


def update_job(job_id, status, output_file_path, result_summary):
    data = {
        "status": status,
        "output_file_path": output_file_path,
        "result_summary": result_summary,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    resp = requests.patch(f"{REST_URL}/jobs?id=eq.{job_id}", headers=headers(), json=data)
    resp.raise_for_status()


def notify(customer_id, title, body, type_):
    try:
        data = {
            "product_id": PRODUCT_ID,
            "customer_id": customer_id,
            "title": title,
            "body": body,
            "type": type_,
            "read": False,
        }
        requests.post(NOTIFICATIONS_URL, headers=headers(), json=data)
    except Exception as exc:
        print(f"Notification error: {exc}")


def process_job(job):
    job_id = job["id"]
    customer_id = job["customer_id"]
    input_file_path = job["input_file_path"]

    try:
        file_bytes = download_file("uploads", input_file_path)
        records, summary = processor.process_file(file_bytes)

        output_file_path = f"results/{job_id}.json"
        output_content = json.dumps({
            "job_id": job_id,
            "product_id": PRODUCT_ID,
            "customer_id": customer_id,
            "summary": summary,
            "records": records,
        }, indent=2).encode("utf-8")

        upload_result("results", output_file_path, output_content)

        for record in records:
            data = {
                "product_id": PRODUCT_ID,
                "customer_id": customer_id,
                "title": record["title"],
                "status": record["status"],
                "details": record["details"],
                "source_file_path": input_file_path,
                "due_date": record.get("due_date"),
            }
            resp = requests.post(f"{REST_URL}/records", headers=headers(), json=data)
            resp.raise_for_status()

        update_job(job_id, "completed", output_file_path, summary)
        notify(customer_id, "Processing complete", "Your upload has been processed successfully.", "success")
    except Exception as exc:
        print(f"Job {job_id} failed: {exc}")
        try:
            update_job(job_id, "failed", None, f"Error: {str(exc)[:500]}")
            notify(customer_id, "Processing failed", "There was an error processing your upload.", "error")
        except Exception as inner_exc:
            print(f"Failed to update job {job_id}: {inner_exc}")


def poll():
    while True:
        try:
            params = {
                "status": "eq.pending",
                "job_type": "eq.process_upload",
                "product_id": f"eq.{PRODUCT_ID}",
                "select": "*",
                "limit": "10",
                "order": "created_at.asc",
            }
            resp = requests.get(f"{REST_URL}/jobs", headers=headers(), params=params)
            resp.raise_for_status()
            jobs = resp.json()
            for job in jobs:
                process_job(job)
        except Exception as exc:
            print(f"Poll error: {exc}")
        time.sleep(60)


if __name__ == "__main__":
    print("Poller started")
    poll()
