import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading

class SerialReaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Port Ma'lumot Tekshiruvchi")
        self.serial_conn = None
        self.running = False

        # Port tanlash
        self.port_label = tk.Label(root, text="Portni tanlang:")
        self.port_label.pack(pady=5)

        self.port_combobox = ttk.Combobox(root, values=self.get_ports(), state="readonly", width=30)
        self.port_combobox.pack(pady=5)

        # Ulanish tugmasi
        self.connect_button = tk.Button(root, text="Ulanish", command=self.connect_serial)
        self.connect_button.pack(pady=5)

        # Natija oynasi
        self.output_text = tk.Text(root, height=15, width=50, state="disabled")
        self.output_text.pack(pady=10)

        # Disconnect tugmasi
        self.disconnect_button = tk.Button(root, text="Uzish", command=self.disconnect_serial, state="disabled")
        self.disconnect_button.pack(pady=5)

    def get_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect_serial(self):
        port = self.port_combobox.get()
        if not port:
            messagebox.showwarning("Xatolik", "Iltimos, portni tanlang!")
            return

        try:
            self.serial_conn = serial.Serial(port, baudrate=9600, timeout=1)
            self.running = True
            self.connect_button.config(state="disabled")
            self.disconnect_button.config(state="normal")
            threading.Thread(target=self.read_serial, daemon=True).start()
            self.log(f"{port} ga ulandi ✅")
        except Exception as e:
            messagebox.showerror("Xatolik", f"Portga ulanishda xato: {e}")

    def read_serial(self):
        while self.running and self.serial_conn.is_open:
            try:
                data = self.serial_conn.readline().decode(errors="ignore").strip()
                if data:
                    self.log(f"Ma'lumot: {data}")
            except Exception as e:
                self.log(f"Xatolik: {e}")
                break

    def disconnect_serial(self):
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.connect_button.config(state="normal")
        self.disconnect_button.config(state="disabled")
        self.log("Ulanish uzildi ❌")

    def log(self, message):
        self.output_text.config(state="normal")
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialReaderApp(root)
    root.mainloop()
