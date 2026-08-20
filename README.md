# Сайт доставки еды Star Burger

Это сайт сети ресторанов Star Burger. Здесь можно заказать превосходные бургеры с доставкой на дом.

![скриншот сайта](https://dvmn.org/filer/canonical/1594651635/686/)


Сеть Star Burger объединяет несколько ресторанов, действующих под единой франшизой. У всех ресторанов одинаковое меню и одинаковые цены. Просто выберите блюдо из меню на сайте и укажите место доставки. Мы сами найдём ближайший к вам ресторан, всё приготовим и привезём.

На сайте есть три независимых интерфейса. Первый — это публичная часть, где можно выбрать блюда из меню, и быстро оформить заказ без регистрации и SMS.

Второй интерфейс предназначен для менеджера. Здесь происходит обработка заказов. Менеджер видит поступившие новые заказы и первым делом созванивается с клиентом, чтобы подтвердить заказ. После оператор выбирает ближайший ресторан и передаёт туда заказ на исполнение. Там всё приготовят и сами доставят еду клиенту.

Третий интерфейс — это админка. Преимущественно им пользуются программисты при разработке сайта. Также сюда заходит менеджер, чтобы обновить меню ресторанов Star Burger.

## Как запустить dev-версию сайта

Для запуска сайта нужно запустить **одновременно** бэкенд и фронтенд, в двух терминалах.

### Как собрать бэкенд

Скачайте код:
```sh
git clone https://github.com/devmanorg/star-burger.git
```

Перейдите в каталог проекта:
```sh
cd star-burger
```

[Установите Python](https://www.python.org/), если этого ещё не сделали.

Проверьте, что `python` установлен и корректно настроен. Запустите его в командной строке:
```sh
python --version
```
**Важно!** Версия Python должна быть не ниже 3.10.

Возможно, вместо команды `python` здесь и в остальных инструкциях этого README придётся использовать `python3`. Зависит это от операционной системы и от того, установлен ли у вас Python старой второй версии. 

В каталоге проекта создайте виртуальное окружение:
```sh
python -m venv venv
```
Активируйте его. На разных операционных системах это делается разными командами:

- Windows: `.\venv\Scripts\activate`
- MacOS/Linux: `source venv/bin/activate`


Установите зависимости в виртуальное окружение:
```sh
pip install -r requirements.txt
```

Определите переменную окружения `SECRET_KEY`. Создать файл `.env` в каталоге `star_burger/` и положите туда такой код:
```sh
SECRET_KEY=django-insecure-0if40nf4nf93n4
```

Создайте файл базы данных PostgreSQL:

```sh
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql
```

В интерактивной оболочке PostgreSQL выполните, заменив `your_secure_password` на ваш пароль :
```sh
CREATE DATABASE star_burger_db;
CREATE USER star_burger_user WITH PASSWORD 'your_secure_password';
ALTER ROLE star_burger_user SET client_encoding TO 'utf8';
ALTER ROLE star_burger_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE star_burger_user SET timezone TO 'UTC';
GRANT ALL ON SCHEMA public TO star_burger_user;
GRANT ALL PRIVILEGES ON DATABASE star_burger_db TO star_burger_user;
\q
```

Отмигрируйте базу:

```sh
python manage.py makemigrations
python manage.py migrate
```

Запустите сервер:

```sh
python manage.py runserver
```

Откройте сайт в браузере по адресу [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Если вы увидели пустую белую страницу, то не пугайтесь, выдохните. Просто фронтенд пока ещё не собран. Переходите к следующему разделу README.

### Собрать фронтенд

**Откройте новый терминал**. Для работы сайта в dev-режиме необходима одновременная работа сразу двух программ `runserver` и `parcel`. Каждая требует себе отдельного терминала. Чтобы не выключать `runserver` откройте для фронтенда новый терминал и все нижеследующие инструкции выполняйте там.

[Установите Node.js](https://nodejs.org/en/), если у вас его ещё нет.

Проверьте, что Node.js и его пакетный менеджер корректно установлены. Если всё исправно, то терминал выведет их версии:

```sh
nodejs --version
# v16.16.0
# Если ошибка, попробуйте node:
node --version
# v16.16.0

npm --version
# 8.11.0
```

Версия `nodejs` должна быть не младше `10.0` и не старше `16.16`. Лучше ставьте `16.16.0`, её мы тестировали. Версия `npm` не важна. Как обновить Node.js читайте в статье: [How to Update Node.js](https://phoenixnap.com/kb/update-node-js-version).

Перейдите в каталог проекта и установите пакеты Node.js:

```sh
cd star-burger
npm ci --dev
```

Команда `npm ci` создаст каталог `node_modules` и установит туда пакеты Node.js. Получится аналог виртуального окружения как для Python, но для Node.js.

Помимо прочего будет установлен [Parcel](https://parceljs.org/) — это упаковщик веб-приложений, похожий на [Webpack](https://webpack.js.org/). В отличии от Webpack он прост в использовании и совсем не требует настроек.

Теперь запустите сборку фронтенда и не выключайте. Parcel будет работать в фоне и следить за изменениями в JS-коде:

```sh
./node_modules/.bin/parcel watch bundles-src/index.js --dist-dir bundles --public-url="./"
```

Если вы на Windows, то вам нужна та же команда, только с другими слешами в путях:

```sh
.\node_modules\.bin\parcel watch bundles-src/index.js --dist-dir bundles --public-url="./"
```

Дождитесь завершения первичной сборки. Это вполне может занять 10 и более секунд. О готовности вы узнаете по сообщению в консоли:

```
✨  Built in 10.89s
```

Parcel будет следить за файлами в каталоге `bundles-src`. Сначала он прочитает содержимое `index.js` и узнает какие другие файлы он импортирует. Затем Parcel перейдёт в каждый из этих подключенных файлов и узнает что импортируют они. И так далее, пока не закончатся файлы. В итоге Parcel получит полный список зависимостей. Дальше он соберёт все эти сотни мелких файлов в большие бандлы `bundles/index.js` и `bundles/index.css`. Они полностью самодостаточны, и потому пригодны для запуска в браузере. Именно эти бандлы сервер отправит клиенту.

Теперь если зайти на страницу  [http://127.0.0.1:8000/](http://127.0.0.1:8000/), то вместо пустой страницы вы увидите:

![](https://dvmn.org/filer/canonical/1594651900/687/)

Каталог `bundles` в репозитории особенный — туда Parcel складывает результаты своей работы. Эта директория предназначена исключительно для результатов сборки фронтенда и потому исключёна из репозитория с помощью `.gitignore`.

**Сбросьте кэш браузера <kbd>Ctrl-F5</kbd>.** Браузер при любой возможности старается кэшировать файлы статики: CSS, картинки и js-код. Порой это приводит к странному поведению сайта, когда код уже давно изменился, но браузер этого не замечает и продолжает использовать старую закэшированную версию. В норме Parcel решает эту проблему самостоятельно. Он следит за пересборкой фронтенда и предупреждает JS-код в браузере о необходимости подтянуть свежий код. Но если вдруг что-то у вас идёт не так, то начните ремонт со сброса браузерного кэша, жмите <kbd>Ctrl-F5</kbd>.


## Как запустить prod-версию сайта

Собрать фронтенд:

```sh
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
```

Настроить бэкенд: создать файл `.env` в каталоге `star_burger/` со следующими настройками:

- `DEBUG` — дебаг-режим. Поставьте `False`.
- `SECRET_KEY` — секретный ключ проекта. Он отвечает за шифрование на сайте. Например, им зашифрованы все пароли на вашем сайте.
- `YANDEX_API_KEY` — Яндекс API токен для доступа к определению координат.
- `ALLOWED_HOSTS` — [см. документацию Django](https://docs.djangoproject.com/en/5.2/ref/settings/#allowed-hosts)
- `ROLLBAR_ACCESS_TOKEN` — токен сервиса ROLLBAR(`post_server_item`).
- `ROLLBAR_ENVIRONMENT` — название окружения или инсталляции сайта.
- `DB_NAME` — название БД Postgres.
- `DB_USER` — имя пользователя БД.
- `DB_PASSWORD` — пароль БД.
- `DB_HOST` — хост БД.
- `DB_PORT` — порт БД.

Для мониторинга ошибок сайта необходимо создать проект на rollbar.com и получить для него токен(`post_server_item`). Проверить работоспособность мониторинга можно используя ссылку в браузере http://127.0.0.1:8000/test-error/.

## Деплой

Скопируйте код в папку(для примера) opt/star-burger
Создайте сервис для запуска node.js

```
sudo nano /etc/systemd/system/star-burger-parcel.service
```

с содержимым

```
Description=Star Burger Parcel Watch
After=network.target

[Service]
User=starburger
Group=starburger
WorkingDirectory=/opt/star-burger
ExecStart=/opt/star-burger/node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

и сервис gunicorn:

```
sudo nano /etc/systemd/system/star-burger-parcel.service
```

с содержимым:

```
[Unit]
Description=Star Burger Gunicorn
After=network.target postgresql.service
Requires=postgresql.service

[Service]
User=starburger
Group=starburger
WorkingDirectory=/opt/star-burger
Environment="PATH=/opt/star-burger/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="DJANGO_SETTINGS_MODULE=star_burger.settings"
ExecStart=/opt/star-burger/venv/bin/gunicorn --bind 127.0.0.1:8000 star_burger.wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

и запустите:

```
sudo systemctl daemon-reload
sudo systemctl start star-burger-parcel
sudo systemctl star-burger-gunicorn
```

Настройте Nginx:

```
sudo nano /etc/nginx/sites-available/star-burger
```

с содержимым:

```
server {
    listen 80;
    server_name ваш_ip_или_домен;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/star-burger/static/;
        expires 1y;
        access_log off;
        add_header Cache-Control "public, immutable";
    }

    location /bundles/ {
        alias /opt/star-burger/bundles/;
        expires 1y;
        access_log off;
        add_header Cache-Control "public, immutable";
    }
}
```

## Быстрое обновление деплоя

Создайте скрипт script.sh
```
#!/bin/bash
set -e

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 16.16.0

PROJECT_DIR="/opt/star-burger"
cd "$PROJECT_DIR"

source venv/bin/activate

echo ">>> Получение обновлений из репозитория..."
git pull

echo ">>> Установка зависимостей Python..."
pip install -r requirements.txt

source .env

echo ">>> Применение миграций базы данных..."
python manage.py migrate

echo ">>> Сбор статики Django..."
python manage.py collectstatic --noinput

echo ">>> Установка зависимостей Node.js..."
npm install --include=dev

echo ">>> Сборка фронтенда (Parcel)..."
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

echo ">>> Перезапуск Gunicorn..."
sudo systemctl restart star-burger-gunicorn

echo ">>> Готово!"
```

Дайте ему права на выполнение:

```
sudo chmod +x script.sh
```

Запускайте:

```
./script.sh
```

## Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org). За основу был взят код проекта [FoodCart](https://github.com/Saibharath79/FoodCart).

Где используется репозиторий:

- Второй и третий урок [учебного курса Django](https://dvmn.org/modules/django/)
