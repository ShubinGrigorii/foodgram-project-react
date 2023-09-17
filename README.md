foodgram-project-react

Команды для запуска <a id=4></a>

Перед запуском необходимо склонировать проект:
```bash
git clone git@github.com:ShubinGrigorii/foodgram-project-react.git

```

Cоздать и активировать виртуальное окружение:
```bash
python -m venv venv
```
```bash
Linux: source venv/bin/activate
Windows: source venv/Scripts/activate
```

И установить зависимости из файла requirements.txt:
```bash
python3 -m pip install --upgrade pip
```
```bash
pip install -r requirements.txt
```

Далее необходимо собрать образы для фронтенда и бэкенда.  
Из папки "./backend/" выполнить команду:
```bash
docker build -t username/foodgram_backend .
```

Из папки "./frontend/" выполнить команду:
```bash
docker build -t username/foodgram_frontend .
```

Из папки "./infra/" выполнить команду:

```bash
docker build -t username/foodgram_gateway .
```

После создания образов можно создавать и запускать контейнеры. 
Из папки "./infra/" выполнить команду:
```bash
docker-compose up -d
```

После успешного запуска контейнеров выполнить миграции:
```bash
docker-compose exec backend python manage.py migrate
```

Создать суперюзера (Администратора):
```bash
docker-compose exec backend python manage.py createsuperuser
```

Собрать статику:
```bash
docker-compose exec backend python manage.py collectstatic --no-input
```

Теперь доступность проекта можно проверить по адресу [http://localhost/](http://localhost/)
