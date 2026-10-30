# Clipboard Pro — Official interface data

©️ Sentechtipsvn

Latest package: **1.6.0-beta.6**, with **37 locale choices and 61 labels per locale**. This release adds the 30 remaining choices in the requested list. All seven beta.5 dictionaries are preserved exactly.

This repository contains public interface labels, not user notes. Notes and clipboard contents stay in the user's iCloud storage and are not uploaded here.

## Compatibility and offline use

Install the beta.6 shortcut to access the new package. Keep the ClipboardPro folder, settings and notes. The first upgrade needs internet to download the new pinned catalog; subsequent runs can use its valid offline cache once iCloud files are available locally. Existing beta.5 shortcuts keep using their immutable seven-language package.

The previous `vi` and `en` identifiers stay unchanged for saved settings. They correspond to `vi-VN` and `en-US` in the requested list. Regional variants count as separate choices; this is not a claim of 37 unrelated languages. See [identifier aliases](releases/1.6.0-beta.6/language-aliases.json).

The interface and note workflows retain the beta.5 layout and navigation. The viewer now follows the direction of its text automatically, including Arabic and Persian. Actual native rendering and translations still benefit from testing by users of each language.

## Release data

- [Readable labels](releases/1.6.0-beta.6/catalog-readable.json)
- [Runtime envelope](releases/1.6.0-beta.6/catalog.txt)
- [Manifest](releases/1.6.0-beta.6/manifest.json)

Release paths are immutable. The shortcut pins a commit URL and checks SHA-256 of the ASCII payload field, independent of outer JSON formatting. Base64 is encoding, not encryption or copy protection. Refresh reloads the pinned compatible package; it does not automatically upgrade the shortcut engine.

## Included choices

| Identifier | Display name |
| --- | --- |
| vi | Tiếng Việt |
| en | English |
| fr-FR | Français |
| de-DE | Deutsch |
| es-ES | Español |
| ja | 日本語 |
| ko-KR | 한국어 |
| ar | العربية |
| bn-BD | বাংলা |
| cs-CZ | Čeština |
| da-DK | Dansk |
| el-GR | Ελληνικά |
| en-GB | English (UK) |
| es-MX | Español (México) |
| fa-IR | فارسی |
| fi-FI | Suomi |
| fil-PH | Filipino |
| fr-CA | Français (Canada) |
| hi-IN | हिन्दी |
| hu-HU | Magyar |
| id-ID | Bahasa Indonesia |
| it-IT | Italiano |
| ms-MY | Bahasa Melayu |
| nb-NO | Norsk bokmål |
| nl-NL | Nederlands |
| pl-PL | Polski |
| pt-BR | Português (Brasil) |
| pt-PT | Português (Portugal) |
| ro-RO | Română |
| ru | Русский |
| sv-SE | Svenska |
| sw-KE | Kiswahili |
| th-TH | ไทย |
| tr-TR | Türkçe |
| uk-UA | Українська |
| zh-CN | 简体中文 |
| zh-TW | 繁體中文 |

Translations were prepared for this beta and have not all been independently reviewed by native speakers. Automated checks validate structure and simulated flows, not every native-device rendering or linguistic nuance.

## Private Photo interface package

[Private Photo](private-photo/README.md) now shares this repository for its own public Vietnamese and English interface package. Its release files and local folders are separate from Clipboard Pro. No user images are stored here.
