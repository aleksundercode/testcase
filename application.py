from settings import *
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from datetime import datetime
from prometheus_client import start_http_server, Counter
import sqlite3
import requests
import logging
import sys

HostName = '0.0.0.0'
ServerPort = 8080

REQUESTS = Counter('my_requests_total', 'Total number of requests to this webserver', ['method'])

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        REQUESTS.labels('GET').inc()
        if self.path == '/hello':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(f"<html><head><title>{APP_NAME}</title></head>", "utf-8"))
            self.wfile.write(bytes("<body>Hello Page</body></html>", "utf-8"))
        elif self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-type", "text/plain; version=0.0.4; charset=utf-8")
            self.end_headers()
            self.wfile.write(bytes(requests.get("http://localhost:8000/").text, "utf-8"))
        elif LOGDRIVER == "SQLLITE" and urlparse(self.path).path == "/user":
            params = parse_qs(urlparse(self.path).query, keep_blank_values=False)
            if 'name' in params:
                try:
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(bytes(f"<html><head><title>{APP_NAME}</title></head>", "utf-8"))
                    self.wfile.write(bytes("<body>", "utf-8"))

                    sqlite_connection = sqlite3.connect(SQLLITE_DBNAME)
                    get_user_query = f'''SELECT name || ': ' || strftime('%H:%M:%S - %d.%m.%Y',date) FROM users WHERE name ='{params['name'][0]}';'''
                    cursor = sqlite_connection.cursor()
                    logging.info(f"Соединение с базой данных {SQLLITE_DBNAME} установлено")
                    for row in cursor.execute(get_user_query):
                        logging.info(row[0])
                        self.wfile.write(bytes(f"{row[0]}<br>", "utf-8"))
                    cursor.close()

                    self.wfile.write(bytes("</body></html>", "utf-8"))

                except Exception as exc:
                    self.send_response(500)
                    self.wfile.write(bytes(f"<html><head><title>{APP_NAME}</title></head>", "utf-8"))
                    self.wfile.write(bytes("<body>", "utf-8"))
                    self.wfile.write(bytes(exc.__str__(), "utf-8"))
                    self.wfile.write(bytes("</body></html>", "utf-8"))
                    logging.error(exc.__str__())
                finally:
                    if (sqlite_connection):
                        sqlite_connection.close()
                        logging.info("Соединение с SQLite закрыто")
            else:
                self.send_response(500)
                self.wfile.write(bytes(f"<html><head><title>{APP_NAME}</title></head>", "utf-8"))
                self.wfile.write(bytes("<body>Expecting 'Name' parameter</body></html>", "utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(f"<html><head><title>{APP_NAME}</title></head>", "utf-8"))
            self.wfile.write(bytes("<body>Page Not Found</body></html>", "utf-8"))

    def do_POST(self):
        REQUESTS.labels('POST').inc()
        if urlparse(self.path).path == "/user":
            params = parse_qs(urlparse(self.path).query, keep_blank_values=False)
            if 'name' in params:
                try:
                    writeUserName(params['name'][0])
                    self.send_response(200)             
                    self.wfile.write(bytes(f"<html><head><title>{APP_NAME}</title></head>", "utf-8"))
                    self.wfile.write(bytes("<body>OK</body></html>", "utf-8"))
                except Exception as exc:
                    self.send_response(500)
                    self.wfile.write(bytes(f"<html><head><title>{APP_NAME}</title></head>", "utf-8"))
                    self.wfile.write(bytes("<body>", "utf-8"))
                    self.wfile.write(bytes(exc.__str__(), "utf-8"))
                    self.wfile.write(bytes("</body></html>", "utf-8"))
            else:
                self.send_response(500)
                self.wfile.write(bytes(f"<html><head><title>{APP_NAME}</title></head>", "utf-8"))
                self.wfile.write(bytes("<body>Expecting 'Name' parameter</body></html>", "utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(f"<html><head><title>{APP_NAME}</title></head>", "utf-8"))
            self.wfile.write(bytes("<body>Page Not Found</body></html>", "utf-8"))

def writeUserName (name):
    if LOGDRIVER == "FILE":
        now = datetime.now().strftime("%H:%M:%S - %d.%m.%Y")
        with open(LOGFILE_NAME, "a") as f:
            f.write(f"{name}: {now}\n")
    elif LOGDRIVER == "SQLLITE":
        insert_user_query = f'''INSERT INTO users (name,date)
                                VALUES('{name}',datetime('now','localtime'));'''
        executeSQLLITEQuery(SQLLITE_DBNAME, insert_user_query, f"Пользователь {name} добавлен в базу данных")

def executeSQLLITEQuery (SQLLITE_DBNAME, QUERY, MESSAGE):
    try:
        sqlite_connection = sqlite3.connect(SQLLITE_DBNAME)
        cursor = sqlite_connection.cursor()
        logging.info(f"Соединение с базой данных {SQLLITE_DBNAME} установлено")
        cursor.execute(QUERY)
        sqlite_connection.commit()
        logging.info(MESSAGE)
        cursor.close()

    except sqlite3.Error as error:
        logging.error("Ошибка при подключении к sqlite", error)
        if (sqlite_connection):
            sqlite_connection.close()
            logging.info("Соединение с SQLite закрыто")
        raise
    finally:
        if (sqlite_connection):
            sqlite_connection.close()
            logging.info("Соединение с SQLite закрыто")
        

if __name__ == '__main__':
    # Create and configure logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    logging.info(f"Log driver set to {LOGDRIVER}")

    # Running migrations
    if LOGDRIVER == "SQLLITE":
        logging.info("Running migrations")
        sqlite_create_table_query = '''CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY,
                                name TEXT NOT NULL,
                                date TEXT NOT NULL);'''
        try:
            executeSQLLITEQuery(SQLLITE_DBNAME, sqlite_create_table_query, "Таблица SQLite создана")
        except:
            logging.error(sys.exc_info())

    # Running Web server    
    try:
        start_http_server(8000)
        MyWebServer = ThreadingHTTPServer((HostName, ServerPort), MyHandler)
        logging.info('Started http server')
        MyWebServer.serve_forever()
    except KeyboardInterrupt:
        logging.info('Stopped HTTP server')
        MyWebServer.socket.close()