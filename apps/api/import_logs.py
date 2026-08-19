import json
import uuid
import urllib.request
import urllib.error
import os
from urllib.parse import urlparse

log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'events.log')

count = 0
duplicates = 0
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except:
            continue
        
        event_type = data.get("event") or data.get("type") or "unknown"
        page_title = data.get("pageTitle") or data.get("title") or ""
        input_text = data.get("input") or data.get("text") or ""
        url = data.get("url", "")
        domain = ""
        if url:
            try:
                domain = urlparse(url).netloc
            except:
                pass
        
        # Collect all other fields into metadata
        metadata = {}
        standard_keys = {"timestamp", "event", "type", "pageTitle", "title", "input", "text", "url", "content"}
        for k, v in data.items():
            if k not in standard_keys:
                metadata[k] = v
        
        payload = {
            "event_id": str(uuid.uuid4()),
            "timestamp": data.get("timestamp"),
            "event_type": event_type,
            "url": url,
            "domain": domain,
            "page_title": page_title,
            "content": data.get("content", ""),
            "input_text": input_text,
            "metadata": metadata,
            "source": "import_script"
        }
        
        req = urllib.request.Request(
            'http://localhost:8000/api/v1/events', 
            data=json.dumps(payload).encode('utf-8'), 
            headers={'Content-Type': 'application/json'}, 
            method='POST'
        )
        try:
            urllib.request.urlopen(req)
            count += 1
        except urllib.error.HTTPError as e:
            msg = e.read().decode()
            if e.code == 409 or "already exists" in msg.lower():
                duplicates += 1
            else:
                print("Failed to post event:", msg)

print(f"Successfully imported {count} new events! (Skipped {duplicates} duplicates)")
