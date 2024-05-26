# Используем официальный базовый образ Python
FROM python:latest
# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Обновляем pip
RUN python -m pip install --upgrade pip

# Копируем файл requirements.txt в контейнер
COPY requirements.txt .


# Копируем все файлы из текущего каталога в рабочую директорию контейнера
COPY . .

# Устанавливаем переменную окружения PYTHONPATH
ENV PYTHONPATH=/app

# Устанавливаем команду для запуска приложения
CMD ["python", "main.py"]