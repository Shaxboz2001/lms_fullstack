import serial
import requests
import time

# channel_name -> port mapping
CHANNEL_PORTS = {
    "Kirish": "COM3",
    "Chiqish": "COM4",
    "Sklad": "COM5"
}

FASTAPI_SERVER = "http://127.0.0.1:8000"  # FastAPI server manzili

def read_weight_from_port(port_name: str) -> str:
    try:
        ser = serial.Serial(port=port_name, baudrate=9600, timeout=2)
        weight_data = ser.readline().decode("utf-8").strip()
        ser.close()
        return weight_data if weight_data else "0"
    except Exception as e:
        print(f"[X] {port_name} portidan o‘qishda xato:", e)
        return "0"

def main():
    while True:
        try:
            # FastAPI serveridan so‘rov kutish
            response = requests.get(f"{FASTAPI_SERVER}/weight_request")
            if response.status_code == 200:
                data = response.json()
                channel_name = data.get("channel_name")
                request_id = data.get("request_id")

                port_name = CHANNEL_PORTS.get(channel_name)
                if not port_name:
                    print(f"[X] {channel_name} uchun port topilmadi")
                    continue

                # Portdan o‘qish
                weight = read_weight_from_port(port_name)
                print(f"[✔] {channel_name} ({port_name}) -> {weight} kg")

                # Olingan vaznni serverga yuborish
                requests.post(f"{FASTAPI_SERVER}/weight_response", json={
                    "request_id": request_id,
                    "channel_name": channel_name,
                    "weight": weight
                })

        except Exception as e:
            print("[X] Xato:", e)

        time.sleep(1)  # 1 soniya kutish

if __name__ == "__main__":
    main()
