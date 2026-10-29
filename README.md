# Clipboard Pro — Official interface data

©️ Sentechtipsvn

Latest interface package: **1.6.0-beta.5**. Seven languages: Tiếng Việt (`vi`), English (`en`), Français (`fr-FR`), Deutsch (`de-DE`), Español (`es-ES`), 日本語 (`ja`), 한국어 (`ko-KR`). Each language contains the same 61 labels.

This repository stores public interface text and release manifests. Notes and clipboard content stay in the user’s own iCloud storage and are not sent to this repository.

Release files are immutable. The shortcut pins a commit URL and SHA-256 of the ASCII `payload` field in `catalog.txt`; JSON key order and outer whitespace do not affect verification. Base64 is encoding, not encryption or copy protection.

The beta.5 engine adds five languages, a clean About title and a viewer without a duplicate heading. Existing beta.3/beta.4 installations continue to use their pinned package. Install the beta.5 shortcut to access the seven-language catalog; keep the ClipboardPro folder and notes. The first upgrade needs internet to fetch the new compatible catalog, then valid cached interface data can work offline. Interface refresh reloads the pinned package and does not update the shortcut engine automatically.

- [Readable beta.5 catalog](releases/1.6.0-beta.5/catalog-readable.json)
- [Runtime beta.5 envelope](releases/1.6.0-beta.5/catalog.txt)
- [Manifest](releases/1.6.0-beta.5/manifest.json)

Translations are prepared for this beta and still benefit from native-speaker review. Functional simulations are separate from iPhone verification.
