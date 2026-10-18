# Bài Thực Hành Số 2: Thu thập, lưu trữ và tiền xử lý dữ liệu IoT

Dự án này là một pipeline hoàn chỉnh giúp thu thập dữ liệu cảm biến (Nhiệt độ, Độ ẩm, Khoảng cách) từ thiết bị nhúng (ESP32 mô phỏng trên Wokwi), truyền qua giao thức MQTT, lưu trữ vào MongoDB Atlas trên Cloud, tiền xử lý dữ liệu, và trực quan hóa thời gian thực bằng Dashboard.

## 🛠️ Yêu Cầu Hệ Thống

1. **Phần cứng/Mô phỏng:** 
   - Trình duyệt web để chạy mô phỏng ESP32 trên [Wokwi](https://wokwi.com/).
2. **Phần mềm:**
   - Ngôn ngữ: Python 3 (Hỗ trợ tốt trên phiên bản 32-bit).
   - Cơ sở dữ liệu: Tài khoản MongoDB Atlas (Cloud).
   - MQTT Broker: HiveMQ (Public Broker: `broker.hivemq.com`).

## 📂 Cấu Trúc Mã Nguồn

- `ESP-32`: Thư mục bao gồm mã nguồn C++ của ESP-32, sơ đồ hệ thống, thư viện được chạy trên trình mô phỏng wokwi  .
- `data_collector.py`: Script Python đăng ký (subscribe) MQTT và ghi dữ liệu thô vào MongoDB.
- `preprocess.py`: Script làm sạch dữ liệu, lọc nhiễu, chuẩn hóa và lưu sang bảng mới.
- `app.py`: Dashboard giao diện tối (Dark mode) vẽ biểu đồ real-time và đánh giá độ trễ, hiệu năng.

## 🚀 Hướng Dẫn Cài Đặt và Chạy

### Bước 1: Cài đặt thư viện Python
Mở Terminal/Command Prompt (CMD) và chạy lệnh sau để cài đặt các thư viện cần thiết:
```bash
pip install paho-mqtt pandas numpy pymongo[srv] certifi matplotlib python-dotenv
```

### Bước 2: Cấu hình MongoDB Atlas
1. Đăng nhập MongoDB Atlas, tạo database tên là `IOT_LAB_2`.
2. Lấy chuỗi kết nối (Connection String) của bạn.
3. Mở các file `data_collector.py`, `preprocess.py` và `app_matplotlib.py`.
4. Tạo file .env và gán biến `ATLAS_URI` bằng chuỗi kết nối của bạn.
   *Ví dụ: `ATLAS_URI = "mongodb+srv://<username>:<password>@cluster0...`*

### Bước 3: Chạy thiết bị gửi dữ liệu (ESP32)
1. Mở trang Wokwi và tạo một project ESP32 với cảm biến DHT22, HC-SR04.
2. Dán mã nguồn `esp32_code.ino` vào cửa sổ code.
3. Bấm **Nút Play (Run)** trên Wokwi. Mở tab Serial Monitor để đảm bảo thiết bị báo "Đã kết nối MQTT" và đang publish dữ liệu.

### Bước 4: Chạy hệ thống thu thập (Background)
Mở một terminal mới, chạy script để hứng dữ liệu từ Broker và lưu vào MongoDB:
```bash
python data_collector.py
```
*(Cứ để terminal này chạy ngầm để liên tục nhận dữ liệu)*

### Bước 5: Giám sát bằng Dashboard (Real-time)
Mở một terminal thứ 2, chạy giao diện theo dõi:
```bash
python app_matplotlib.py
```
Một cửa sổ ứng dụng sẽ hiện lên, tự động cập nhật biểu đồ và hiển thị thông số độ trễ mỗi 3 giây.

### Bước 6: Tiền xử lý dữ liệu (Chạy thủ công)
Khi bạn đã thu thập được một lượng dữ liệu nhất định và muốn làm sạch (bỏ NaN, lọc nhiễu, chuẩn hóa min-max), hãy mở terminal thứ 3 và chạy lệnh:
```bash
python preprocess.py
```
Hệ thống sẽ tính toán và xuất dữ liệu "sạch" vào một collection mới mang tên `sensor_data_processed` trên MongoDB.

## 📝 Lưu ý quan trọng
- Do sử dụng Python 32-bit, hệ thống không dùng Streamlit hay Scikit-learn mà đã được tối ưu hoàn toàn bằng thư viện gốc (Pandas, Matplotlib) để đảm bảo chạy mượt mà không gặp lỗi Dependency.
- Nhớ thay thế `<username>` và `<password>` trong chuỗi `ATLAS_URI` bằng user của database (không phải user đăng nhập web).
