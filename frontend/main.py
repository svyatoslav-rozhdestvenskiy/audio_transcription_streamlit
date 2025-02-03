import asyncio
import threading
import os
import json
import uvicorn

from websocket_client import app

def clear_tasks():
    """Очищает файл tasks.json при запуске."""
    if os.path.exists("tasks.json"):
        with open("tasks.json", "w", encoding="utf-8") as f:
            json.dump({}, f)

def clear_transcripts():
    """Удаляет все файлы в папке transcripts при запуске."""
    transcripts_folder = "transcripts"
    if os.path.exists(transcripts_folder):
        for file in os.listdir(transcripts_folder):
            file_path = os.path.join(transcripts_folder, file)
            os.remove(file_path)

async def start_server():
    """Запускает сервер WebSocket на порту 9000."""
    config = uvicorn.Config(app=app, host="0.0.0.0", port=9000)
    server = uvicorn.Server(config)
    await server.serve()

def run_streamlit():
    """Запускает Streamlit в отдельном потоке."""
    os.system("streamlit run streamlit_website.py")

async def main():
    clear_tasks()
    clear_transcripts()

    # Запускаем Streamlit в отдельном потоке
    streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
    streamlit_thread.start()

    # Запускаем сервер WebSocket
    await start_server()

if __name__ == "__main__":
    asyncio.run(main())
