import serial
import websockets
import json
import re
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import queue
import asyncio

# Настройки
COM_PORT = "COM1"
BAUDRATE = 9600
WS_SERVER = "ws://172.16.1.85/ws/"

class ScaleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Весы КАС")

        # Очередь для обмена данными между потоками
        self.ws_queue = queue.Queue()
        self.running = False
        self.ser = None
        self.ws_connected = False
        self.ws_reconnect = True

        # GUI
        self.text_area = scrolledtext.ScrolledText(root, width=60, height=15)
        self.text_area.pack(padx=10, pady=5)

        # Статус бар
        self.status_frame = ttk.Frame(root)
        self.status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.com_status = ttk.Label(self.status_frame, text="COM: Отключено", foreground="red")
        self.com_status.pack(side=tk.LEFT)
        
        self.ws_status = ttk.Label(self.status_frame, text="WebSocket: Отключено", foreground="red")
        self.ws_status.pack(side=tk.LEFT, padx=20)

        # Кнопки управления
        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(pady=5)
        
        self.start_button = ttk.Button(self.button_frame, text="Запуск", command=self.start)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(self.button_frame, text="Стоп", command=self.stop, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)

        # Запуск обработчика WebSocket в отдельном потоке
        self.ws_thread = threading.Thread(target=self.run_ws_client, daemon=True)
        self.ws_thread.start()

    def log(self, message):
        self.text_area.insert(tk.END, message + "\n")
        self.text_area.see(tk.END)

    def update_status(self):
        com_text = "COM: Подключено" if self.ser and self.ser.is_open else "COM: Отключено"
        com_fg = "green" if self.ser and self.ser.is_open else "red"
        
        ws_text = "WebSocket: Подключено" if self.ws_connected else "WebSocket: Отключено"
        ws_fg = "green" if self.ws_connected else "red"
        
        self.com_status.config(text=com_text, foreground=com_fg)
        self.ws_status.config(text=ws_text, foreground=ws_fg)

    def start(self):
        self.running = True
        self.ws_reconnect = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        threading.Thread(target=self.read_scale, daemon=True).start()
        self.update_status()

    def stop(self):
        self.running = False
        self.ws_reconnect = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        if self.ser:
            self.ser.close()
            self.ser = None
        self.update_status()

    def get_weight(self):
        try:
            if not self.ser or not self.ser.is_open:
                self.ser = serial.Serial(COM_PORT, BAUDRATE, timeout=1)
                self.log("Подключено к COM-порту")
                self.update_status()

            self.ser.write(b'P\r\n')
            response = self.ser.read_until(b'\r\n').decode('ascii', errors='ignore').strip()

            match = re.search(r'[-+]?\d*\.\d+|\d+', response)
            if match:
                return float(match.group())
        except Exception as e:
            self.log(f"Ошибка COM-порта: {str(e)}")
            if self.ser:
                self.ser.close()
                self.ser = None
            self.update_status()
            return None

    def read_scale(self):
        while self.running:
            weight = self.get_weight()
            if weight is not None:
                timestamp = datetime.now().isoformat()
                payload = json.dumps({"weight": weight, "timestamp": timestamp})
                self.ws_queue.put(payload)
                self.log(f"Вес: {weight:.2f} кг")
            self.root.after(500, lambda: None)  # Пауза для GUI

    async def ws_sender(self):
        while self.ws_reconnect:
            try:
                async with websockets.connect(WS_SERVER, ping_interval=20) as ws:
                    self.ws_connected = True
                    self.log("Успешное подключение к WebSocket")
                    self.update_status()
                    
                    while self.running and self.ws_reconnect:
                        try:
                            payload = self.ws_queue.get_nowait()
                            await ws.send(payload)
                            self.log(f"Отправлено: {payload}")
                        except queue.Empty:
                            await asyncio.sleep(0.1)
                        except websockets.exceptions.ConnectionClosed:
                            self.log("Соединение WebSocket закрыто")
                            self.ws_connected = False
                            self.update_status()
                            break
                            
            except Exception as e:
                self.ws_connected = False
                self.update_status()
                self.log(f"Ошибка WebSocket: {str(e)}. Переподключение через 5 сек...")
                await asyncio.sleep(5)
                
        self.ws_connected = False
        self.update_status()

    def run_ws_client(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.ws_sender())

if __name__ == "__main__":
    root = tk.Tk()
    app = ScaleApp(root)
    root.protocol("WM_DELETE_WINDOW", app.stop)
    root.mainloop()