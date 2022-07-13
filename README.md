# Бот магазин в Telegram

## Цели проекта

* Создать бота с inline кнопками
* Подключить базу данных Redis
* Интегрировать с CMS 

> Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).

## Пример работы программы
Пример результата для Telegram:

Реальный [пример бота tg](https://t.me/etokosmo1337_bot):


![Пример результата для Telegram](https://dvmn.org/filer/canonical/1569215892/326/)


## Конфигурации

* Python version: 3.8.5
* Libraries: requirements.txt

## Запуск

- Скачайте код
- Через консоль в директории с кодом установите виртуальное окружение командой:

```bash
python3 -m venv env
```

- Активируйте виртуальное окружение командой:
```bash
source env/bin/activate
```

- Установите библиотеки командой:
```bash
pip install -r requirements.txt
```

- Запишите переменные окружения в файле `.env` в формате КЛЮЧ=ЗНАЧЕНИЕ


`TELEGRAM_API_TOKEN` Токен Телеграмма. Получить можно у [BotFather](https://telegram.me/BotFather).

`TELEGRAM_CHAT_ID` ID чата в телеграм, куда будут приходить возникшие ошибки бота

`DATABASE_HOST` Адрес базы данных redis

`DATABASE_PORT` Порт базы данных redis

`DATABASE_PASSWORD` Пароль базы данных redis

`MOTLIN_CLIENT_ID` Client id на [motlin](https://euwest.cm.elasticpath.com/)

`MOTLIN_CLIENT_SECRET` Client server на [motlin](https://euwest.cm.elasticpath.com/)


- Для запуска бота в Телеграм запустите скрипт командой:
```bash
python3 tg_bot.py
```


## Деплой
Деплой можно осуществить на [heroku](https://id.heroku.com/login).

Для этого там необходимо: 
* Зарегестировать аккаунт и создать приложение. 
* Интегрировать код из собственного репозитория на GitHub.
* В репозитории необходим файл `Procfile` в котором прописано:
```bash
bot: python3 tg_bot.py
```
* В `Resources` активировать ботов.
* Во вкладке `Settings` -> `Config Vars` прописать переменные окружения из `.env`.
* Для удобства отслеживания логов можно установить `Heroku CLI`.
* Для подключения приложения в `CLI` прописать в корне проекта
```bash
heroku login
heroku git:remote -a app_name
heroku logs --tail
```
