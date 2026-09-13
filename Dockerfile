# 基础pytorch镜像
FROM pytorch/pytorch:2.12.0-cuda13.0-cudnn9-runtime

# 安装nodejs
RUN apt-get upadte && \
    apt-get -y upgrade && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# 工作目录
WORKDIR /imagesearch

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装nodejs依赖
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install

# 构建数据库
COPY database/* ./

# 项目代码
COPY . .