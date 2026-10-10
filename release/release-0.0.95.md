# Release notes — 0.0.95

Release date: 09-Oct-2026

## English

- Protect saved progress and bookmarks during sync when local book folders are missing or inaccessible.
- Keep favourite and completion status syncing even when some book files are unavailable.
- Keep progress, bookmarks and favourite status consistent across entries for the same online book.
- Prevent duplicate favourites and repeated history entries for the same online book, and stop library scans from inflating play counts.

### Behavior changes

- Updates that need access to unavailable book files remain pending for later recovery, while other library changes can sync.
- Removing an online book from favourites or history applies to all matching entries for that book.

### BREAKING CHANGES

None

### Risks / What to test

- Sync between two devices while a book folder is missing or its access permission is revoked; check that progress and bookmarks are preserved.
- Restore folder access and sync again; check that pending updates are applied.
- Change favourite and completion status while book files are unavailable; confirm the changes reach the other device.
- Check duplicate online-book entries: progress stays consistent, removal affects all matching entries, and repeated scans do not increase play counts.

## Русский

- Сохранённая позиция прослушивания и закладки защищены при синхронизации, если локальные папки с книгами отсутствуют или недоступны.
- Статусы «Избранное» и «Прослушано» продолжают синхронизироваться, даже когда файлы некоторых книг недоступны.
- Позиция прослушивания, закладки и статус «Избранное» согласованы между записями одной и той же онлайн-книги.
- Устранены дубликаты одной онлайн-книги в избранном и истории, а повторное сканирование библиотеки больше не увеличивает счётчик воспроизведений.

### Изменения в работе приложения

- Обновления, которым нужен доступ к недоступным файлам книги, остаются в ожидании восстановления доступа. Остальные изменения библиотеки могут синхронизироваться.
- Удаление онлайн-книги из избранного или истории применяется ко всем соответствующим записям этой книги.

### КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ

Нет

### Риски / Что проверить

- Выполните синхронизацию между двумя устройствами, когда папка книги отсутствует или разрешение на доступ отозвано; убедитесь, что позиция прослушивания и закладки сохранены.
- Восстановите доступ к папке и повторите синхронизацию; проверьте, что ожидающие обновления применены.
- Измените статусы «Избранное» и «Прослушано», пока файлы книги недоступны; убедитесь, что изменения появились на другом устройстве.
- Проверьте дублирующиеся записи онлайн-книги: позиция прослушивания согласована, удаление затрагивает все соответствующие записи, а повторное сканирование не увеличивает счётчик воспроизведений.