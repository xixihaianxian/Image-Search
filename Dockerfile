# 基础镜像
FROM ubuntu:22.04

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y \
        curl \
        sqlite3 \
        python3 \
        python3-pip && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# 工作目录
WORKDIR /imagesearch

# 安装 Python 依赖
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# 安装 Node.js 依赖
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install

# 创建数据库
COPY database/ ./database/
RUN cd database && \
    rm -f *.db *.sqlite && \
    sqlite3 image_search.db < initialize_database.sql

# 创建运行目录
RUN mkdir -p upload vector

# 项目代码
COPY . .