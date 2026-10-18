import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json
import certifi
from datetime import datetime, timezone # Thêm thư viện xử lý thời gian
import os 
from dotenv import load_dotenv

load_dotenv()

# Cấu hình kết nối MongoDB Atlas (Giữ nguyên URI của bạn)
ATLAS_URI = os.getenv("ATLAS_URI")
mongo_client = MongoClient(ATLAS_URI, tlsCAFile=certifi.where())
db = mongo_client['IOT_LAB_2']
collection = db['sensor_data']

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode()) 
        
        # Python tự tạo timestamp chuẩn UTC lúc nhận được tin nhắn
        current_time = datetime.now(timezone.utc)
        
        # Bổ sung đọc trường distance_cm từ ESP32
        doc = {
            "timestamp": current_time, 
            "metadata": { "device_id": payload.get("device_id", "esp32_01") }, 
            "temperature": payload.get("temperature"),
            "humidity": payload.get("humidity"),
            "distance_cm": payload.get("distance_cm") 
        }
        
        collection.insert_one(doc)
        print("Đã ghi thành công lên Atlas:", doc)
    except Exception as e:
        print("Lỗi xử lý:", e)

# Fix cảnh báo Deprecation bằng cách chỉ định rõ Callback API Version 1
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
mqtt_client.on_message = on_message

print("Đang kết nối tới Broker...")
mqtt_client.connect("broker.hivemq.com", 1883, 60)
mqtt_client.subscribe("telemetry/esp32/sensors") 
mqtt_client.loop_forever()