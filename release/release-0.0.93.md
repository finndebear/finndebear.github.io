# Release notes — 0.0.93

Release date: 06-Oct-2026

## English

- More reliable saving of listening progress when switching books, closing the app, or restarting.
- Better protection for favourites and history when saving is interrupted or storage becomes unavailable.
- Synchronisation and backup imports protect progress and bookmarks changed while the operation is running.
- Downloads continue when you switch or close screens.
- Downloaded ZIP audiobooks remain visible without extracting the audio, with better checks for incomplete or damaged archives.
- Cancelled or replaced sleep timers and volume fades no longer interrupt playback with outdated commands.
- Improved Android TV navigation: focus returns after closing dialogs, and a single Back press no longer triggers two navigation actions.

### Behavior changes

- Closing or restarting pauses playback and waits for progress to save. If saving fails or takes too long, the app stays open. Resuming playback cancels the pending close.
- If a download folder becomes inaccessible, the app keeps your folder selection and existing files. Restore access or choose another folder in Settings, then retry.
- Changing the library folder resets the custom download location to the default folder inside the new library. Existing downloads stay in their original location.
- Unsupported storage locations are now rejected during library folder selection, with guidance to use internal storage or an SD card.
- To cancel a download, use its download menu; leaving the screen does not cancel it.

### BREAKING CHANGES

None

### Risks / What to test

- Check saved progress after switching books, closing, and reopening the app.
- Verify favourites, history, and bookmarks after restarting; test synchronisation and backup imports while listening or editing bookmarks.
- Download while navigating between screens, then test cancellation, resuming, and offline playback, including ZIP audiobooks.
- Restore lost folder access and change library or download folders; confirm existing files remain intact.
- On Android TV, check focus after dialogs and single-press Back navigation.
- Reset or cancel sleep timers and volume fades; check for unexpected pauses.

## Русский

- Надёжнее сохраняется позиция прослушивания при переключении книг, выходе из приложения и перезапуске.
- Улучшена защита избранного и истории при прерывании сохранения или потере доступа к хранилищу.
- Синхронизация и импорт резервных копий защищают позицию прослушивания и закладки, изменённые во время операции.
- Загрузки продолжаются при переходе на другой экран или закрытии текущего.
- Скачанные аудиокниги в ZIP остаются видимыми без распаковки аудио; улучшена проверка неполных и повреждённых архивов.
- Отменённые или заменённые таймеры сна и плавного затухания громкости больше не прерывают воспроизведение устаревшими командами.
- Улучшена навигация на Android TV: после закрытия диалогов восстанавливается фокус, а одно нажатие «Назад» больше не вызывает два действия.

### Изменения в работе приложения

- Перед выходом или перезапуском приложение приостанавливает воспроизведение и ждёт сохранения позиции. При ошибке или слишком долгом сохранении оно остаётся открытым. Возобновление воспроизведения отменяет ожидающий выход.
- Если папка загрузок недоступна, приложение сохраняет выбранное расположение и существующие файлы. Восстановите доступ или выберите другую папку в настройках, затем повторите попытку.
- При смене папки библиотеки выбранная вручную папка загрузок сбрасывается на стандартную внутри новой библиотеки. Скачанные файлы остаются на прежнем месте.
- Неподдерживаемые хранилища теперь отклоняются при выборе папки библиотеки. Приложение предлагает выбрать папку во внутренней памяти или на SD-карте.
- Для отмены загрузки используйте её меню: уход с экрана не отменяет загрузку.

### НЕСОВМЕСТИМЫЕ ИЗМЕНЕНИЯ

Нет

### Риски / Что проверить

- Проверьте сохранение позиции при переключении книг, выходе и повторном запуске приложения.
- Проверьте избранное, историю и закладки после перезапуска; выполните синхронизацию и импорт резервной копии во время прослушивания или редактирования закладок.
- Запустите загрузку и переходите между экранами, затем проверьте отмену, возобновление и прослушивание без интернета, включая аудиокниги в ZIP.
- Восстановите потерянный доступ к папке и смените папку библиотеки или загрузок; убедитесь, что существующие файлы сохранились.
- На Android TV проверьте фокус после закрытия диалогов и реакцию на одиночное нажатие «Назад».
- Перезапустите или отмените таймеры сна и затухания громкости; проверьте, нет ли неожиданных пауз.