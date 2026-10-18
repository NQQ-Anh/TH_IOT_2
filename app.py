import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
from pymongo import MongoClient
import certifi
import time
from datetime import datetime, timezone
import os 
from dotenv import load_dotenv

load_dotenv()
# 1. Kết nối MongoDB Atlas
ATLAS_URI = os.getenv("ATLAS_URI")
client = MongoClient(ATLAS_URI, tlsCAFile=certifi.where())
db = client['IOT_LAB_2']

# 2. Cấu hình giao diện (Tăng kích thước chiều dọc để chứa 3 biểu đồ)
plt.style.use('dark_background')
fig = plt.figure(figsize=(12, 10)) 
fig.canvas.manager.set_window_title('IoT Smart Dashboard - System Performance')

# Chia lưới (Grid) layout thành 4 hàng: Text hiển thị, Nhiệt độ, Độ ẩm, Khoảng cách
gs = fig.add_gridspec(4, 1, height_ratios=[1.5, 3, 3, 3])
ax_metrics = fig.add_subplot(gs[0])
ax_temp = fig.add_subplot(gs[1])
ax_hum = fig.add_subplot(gs[2])
ax_dist = fig.add_subplot(gs[3]) # Khung biểu đồ mới cho Khoảng cách

def update_graph(frame):
    # Xóa dữ liệu khung hình cũ
    ax_metrics.clear()
    ax_temp.clear()
    ax_hum.clear()
    ax_dist.clear() # Xóa khung khoảng cách cũ
    
    # ---------------- TÍNH TOÁN HIỆU NĂNG & ĐỘ TRỄ ----------------
    start_fetch = time.time()
    cursor_raw = db['sensor_data'].find().sort("timestamp", -1).limit(40)
    df_raw = pd.DataFrame(list(cursor_raw))
    fetch_latency_ms = (time.time() - start_fetch) * 1000
    
    total_docs = db['sensor_data'].count_documents({})
    estimated_size_kb = (total_docs * 150) / 1024 
    
    if not df_raw.empty:
        # Sắp xếp thời gian từ trái sang phải
        df_raw = df_raw.sort_values("timestamp")
        
        # Đo độ trễ E2E
        latest_record_time = df_raw.iloc[-1]['timestamp']
        if latest_record_time.tzinfo is None:
            latest_record_time = latest_record_time.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        e2e_latency_ms = abs((now - latest_record_time).total_seconds()) * 1000
        
        # Lấy các giá trị mới nhất
        latest_temp = df_raw.iloc[-1].get('temperature', 0)
        latest_hum = df_raw.iloc[-1].get('humidity', 0)
        latest_dist = df_raw.iloc[-1].get('distance_cm', 0) # Lấy giá trị khoảng cách
        
        # ---------------- TRÌNH BÀY PANEL THÔNG SỐ (METRICS) ----------------
        ax_metrics.axis('off') 
        
        metrics_text = (
            f"🔥 Nhiệt độ: {latest_temp:.1f} °C      💧 Độ ẩm: {latest_hum:.1f} %      📏 Khoảng cách: {latest_dist:.1f} cm\n\n"
            f"⏱️ Độ trễ truy vấn: {fetch_latency_ms:.0f} ms      🚀 Độ trễ End-to-End: {e2e_latency_ms:.0f} ms\n\n"
            f"💾 Tổng dữ liệu: {total_docs:,} bản ghi      💽 Dung lượng: {estimated_size_kb:.2f} KB"
        )
        
        ax_metrics.text(0.5, 0.5, metrics_text, ha='center', va='center', 
                        fontsize=12, color='#00FFFF', fontweight='bold',
                        bbox=dict(facecolor='#1A1A1A', edgecolor='#00FFFF', boxstyle='round,pad=1', alpha=0.8))
        
        # ---------------- VẼ BIỂU ĐỒ NHIỆT ĐỘ ----------------
        ax_temp.plot(df_raw['timestamp'], df_raw['temperature'], color='#FF4500', marker='o', linewidth=2)
        ax_temp.set_title("📈 Nhiệt độ (°C)", color='white', fontsize=11, pad=5)
        ax_temp.grid(color='#444444', linestyle='--', linewidth=0.5)
        
        # ---------------- VẼ BIỂU ĐỒ ĐỘ ẨM ----------------
        ax_hum.plot(df_raw['timestamp'], df_raw['humidity'], color='#1E90FF', marker='s', linewidth=2)
        ax_hum.set_title("📉 Độ ẩm (%)", color='white', fontsize=11, pad=5)
        ax_hum.grid(color='#444444', linestyle='--', linewidth=0.5)
        
        # ---------------- VẼ BIỂU ĐỒ KHOẢNG CÁCH ----------------
        # Màu xanh lá mạ (#32CD32) và dùng marker hình tam giác ('^')
        ax_dist.plot(df_raw['timestamp'], df_raw['distance_cm'], color='#32CD32', marker='^', linewidth=2)
        ax_dist.set_title("📏 Khoảng cách siêu âm (cm)", color='white', fontsize=11, pad=5)
        ax_dist.grid(color='#444444', linestyle='--', linewidth=0.5)
        
        # Tự động nghiêng chữ ở trục thời gian và định dạng layout gọn gàng
        fig.autofmt_xdate()
        plt.tight_layout()

# Chạy vòng lặp tự động cập nhật mỗi 3000ms (3 giây)
ani = FuncAnimation(fig, update_graph, interval=3000, cache_frame_data=False)
plt.show()