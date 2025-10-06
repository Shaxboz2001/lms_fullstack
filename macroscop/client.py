import serial
import requests
import time
import tkinter as tk
import threading
import re

CHANNEL_PORTS = {
    "Авто КПП2 весовой (вход 1)": "COM1",
    "Авто КПП2 весовой (выход 1)": "COM8"
}

FASTAPI_SERVER = "http://172.16.7.26:8000"
running = False
channel_widgets = {}

def clean_weight(raw_data: str) -> str:
    match = re.search(r"(\d+)\s*kg", raw_data)
    if match:
        return match.group(1)
    match = re.search(r"(\d+)", raw_data)
    if match:
        return match.group(1)
    return "0"


def read_weight_from_port(port_name: str) -> str:
    try:
        ser = serial.Serial(port=port_name, baudrate=9600, timeout=2)
        readings = []
        for _ in range(3):
            raw_data = ser.readline().decode("utf-8", errors="ignore").strip()
            weight = clean_weight(raw_data)
            if weight.isdigit():
                readings.append(weight)
            time.sleep(0.3)
        ser.close()

        if readings and len(set(readings)) == 1:
            return readings[0]
        else:
            print(f"[!] {port_name} → Vazn stabil emas: {readings}")
            return "0"
    except Exception as e:
        print(f"[X] {port_name} xato:", e)
        return "0"


def worker():
    while running:
        try:
            response = requests.get(f"{FASTAPI_SERVER}/weight_request", timeout=5)
            if response.status_code == 200:
                data = response.json()
                channel_name = data.get("channel_name")
                request_id = data.get("request_id")

                port_name = CHANNEL_PORTS.get(channel_name)
                if not port_name:
                    print(f"[X] {channel_name} uchun COM topilmadi")
                    continue

                weight = read_weight_from_port(port_name)
                update_display(channel_name, port_name, weight)

                payload = {
                    "request_id": request_id,
                    "channel_name": channel_name,
                    "weight": weight
                }
                requests.post(f"{FASTAPI_SERVER}/weight_response", json=payload)
                print(f"[→] Javob yuborildi: {payload}")

            time.sleep(1)

        except Exception as e:
            print("[X] Worker xato:", e)
            time.sleep(3)


def start():
    global running
    if not running:
        running = True
        threading.Thread(target=worker, daemon=True).start()
        print("[▶️] Klient ishga tushdi")


def stop():
    global running
    running = False
    print("[⏹] Klient to‘xtatildi")


def reset():
    for widget in channel_widgets.values():
        widget["channel"].config(text="Kanal: -")
        widget["port"].config(text="Port: -")
        widget["weight"].config(text="Og‘irlik: - kg")
    print("[🔄] GUI reset qilindi")


def update_display(channel, port, weight):
    if channel in channel_widgets:
        channel_widgets[channel]["channel"].config(text=f"Kanal: {channel}")
        channel_widgets[channel]["port"].config(text=f"Port: {port}")
        channel_widgets[channel]["weight"].config(text=f"Og‘irlik: {weight} kg")


# ================= GUI =================
root = tk.Tk()
root.title("CAS Tarozi Klienti")

frame = tk.Frame(root)
frame.pack(pady=10)

for i, (channel, port) in enumerate(CHANNEL_PORTS.items()):
    card = tk.LabelFrame(frame, text=channel, bd=3, relief="ridge", font=("Arial", 12, "bold"), padx=10, pady=10)
    card.grid(row=i, column=0, padx=10, pady=10, sticky="w")

    lbl_channel = tk.Label(card, text=f"Kanal: {channel}", font=("Consolas", 11))
    lbl_channel.pack(anchor="w")

    lbl_port = tk.Label(card, text=f"Port: {port}", font=("Consolas", 11))
    lbl_port.pack(anchor="w")

    lbl_weight = tk.Label(card, text="Og‘irlik: - kg", font=("Consolas", 11, "bold"))
    lbl_weight.pack(anchor="w")

    channel_widgets[channel] = {
        "channel": lbl_channel,
        "port": lbl_port,
        "weight": lbl_weight
    }

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="▶️ Start", command=start, width=12, bg="lightgreen").grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="⏹ Stop", command=stop, width=12, bg="tomato").grid(row=0, column=1, padx=5)
tk.Button(btn_frame, text="🔄 Reset", command=reset, width=12, bg="lightblue").grid(row=0, column=2, padx=5)

root.mainloop()
