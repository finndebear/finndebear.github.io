# STPlayer — Stream Transport Player

STPlayer is a free audiobook player for Android 8.0 and newer. Listen to your own
files, browse supported public online catalogs, or download supported books for
offline playback. STPlayer does not host, bundle or sell audiobooks.

## Install

- [Google Play](https://play.google.com/store/apps/details?id=com.st.player)
- [RuStore](https://www.rustore.ru/catalog/app/com.st.player)
- [Latest APK and ZIP](https://finndebear.github.io/stplayer/latest/)
- [Русская страница скачивания](https://finndebear.github.io/stplayer/ru/latest/)

For a direct APK installation, Android may ask you to allow installation from your
browser or file manager. Install an update over the existing app to retain its data.

This release reworks internal library storage. Before updating, create a library
backup in **Settings → Backup & restore → Back up** as a precaution. Audio files are not
included in the library backup.

## Listening

- Resume positions, chapter navigation, bookmarks and favorites.
- Playback speed and pitch, silence skipping and loudness normalization.
- Sleep timer with duration, end-of-track, schedule and optional motion reset.
- Local audio, online streaming, supported downloads and torrent sources.
- Background playback, Android Auto, Bluetooth and Android TV controls.
- Themes, text scaling and 12 interface languages.

Catalog availability, downloads and category/sort options depend on each source.
The in-app **Help** describes current controls and recovery steps in your selected
language. In **About**, the icon and STPlayer name open the website, and **Privacy
Policy** opens the policy in the app language.

## Privacy

Library data is stored on your device. Production builds use Firebase Crashlytics
for crash diagnostics. Online sources receive requests when you use them. Optional
synchronization sends encrypted snapshots through independent public Nostr relays;
audio files and storage permissions stay on each device.

Read the [Privacy Policy](https://finndebear.github.io/stplayer/privacy/?lang=en)
or [Политику конфиденциальности](https://finndebear.github.io/stplayer/privacy/?lang=ru).

## Website maintenance

The public site is served by GitHub Pages from this repository. The home and
`latest` pages read the latest stable GitHub release automatically, including
localized release notes with a link to the exact source release. A checked-in
snapshot keeps downloads available when JavaScript or the API is unavailable.

See [website tools and verification](tools/README.md) before changing or publishing
the site. Official SVG store badges are stored locally; RuStore appears only on the
Russian download page.

## License

© 2025–2026 stpork. All rights reserved.
Personal use only; see [LICENSE](LICENSE).
