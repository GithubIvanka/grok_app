import webview
import json
import os
import sys
import threading
import logging
import time

# Настройка логирования в файл
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class GrokApp:
    def __init__(self):
        # Определяем путь к cookies.json относительно исполняемого файла
        if getattr(sys, 'frozen', False):
            # Если запущен .exe
            self.base_path = os.path.dirname(sys.executable)
        else:
            # Если запущен .py
            self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.cookies_file = os.path.join(self.base_path, "cookies.json")

        self.webview_window = None
        self.webview_started = False
        self.open_webview()

    def load_cookies(self):
        """Загружает cookies из файла и возвращает их в формате, пригодном для webview."""
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, "r") as f:
                    cookies = json.load(f)
                logging.info("Cookies успешно загружены")
                return cookies
            except Exception as e:
                logging.error(f"Ошибка загрузки cookies: {str(e)}")
        return []

    def save_cookies(self):
        """Сохраняет cookies текущей сессии в файл."""
        if self.webview_window:
            try:
                cookies = self.webview_window.get_cookies()
                cookie_list = [
                    {
                        "name": cookie["name"],
                        "value": cookie["value"],
                        "domain": cookie.get("domain", ".grok.com"),
                        "path": cookie.get("path", "/"),
                        "expires": cookie.get("expires", -1),
                        "secure": cookie.get("secure", False),
                        "httpOnly": cookie.get("httpOnly", False)
                    }
                    for cookie in cookies
                ]
                with open(self.cookies_file, "w") as f:
                    json.dump(cookie_list, f, indent=2)
                logging.info("Cookies успешно сохранены")
            except Exception as e:
                logging.error(f"Ошибка сохранения cookies: {str(e)}")

    def open_webview(self):
        """Открывает окно webview и загружает cookies."""
        if self.webview_window is None:
            try:
                self.webview_window = webview.create_window(
                    "Grok",
                    "https://grok.com",
                    width=1280,
                    height=720
                )

                def on_loaded():
                    """Загружает cookies после загрузки страницы."""
                    cookies = self.load_cookies()
                    try:
                        for cookie in cookies:
                            expires = f"expires={cookie['expires']}" if cookie["expires"] > 0 else ""
                            js_code = (
                                f"document.cookie = '{cookie['name']}={cookie['value']}; "
                                f"domain={cookie['domain']}; "
                                f"path={cookie['path']}; "
                                f"{'secure;' if cookie['secure'] else ''}"
                                f"{expires}';"
                            )
                            self.webview_window.evaluate_js(js_code)
                        logging.info("Cookies успешно восстановлены")
                    except Exception as e:
                        logging.error(f"Ошибка восстановления cookies: {str(e)}")

                def on_closing():
                    """Сохраняет cookies и очищает ресурсы перед закрытием."""
                    self.save_cookies()
                    if self.webview_window:
                        try:
                            self.webview_window.destroy()
                            logging.info("Окно webview уничтожено")
                        except Exception as e:
                            logging.error(f"Ошибка при уничтожении окна: {str(e)}")
                    self.webview_window = None

                self.webview_window.events.loaded += on_loaded
                self.webview_window.events.closed += on_closing

                if not self.webview_started:
                    try:
                        webview.start()
                        self.webview_started = True
                        logging.info("Webview успешно запущен")
                    except Exception as e:
                        logging.error(f"Ошибка запуска webview: {str(e)}")
                        raise

            except Exception as e:
                logging.error(f"Ошибка создания окна webview: {str(e)}")
                raise

    def __del__(self):
        """Гарантирует завершение webview при уничтожении объекта."""
        if self.webview_window:
            try:
                self.webview_window.destroy()
                logging.info("Окно webview уничтожено при выходе")
            except:
                pass

if __name__ == "__main__":
    try:
        app = GrokApp()
    except Exception as e:
        logging.error(f"Ошибка инициализации приложения: {str(e)}")
        # Задержка для гарантированного завершения процессов
        time.sleep(2)