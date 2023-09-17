# Foodgram «Продуктовый помощник»

## Описание

«Foodgram» - это сервис, где пользователи могут публиковать разные рецепты, подписываться на публикации других пользователей и добавлять понравившиеся рецепты в избранное. Самой главной особенностью Foodgram является возможность добавлять рецепты в «Список покупок» и скачать список продуктов для нужного рецепта. Foodgram включает в себя онлайн-сервис и API для него.

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

## Об авторе
Шубин Григорий [ShubinGrigorii](https://github.com/ShubinGrigorii)