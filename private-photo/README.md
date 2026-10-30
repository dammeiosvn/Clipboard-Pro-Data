# Private Photo — Official interface data

©️ Sentechtipsvn

Current package: **1.0.0-beta.4**, Vietnamese and English, 88 labels per locale.

This directory shares Clipboard-Pro-Data but uses separate release paths and caches. It contains public interface labels only, never user images, settings or indexes.

- [Runtime envelope](releases/1.0.0-beta.4/catalog.txt)
- [Readable labels](releases/1.0.0-beta.4/catalog-readable.json)
- [Manifest](releases/1.0.0-beta.4/manifest.json)

The beta.4 engine pins a commit URL and verifies the payload SHA-256. Upgrading downloads the new compatible interface package once, then uses its local cache when available. Existing settings, albums and images are kept. Older engines retain their pinned beta.1 package.

Base64 storage is not password encryption. Images are not uploaded here. Released package paths remain immutable.
