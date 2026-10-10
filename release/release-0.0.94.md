# Release notes — 0.0.94

Release date: 08-Oct-2026

## English

- More reliable saving of favourites and history, keeping favourite status and date-added ordering consistent.
- Fixed favourite toggling when the same book appears through different catalogue links.
- Improved recovery of book details and listening positions from downloaded copies when the main saved copy is missing or unreadable.
- Sorting choices and selected sources are saved more reliably when leaving a screen.
- Preserved chapter boundaries and durations when saving books with multiple chapters in one audio file.

### Behavior changes

- Favourite changes appear after saving succeeds. If saving fails, the previous favourite state remains.
- Removing a favourite from the catalogue also clears favourite status for saved copies recognised as the same book.

### BREAKING CHANGES

- Older app versions cannot read library data saved by 0.0.94. Downgrading may make history and favourites unavailable.

### Risks / What to test

- Upgrade from 0.0.93 and check history, favourites, date-added ordering and selected sources.
- Add and remove favourites rapidly, then restart the app and check the results.
- Change sorting and immediately leave the screen; confirm the choice is retained.
- Check book details and resume positions for downloaded books, plus chapter boundaries for books sharing one audio file.

## Русский

- Избранное и история сохраняются надёжнее: статус избранного и порядок по дате добавления остаются согласованными.
- Исправлено добавление и удаление из избранного, когда одна книга доступна по разным ссылкам в каталоге.
- Улучшено восстановление сведений о книге и позиции прослушивания из скачанных копий, если основная сохранённая копия отсутствует или не читается.
- Выбранная сортировка и источник сохраняются надёжнее при выходе с экрана.
- При сохранении книг с несколькими главами в одном аудиофайле сохраняются границы и длительность глав.

### Изменения поведения

- Статус избранного меняется после успешного сохранения. Если сохранить изменение не удалось, прежний статус остаётся.
- Удаление книги из избранного в каталоге также снимает этот статус у сохранённых копий, распознанных как та же книга.

### КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ

- Старые версии приложения не могут прочитать данные библиотеки, сохранённые версией 0.0.94. При возврате к старой версии история и избранное могут стать недоступны.

### Риски / Что проверить

- После обновления с 0.0.93 проверить историю, избранное, порядок по дате добавления и выбранные источники.
- Быстро добавить и удалить книги из избранного, затем перезапустить приложение и проверить результат.
- Изменить сортировку и сразу выйти с экрана; убедиться, что выбор сохранился.
- Проверить сведения и позиции продолжения прослушивания у скачанных книг, а также границы глав у книг с одним общим аудиофайлом.