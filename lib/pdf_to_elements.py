import requests, time, zipfile, os, json, io

TOKEN = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI0NjkwMDgwNiIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc3MTE4NTg2NywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiNmI0OWI0OWQtMWEzZi00MmQ5LWJlY2MtMTViMGJhNzA0MWY3IiwiZW1haWwiOiIiLCJleHAiOjE3Nzg5NjE4Njd9.1xihdazAQG9trnRIub0vZ7h41yy-PvcIk_swXSFM8sI5lIA1WexSTpvtk0R5DXI-ujmcbeX8MYRG9pGV7AvVRw"
CREATE_URL = "https://mineru.net/api/v4/extract/task"
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}

def create_task(pdf_path):
    payload = {
        "url": pdf_path,
        "model_version": "vlm",
        "output_format": "json",
        "extract_config": {
            "enable_ocr": False,
            "enable_image": False,
            "enable_formula": False
        }
    }
    res = requests.post(CREATE_URL, headers=HEADERS, json=payload)
    data = res.json()
    if "data" not in data or "task_id" not in data["data"]:
        raise Exception(f"API did not return task_id: {data}")
    return data["data"]["task_id"]


def wait_for_result(task_id, timeout=300):
    url = f"https://mineru.net/api/v4/extract/task/{task_id}"
    start = time.time()
    while True:
        r = requests.get(url, headers=HEADERS)
        data = r.json().get("data", {})
        state = data.get("state")
        if state in ("done", "success"):
            return data
        if state in ("failed", "error"):
            raise Exception(data.get("err_msg") or "Task failed")
        if time.time() - start > timeout:
            raise TimeoutError("Timeout waiting for task")
        time.sleep(5)

def download_and_extract_zip(zip_url):
    r = requests.get(zip_url)
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        extracted = {name: zf.read(name).decode("utf-8") for name in zf.namelist() if name.endswith("_content_list.json")}
        return extracted

def extract_ad_tables(extracted_jsons):
    ad_2_10, ad_2_12 = [], []

    for content_str in extracted_jsons.values():
        data = json.loads(content_str)
        items = data if isinstance(data, list) else data.get("items", [])
        for idx, item in enumerate(items):
            if item.get("type") != "table":
                continue
            captions = item.get("table_caption", [])
            caption_text = " ".join(captions).upper() if captions else ""
            prev_text = ""
            if idx > 0 and items[idx-1].get("type") == "text":
                prev_text = items[idx-1].get("text", "").upper()
            combined = prev_text + " " + caption_text
            html = item.get("table_body", "")
            if "AD 2.10" in combined:
                ad_2_10.append(html)
            elif "AD 2.12" in combined:
                ad_2_12.append(html)

    return {"AD_2_10": ad_2_10, "AD_2_12": ad_2_12}

def pdf_path_to_elements(pdf_path):
    task_id = create_task(pdf_path)
    result = wait_for_result(task_id)
    zip_url = result.get("full_zip_url")
    if not zip_url:
        raise Exception("No ZIP URL found")
    extracted_jsons = download_and_extract_zip(zip_url)
    tables = extract_ad_tables(extracted_jsons)
    return tables