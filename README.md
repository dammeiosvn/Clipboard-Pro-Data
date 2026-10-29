# Clipboard Pro Data

©️ Sentechtipsvn

Official interface data for Clipboard Pro. Personal notes are never uploaded here. The runtime engine stays in the shortcut.

## beta.3 package format

`releases/1.6.0-beta.3/catalog.txt` is a JSON envelope with `format` and `payload` string fields. `payload` is standard Base64 for the UTF-8 interface catalog. The shortcut pins a commit and SHA-256 of the ASCII payload value. JSON key order and indentation may change without changing the payload or its digest. `catalog-readable.json` is the human-readable companion; it is not downloaded by the runtime.

This fixes beta.2's false verification failure after iOS reserializes JSON during file I/O. Downloads, staged files and active caches are checked separately. Base64 is an encoding, not encryption or copy protection.

The first run needs internet; subsequent runs use the verified iCloud cache. Settings and private notes remain unchanged. beta.2 release files remain available for historical builds.

Attribution must be retained; redistribution and commercial terms require agreement with the author. This notice does not technically prevent editing or copying an editable shortcut.
