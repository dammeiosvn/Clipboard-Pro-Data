"""Build-time signing via Shortcuty's documented public API; never part of the iOS workflow.

Uploads only this public, generated workflow. No personal list or iCloud data is read.
API: https://github.com/Shortcuty/Signing-Server-API-Documentation
"""
from pathlib import Path
import base64
import hashlib
import json
import plistlib
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'https://sign.shortcuty.app/api/v1/sign?response=json'


def main():
    source = ROOT / 'dist/AppList-Pro.unsigned.bplist'
    raw = source.read_bytes()
    assert plistlib.loads(raw) == plistlib.loads((ROOT / 'dist/AppList-Pro.unsigned.shortcut').read_bytes())
    boundary = 'AppListPro-' + uuid.uuid4().hex
    header = ('--' + boundary + '\r\nContent-Disposition: form-data; name="file"; '
              'filename="AppList-Pro.shortcut"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()
    body = header + raw + ('\r\n--' + boundary + '--\r\n').encode()
    request = urllib.request.Request(ENDPOINT, data=body, headers={
        'Content-Type': 'multipart/form-data; boundary=' + boundary,
        'User-Agent': 'AppListPro-Build/1.1', 'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=55) as response:
        result = json.load(response)
    assert result.get('success') is True, result.get('error')
    item = result['file']
    content = base64.b64decode(item['content_base64'], validate=True)
    assert item['input_sha256'] == hashlib.sha256(raw).hexdigest()
    assert item['signed_sha256'] == hashlib.sha256(content).hexdigest()
    assert item['format'] == 'AEA1' and item['signing_mode'] == 'anyone'
    assert content.startswith(b'AEA1') and len(content) == item['size']
    dest = ROOT / 'dist/AppList-Pro-1.1-beta3.shortcut'
    dest.write_bytes(content)
    report = {'signed': True, 'format': 'AEA1', 'mode': 'anyone', 'bytes': len(content),
              'sha256': item['signed_sha256'], 'inputSHA256': item['input_sha256'],
              'nativeDeviceVerified': False}
    (ROOT / 'qa/signing.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
