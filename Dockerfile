# Sử dụng base image Python chính thức
FROM python:3.11-slim

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED True
ENV APP_HOME /app

# Tạo và chuyển đến thư mục làm việc
WORKDIR $APP_HOME

# Sao chép file requirements và cài đặt các dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ code của ứng dụng vào image
COPY . .

# Chạy ứng dụng bằng uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]