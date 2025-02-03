import asyncio
import os
import threading
import json
import time
import streamlit as st

from websocket_client import file_manager

def load_tasks():
    '''Загружает задачи из файла'''
    while True:
        try:
            if os.path.exists("tasks.json"):
                with open("tasks.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except (json.JSONDecodeError, OSError):
            time.sleep(0.1)

# Инициализируем переменную
if "uploaded_file" not in st.session_state:
    st.session_state["uploaded_file"] = None

# Заголовок
st.title("Онлайн транскрипция аудио и видео")

# Форма для загрузки одного файла
uploaded_file = st.file_uploader(
    "Загрузите файл для обработки",
    accept_multiple_files=False
)

# Обработка загруженного файла
if uploaded_file and uploaded_file.name != st.session_state["uploaded_file"]:
    file_path = os.path.join('uploaded_files', uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    # Добавляем задачу
    task = file_manager.add_task(file_path)
    if task:
        task_id, file_path = task

        # Отправляем файл на бэкэнд
        threading.Thread(target=lambda: asyncio.run(file_manager.send_file(file_path, task_id))).start()
        st.session_state["uploaded_file"] = uploaded_file.name
    else:
        st.error(f"Формат файла {uploaded_file.name} не поддерживается.")
        os.remove(file_path)


# Кнопка для обновления результатов
if st.button("Обновить результаты"):
    st.rerun()

# Отображение таблицы с файлами и статусами
st.subheader("Статус обработки файлов")

# Загружаем задачи
tasks = load_tasks()

# Проверяем, есть ли задачи
if tasks:
    # Сортируем задачи по времени (новые сверху)
    sorted_tasks = sorted(tasks.values(), key=lambda x: x["timestamp"], reverse=True)

    # Заголовки таблицы
    table_data = [["Имя файла", "Статус", "Результат"]]

    for task in sorted_tasks:
        file_name = task["original_name"]
        file_status = task["status"]
        transcript_path = task["transcript_path"]
        error_message = task["error"]

        if file_status == "В обработке...":
            result = ""
        elif error_message:
            result = f"Ошибка: {error_message}"
        elif transcript_path:
            try:
                with open(transcript_path, "r", encoding="utf-8") as f:
                    transcript_content = f.read()
                result = transcript_content
            except FileNotFoundError:
                result = "Файл транскрипции не найден."
        else:
            result = ""

        table_data.append([file_name, file_status, result])

    # Отображаем таблицу
    st.table(table_data)
else:
    st.write("Нет загруженных файлов.")
