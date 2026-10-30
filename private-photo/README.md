# Private Photo — Official interface data

©️ Sentechtipsvn

This directory shares the existing Clipboard-Pro-Data repository. Private Photo and Clipboard Pro have separate product identifiers, release paths, caches and user-data folders.

Current interface package: **1.0.0-beta.1**, with Vietnamese and English, **83 labels per locale**.

This repository contains public interface labels and release metadata. It does not contain users' images, image indexes, notes, passwords or vault settings. The shortcut downloads its pinned interface package and caches it in iCloud Drive/Shortcuts/PrivatePhoto. It does not upload images to this repository.

- [Readable labels](releases/1.0.0-beta.1/catalog-readable.json)
- [Runtime envelope](releases/1.0.0-beta.1/catalog.txt)
- [Manifest](releases/1.0.0-beta.1/manifest.json)

The shortcut pins the release to a commit URL and verifies SHA-256 of the envelope's ASCII payload. Refresh reloads the pinned compatible package; it does not silently update the workflow engine. Subsequent offline use requires the cached package and relevant iCloud files to be available locally.

**Storage is Base64 encoding, not password encryption.** Anyone who can read the vault folder can recover the images. Hash verification is an integrity check, not encryption or copy protection. Original images are kept by the shortcut.

Future versions should receive new immutable release paths. Do not replace a released payload in place. Clipboard Pro's existing files are independent of this package.
