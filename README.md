# NewLocalShare

## 🇷🇺 Русская версия

Веб-приложение на Flask для загрузки, хранения и просмотра медиафайлов (видео, аудио и других файлов) с категориями, превью и статистикой просмотров.

### Возможности

* Загрузка видео, аудио и других файлов
* Автоматическое определение типа файла
* Генерация превью для видео
* Подсчёт просмотров
* Категории файлов
* Сортировка:

  * по дате загрузки
  * по просмотрам
  * по длительности
* SQLite база данных
* HTML шаблоны (Jinja2)
* Простая UI панель загрузки

### Стек технологий

* Python
* Flask
* SQLite
* OpenCV (генерация превью видео)
* HTML / CSS / JS

### Структура проекта

```
.
├── index.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   ├── video.html
│   ├── file.html
│   └── categories.html
├── static/
│   ├── styles.css
│   └── app.js
├── uploads/
├── thumbnails/
├── temp_chunks/
└── database.db
```

### Установка

```bash
git clone https://github.com/yourusername/project.git
cd project
```

Создать виртуальное окружение:

```bash
python -m venv venv
```

Активировать:

Windows:

```bash
venv\Scripts\activate
```

Linux / Mac:

```bash
source venv/bin/activate
```

Установить зависимости:

```bash
pip install flask opencv-python
```

### Запуск

```bash
python index.py
```

Открыть в браузере:

```
http://127.0.0.1:5000
```

### Поддерживаемые форматы

Видео:

* mp4
* avi
* mov
* mkv
* webm
* flv
* wmv

Аудио:

* mp3
* wav
* ogg
* flac
* aac
* m4a

### База данных

Автоматически создаётся SQLite база со следующими таблицами:

* files
* categories
* file_category

### Скриншоты

Добавьте сюда скриншоты интерфейса.

---

## 🇬🇧 English Version

Flask web application for uploading, storing and viewing media files (video, audio and others) with categories, thumbnails and view statistics.

### Features

* Upload video, audio and other files
* Automatic file type detection
* Video thumbnail generation
* View counter
* File categories
* Sorting:

  * by upload date
  * by views
  * by duration
* SQLite database
* Jinja2 templates
* Simple upload UI

### Tech Stack

* Python
* Flask
* SQLite
* OpenCV (video thumbnails)
* HTML / CSS / JavaScript

### Project Structure

```
.
├── index.py
├── templates/
├── static/
├── uploads/
├── thumbnails/
├── temp_chunks/
└── database.db
```

### Installation

```bash
git clone https://github.com/yourusername/project.git
cd project
```

Create virtual environment:

```bash
python -m venv venv
```

Activate:

Windows:

```bash
venv\Scripts\activate
```

Linux / Mac:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install flask opencv-python
```

### Run

```bash
python index.py
```

Open in browser:

```
http://127.0.0.1:5000
```

### Supported Formats

Video:

* mp4
* avi
* mov
* mkv
* webm
* flv
* wmv

Audio:

* mp3
* wav
* ogg
* flac
* aac
* m4a

### Database

SQLite database is created automatically with tables:

* files
* categories
* file_category

### Screenshots

Add screenshots here.

---

## License

MIT
