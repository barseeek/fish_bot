## MVP Fish-shop bot

Проект магазина по продаже рыбы через Telegram

MVP версия проекта позволяет:
- Выбрать нужный товар в меню
- Добавлять товары в корзину
- Удалять товары из корзины
- Посмотреть корзину
- Оставить контакты покупателя для обратной связи



## Как установить

- Создайте базу данных в [RedisLabs](https://redislabs.com/)
- Создайте бота [Telegram messenger](https://web.telegram.org/#/login)

- Установить [Python3](https://www.python.org/downloads/)
- Установить [Node.js](https://nodejs.org/en)
- Создайте проект [Strapi](https://docs.strapi.io/user-docs/intro)
  ```
  npx create-strapi-app my-project --quickstart
  ```
- Установите зависимости:
    ```
    pip install -r requirements.txt
    ```

Создать в корне проекта файл `.env` и прописать в нем переменные следующим образом:

```
STRAPI_TOKEN=<your_strapi_token>
TELEGRAM_BOT_TOKEN=<your_telegram_bot_token>
TELEGRAM_LOG_BOT_TOKEN=<your_telegram_log_bot_token>
TELEGRAM_CHAT_ID=<your_telegram_chat_id>
REDIS_HOST=<your_redis_host>
REDIS_PORT=<your_redis_port>
REDIS_PASSWORD=<your_redis_password>
```

### Описание переменных:
- STRAPI_TOKEN: Токен для доступа к API Strapi.
- TELEGRAM_BOT_TOKEN: Токен вашего главного Telegram-бота.
- TELEGRAM_LOG_BOT_TOKEN: Токен Telegram-бота, который используется для логирования.
- TELEGRAM_CHAT_ID: Идентификатор чата Telegram, куда будут отправляться уведомления и логи.
- REDIS_HOST: Хост сервера Redis.
- REDIS_PORT: Порт сервера Redis.
- REDIS_PASSWORD: Пароль для доступа к серверу Redis.


## Как запустить.
```
python bot.py
```




## Цель проекта
Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org/modules/chat-bots/lesson/fish-shop/).