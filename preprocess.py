import pandas as pd
import numpy as np
from pymongo import MongoClient
import certifi
import os 
from dotenv import load_dotenv

load_dotenv()

# 1. Kết nối cơ sở dữ liệu MongoDB Atlas
ATLAS_URI = os.getenv("ATLAS_URI")
client = MongoClient(ATLAS_URI, tlsCAFile=certifi.where())
db = client['IOT_LAB_2']

def run_preprocessing():
    print("Đang đọc dữ liệu thô từ Database...")
    cursor = db['sensor_data'].find()
    df = pd.DataFrame(list(cursor))
    
    if df.empty:
        print("Không có dữ liệu để xử lý.")
        return

    # Chuyển đổi timestamp thành kiểu Datetime và đặt làm Index để Resampling
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    # --- BƯỚC 1: LÀM SẠCH DỮ LIỆU ---
    df = df.dropna(subset=['temperature', 'humidity', 'distance_cm'])

    # --- BƯỚC 2: PHÁT HIỆN BẤT THƯỜNG (Áp dụng IQR cho Nhiệt độ) ---
    Q1 = df['temperature'].quantile(0.25)
    Q3 = df['temperature'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    # Lọc giữ lại các giá trị nằm trong ngưỡng an toàn
    df = df[(df['temperature'] >= lower_bound) & (df['temperature'] <= upper_bound)]

    # --- BƯỚC 3: RESAMPLING ---
    # Gộp nhóm dữ liệu và tính trung bình mỗi 1 phút ('1T' hoặc '1min')
    df_resampled = df.resample('1T').mean(numeric_only=True).dropna()

    # --- BƯỚC 4: TẠO ĐẶC TRƯNG MỚI ---
    # Tính trung bình trượt (rolling mean) 3 khung thời gian
    df_resampled['temp_rolling_mean'] = df_resampled['temperature'].rolling(window=3).mean()
    # Tính độ chênh lệch (delta) so với phút trước đó
    df_resampled['temp_delta'] = df_resampled['temperature'].diff()
    df_resampled = df_resampled.dropna() # Bỏ các dòng NaN sinh ra ở những phút đầu tiên

    # --- BƯỚC 5: CHUẨN HÓA DỮ LIỆU (Min-Max Scaling thủ công) ---
    for col in ['temperature', 'humidity', 'distance_cm']:
        col_min = df_resampled[col].min()
        col_max = df_resampled[col].max()
        
        # Tránh lỗi chia cho 0 nếu tất cả các giá trị đều bằng nhau
        if col_max != col_min:
            df_resampled[f'{col}_normalized'] = (df_resampled[col] - col_min) / (col_max - col_min)
        else:
            df_resampled[f'{col}_normalized'] = 0.0

    # --- BƯỚC 6: LƯU TRỮ VÀO BẢNG MỚI ---
    df_resampled.reset_index(inplace=True) # Đưa timestamp từ Index về lại thành cột
    
    processed_records = df_resampled.to_dict('records')
    if processed_records:
        # Xóa dữ liệu cũ trong bảng processed để cập nhật bản mới nhất
        db['sensor_data_processed'].delete_many({})
        db['sensor_data_processed'].insert_many(processed_records)
        print(f"Tiền xử lý thành công! Đã lưu {len(processed_records)} bản ghi chuẩn hóa vào database.")

if __name__ == "__main__":
    run_preprocessing()