import os
import json
import uuid
import mimetypes
from urllib.request import Request, urlopen


def send_to_localsend(filepath, target_ip, port=53317):
    filename = os.path.basename(filepath)
    size = os.path.getsize(filepath)
    file_id = str(uuid.uuid4())
    mime = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'

    prepare_payload = {
        "info": {
            "alias": "Calibre",
            "version": "2.0",
            "deviceModel": "Calibre",
            "deviceType": "desktop",
            "fingerprint": str(uuid.uuid4()),
            "port": port,
            "protocol": "http",
            "download": False
        },
        "files": {
            file_id: {
                "id": file_id,
                "fileName": filename,
                "size": size,
                "fileType": mime,
                "preview": None
            }
        }
    }

    url = f"http://{target_ip}:{port}/api/localsend/v2/prepare-upload"
    req = Request(
        url,
        data=json.dumps(prepare_payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urlopen(req, timeout=60) as r:
        resp = json.loads(r.read())

    session_id = resp['sessionId']
    token = resp['files'][file_id]

    upload_url = (
        f"http://{target_ip}:{port}/api/localsend/v2/upload"
        f"?sessionId={session_id}&fileId={file_id}&token={token}"
    )

    with open(filepath, 'rb') as f:
        data = f.read()

    req = Request(
        upload_url,
        data=data,
        headers={'Content-Type': 'application/octet-stream'}
    )
    with urlopen(req, timeout=300) as r:
        r.read()