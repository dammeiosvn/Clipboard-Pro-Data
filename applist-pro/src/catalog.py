"""Public interface packages. Personal app lists never belong in this catalog."""
from pathlib import Path
import base64
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.1.0-beta.4'
DATA_VERSION = '1.1.0-beta.1'
BASE_URL = 'https://raw.githubusercontent.com/dammeiosvn/Clipboard-Pro-Data/main/applist-pro/releases/' + DATA_VERSION + '/'
LANGUAGES = {
    'vi': 'Tiếng Việt', 'en': 'English', 'en-GB': 'English (UK)',
    'ja': '日本語', 'ko': '한국어', 'zh-Hans': '简体中文', 'zh-Hant': '繁體中文',
    'fr': 'Français', 'de': 'Deutsch', 'ru': 'Русский', 'es': 'Español',
    'th': 'ไทย', 'id': 'Bahasa Indonesia', 'tr': 'Türkçe', 'it': 'Italiano',
    'pt-BR': 'Português (Brasil)', 'hi': 'हिन्दी', 'ar': 'العربية',
    'nl': 'Nederlands', 'pl': 'Polski',
}
KEYS = 'manage add edit delete store language backups info back search paste rename pin unpin export import restore update cancel searchPrompt chooseApp namePrompt linkPrompt empty noResults exists badName invalidData saveFailed changedElsewhere missingStore added removed saved deleteConfirm replaceConfirm recovered infoBody'.split()


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def package(strings):
    payload = base64.b64encode(compact(strings).encode('utf-8')).decode('ascii')
    return {'format': 'applist-language-v1', 'payload': payload, 'sha256': digest(payload)}


def publish():
    catalog = json.loads((ROOT / 'config/strings.json').read_text())
    assert set(catalog) == set(LANGUAGES)
    out = ROOT / 'releases' / DATA_VERSION
    out.mkdir(parents=True, exist_ok=True)
    descriptors = {}
    for code, name in LANGUAGES.items():
        strings = catalog[code]
        assert set(strings) == set(KEYS), (code, set(KEYS) - set(strings))
        assert all(isinstance(s, str) and s.strip() and len(s) < 5000 for s in strings.values())
        assert len(set(strings[k] for k in KEYS[:19])) == 19, code
        env = package(strings)
        (out / (code + '.txt')).write_text(compact(env))
        (out / (code + '.json')).write_text(json.dumps(strings, ensure_ascii=False, indent=2) + '\n')
        descriptors[code] = {'name': name, 'sha256': env['sha256']}
    manifest = {'productId': 'applist-pro', 'schemaVersion': '2', 'version': DATA_VERSION,
                'author': '© Sentechtipsvn', 'languages': descriptors}
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return descriptors


if __name__ == '__main__':
    print(json.dumps(publish(), ensure_ascii=False))
