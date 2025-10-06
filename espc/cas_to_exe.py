import serial
import time
import re
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox


class ScaleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Весы КАС - Мониторинг")
        self.root.geometry("400x200")

        # Переменные
        self.weight_var = tk.StringVar(value="0.00 кг")
        self.status_var = tk.StringVar(value="Ожидание данных...")

        # GUI элементы
        self.create_widgets()

        # Настройка COM-порта
        self.ser = None
        self.connect_serial()

        # Запуск обновления данных
        self.update_scale_data()

    def create_widgets(self):
        # Стиль
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 14))
        style.configure("TButton", font=("Arial", 12))

        # Основные элементы
        ttk.Label(self.root, text="Текущий вес:", font=("Arial", 16)).pack(pady=5)
        ttk.Label(self.root, textvariable=self.weight_var, font=("Arial", 24, "bold")).pack(pady=10)
        ttk.Label(self.root, textvariable=self.status_var, foreground="gray").pack(pady=5)

        # Кнопка выхода
        ttk.Button(self.root, text="Выход", command=self.root.quit).pack(pady=10)

    def connect_serial(self):
        try:
            self.ser = serial.Serial(
                port="COM1",
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            self.status_var.set("✅ Подключено к COM1")
        except Exception as e:
            self.status_var.set(f"❌ Ошибка: {str(e)}")
            self.weight_var.set("0.00 кг")

    def read_scale_data(self):
        try:
            if self.ser and self.ser.is_open:
                self.ser.write(b'P\r\n')  # Команда для запроса веса
                time.sleep(0.2)

                if self.ser.in_waiting:
                    response = self.ser.read(self.ser.in_waiting)
                    if response:
                        data = response.decode(errors='ignore').strip()
                        match = re.search(r'[-+]?\d*\.\d+|\d+', data)
                        if match:
                            weight = float(match.group())
                            return weight
        except Exception as e:
            self.status_var.set(f"❌ Ошибка: {str(e)}")
        return None

    def update_scale_data(self):
        weight = self.read_scale_data()
        if weight is not None:
            self.weight_var.set(f"{weight:.2f} кг")
            now = datetime.now().strftime("%H:%M:%S")
            self.status_var.set(f"Последнее обновление: {now}")
        else:
            self.weight_var.set("0.00 кг")

        # Повторяем каждые 500 мс
        self.root.after(500, self.update_scale_data)


if __name__ == "__main__":
    root = tk.Tk()
    app = ScaleApp(root)
    root.mainloop()