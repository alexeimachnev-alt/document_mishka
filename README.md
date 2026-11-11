# Генератор документов МИШКА (Mini App)

Этот бот использует встроенное веб-приложение Telegram (Mini App) для быстрого сбора данных и генерации документов.

## Установка и запуск (Render)

1. Загрузите файлы из этого архива в ваш GitHub-репозиторий.
2. В репозитории **ОБЯЗАТЕЛЬНО** должны быть файлы шаблонов и шрифтов:
    * `cert_template.jpg`
    * `dover_template.pdf`
    * `contract_template.pdf`
    * `arial.ttf`, `arialbd.ttf`, `times.ttf`, `calibri.ttf`, `calibrib.ttf`
3. В настройках **Environment Variables** на Render добавьте:
    * `BOT_TOKEN` — ваш токен бота.
    * `WEBAPP_URL` — ссылка на ваш проект в Render с приставкой `/app` (например, `https://mishka-doc-bot.onrender.com/app`).
4. Запустите сервис (команда `python bot.py`).

В Telegram нажмите кнопку `Запустить` (или отправьте `/start`). Появится кнопка "Открыть приложение", внутри которой собраны удобные формы для всех трех документов!
