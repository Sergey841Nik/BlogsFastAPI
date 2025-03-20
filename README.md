# FastApiWithAuthSample

## Введение

Этот проект представляет собой пример приложения на FastAPI с аутентификацией и авторизацией. Он включает в себя базовую структуру для создания RESTful API с использованием Python и FastAPI.

## Установка

1. Убедитесь, что у вас установлен Python 3.8 или выше.
2. Установите Poetry для управления зависимостями:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
3. Клонируйте репозиторий:
   ```bash
   https://github.com/Sergey841Nik/BlogsFastAPI.git
   cd BlogsFastAPI
   ```
4. Установите зависимости:
   ```bash
   poetry install
   ```

## Использование

1. Запустите сервер разработки:
   ```bash
   poetry run uvicorn main:app --reload
   ```
2. Откройте браузер и перейдите по адресу `http://127.0.0.1:8000` для доступа к API.

## Структура проекта

```
FastApiWithAuthSample/
├── alembic/
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/
│       ├── 2025_01_06_1749-27c82a45aaa3_add_table_users_and_roles.py
│       ├── 2025_01_06_1750-aa589a50226f_add_table_blogs.py
│       └── 2025_01_06_1752-5739f080fdc9_crate_table_tags_and_blog_tags.py
├── api/
│   ├── crud.py
│   ├── dependencies.py
│   ├── schemes.py
│   └── views.py
├── auth/
│   ├── __init__.py
│   ├── auth_jwt.py
│   ├── crud.py
│   ├── dependencies.py
│   ├── README.md
│   ├── schemes.py
│   ├── utils.py
│   └── views.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   └── models/
│       ├── base.py
│       └── db_helper.py
├── pages/
│   └── views.py
├── static/
│   ├── .gitkeep
│   ├── js/
│   │   └── post.js
│   └── style/
│       ├── 404.css
│       ├── login.css
│       ├── post.css
│       └── posts.css
├── templates/
│   ├── 404.html
│   ├── login.html
│   ├── post.html
│   └── posts.html
├── .gitignore
├── alembic.ini
├── db_sql.db
├── main.py
├── poetry.lock
└── pyproject.toml
```

## Зависимости

Проект использует Poetry для управления зависимостями. Основные зависимости перечислены в `pyproject.toml`.


