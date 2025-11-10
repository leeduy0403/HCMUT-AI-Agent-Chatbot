# 1. Chọn Python làm môi trường cơ sở
FROM python:3.11

# 2. Thiết lập thư mục làm việc trong container
WORKDIR /app

# 3. Copy file requirements.txt vào trước để tận dụng cache của Docker
COPY requirements.txt .

# 4. Cài đặt các thư viện cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy toàn bộ code hiện tại vào thư mục /app trong container
COPY . .

# 6. Thông báo port mà backend sẽ chạy (VD: 8000, bạn cần check trong main.py xem nó chạy port nào)
EXPOSE 8000

# 7. Lệnh chạy backend khi container khởi động
CMD ["python", "src/main.py"]