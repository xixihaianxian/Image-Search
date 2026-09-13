# ImageSearch · 本地以图搜图系统

一个**双端**的图片检索项目：`Python` 后端负责深度学习特征提取与相似度检索，`Electron` 桌面端负责交互界面。选择本地图片库目录 → 后端扫盘生成缩略图并入库 → 选一张查询图 → 用 `VGG16` 或 `OpenCLIP` 特征做相似图片搜索，支持全量相似度搜索与 `FAISS` 快速检索，还支持「框选图片局部区域」进行搜索。

---

## 功能特性

- 📁 **本地图库管理**：选择本地目录，后端递归扫描图片、生成缩略图并入库，支持增量更新。
- 🖼️ **分页浏览**：无限滚动分页展示图库缩略图。
- 💻 **两种特征模型**：`VGG16`（512 维）与 `OpenCLIP ViT-B-32`，后端注册模型列表可扩展。
- 🔍 **两种搜索方式**：
  - `slow`：全量遍历计算余弦相似度排序；
  - `swift`：基于 FAISS `IndexFlatIP` 的快速检索（计算相似度的方法仍然是余弦相似度）。
- ✂️ **框选搜索**：在查询图上框选局部区域，用裁剪后的图像进行检索。
- 🖱️ **图片右键菜单**：放大预览、复制路径、在资源管理器中定位、下载原图。
- 🎛️ **TOP-K 可调**：拖动滑杆设置返回的相似图片数量（0–200）（仅在`FAISS`快速搜索时适用）。

---

## 技术栈

|     层     |                          技术                           |
|:----------:|:-------------------------------------------------------:|
|    后端    | FastAPI · SQLAlchemy(async) · SQLite · PyTorch · FAISS  |
|  特征模型  |       VGG16（ImageNet 预训练）· OpenCLIP ViT-B-32       |
|    前端    |      Electron · Vue 3 · Vue Router · electron-vite      |

---

## 目录结构

```
ImageSearch/
├── main.py                        # FastAPI 入口
├── config/
│   └── config.yml                 # 全局配置（权重路径/设备/数据库等）
├── routers/
│   └── retrieve.py                # API 路由层
├── crud/
│   ├── retrieve.py                # 核心业务：入库/缩略图/特征提取/搜索
│   └── inquiry.py                 # 配置加载
├── model/
│   └── retrieve.py                # SQLAlchemy ORM 模型
├── schema/
│   ├── retrieve.py                # Pydantic 请求模型
│   └── response.py                # 统一响应封装
├── utils/
│   ├── database_contrl.py         # 异步 engine/session
│   ├── data_collection.py         # VGG 数据集 / FeatureStripping
│   ├── vgg16_feature_extraction.py
│   └── openclip_feature_extraction.py
├── database/
│   ├── initialize_database.sql    # 建表脚本
│   └── image_search.db            # SQLite 数据库
├── module/                        # 模型权重（被 .gitignore 忽略，需自行准备）
│   ├── vgg16-397923af.pth
│   └── open_clip_model.safetensors
├── upload/                        # 上传的图片与缩略图（运行时生成）
├── vector/                        # 特征向量 .npy（运行时生成）
├── static/                        # 静态资源与文档配图
└── frontend/                      # Electron + Vue 前端
    └── src/
        ├── main/                  # Electron 主进程
        ├── preload/               # contextBridge 桥接
        └── renderer/              # Vue 渲染进程
```

---

## 环境要求

- **Python 3.10+**（依赖 PyTorch，建议 3.10/3.11），当前环境**Python 3.11.11**
- **Node.js 18+**（前端），当前环境**Node.js 22.17.1**
- **CUDA（可选）**：有 NVIDIA GPU 可加速特征提取，无则自动回退 CPU，需要在config.yml文件中设置`device: cpu`

---

## 快速开始

### 1. 安装后端依赖

- `clone`项目
  
  ```bash
  # clone master分支
  git clone -b master https://github.com/xixihaianxian/Image-Search.git
  ```

- 项目提供了对应的 `requirements.txt`，请按需安装（建议使用虚拟环境）：

  ```bash
  # 创建虚拟环境
  conda create -n imagesearch python=3.11

  # 激活环境
  conda activate imagesearch

  # 下载所需的库
  pip install -r requirements.txt
  ```

  ```bash
  # 查看cuda版本
  nvidia-smi
  ```

  > `faiss-cpu` 可替换为 `faiss-gpu`（需匹配 CUDA 版本）。`torch`/`torchvision` 建议按官方指引安装对应 CUDA 版本。

  [torch下载地址](https://pytorch.org/get-started/locally)，根据自身cuda版本下载对应的版本

### 2. 准备模型权重

`module/` 目录下的权重文件被 `.gitignore` 忽略，需自行准备两个文件：

- `module/vgg16-397923af.pth` —— torchvision 的 VGG16 ImageNet 权重；[vgg16权重下载地址](https://download.pytorch.org/models/vgg16-397923af.pth)
- `module/open_clip_model.safetensors` —— OpenCLIP `ViT-B-32` 的 `laion2B-s34B-b79K` 权重（对应配置项 `model_tag: laion/CLIP-ViT-B-32-laion2B-s34B-b79K`）。[laion/CLIP-ViT-B-32-laion2B-s34B-b79K参数下载地址](https://huggingface.co/laion/CLIP-ViT-B-32-laion2B-s34B-b79K)

> VGG16 权重不放在本地时，可将 `config/config.yml` 中的 `weight_path` 置空，代码会回退为在线下载 `VGG16_Weights.IMAGENET1K_V1`。

### 3. 初始化数据库

表结构通过 SQL 脚本手动创建:

```bash
sqlite3 database/image_search.db < database/initialize_database.sql
```

该脚本会创建 `folders`、`images`、`imagefeatures`、`models` 四张表，并预置 `vgg16`、`openclip` 两个模型记录。

### 4. 启动后端

```bash
fastapi dev
```

> 前端写死了后端地址 `http://127.0.0.1:8000`，请保持端口一致。

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

开发模式启动后，首页会检测后端连通状态，绿色圆点表示已连接。

---

## 配置说明（`config/config.yml`）

| 配置项 | 说明 |
|---|---|
| `weight_path` | VGG16 权重路径 |
| `device` | 计算设备，`cuda` 或 `cpu`（无 GPU 时自动回退 CPU） |
| `image_extensions` | 支持的图片扩展名 |
| `gallery_dir` | 上传图片存放目录 |
| `thumbnail.size` | 缩略图最大尺寸（宽 × 高） |
| `database` | 数据库连接与连接池配置 |
| `page_size` | 图库分页每页数量 |
| `vector_dir` | 特征向量存放目录 |
| `open_clip_weight` / `model_tag` | OpenCLIP 权重路径与模型 tag |

---

## 使用流程

1. **进入工作台**：首页点击「进入工作台」。
2. **选择图库目录**：右下角点击「目录」，选择本地图片目录，后端扫盘生成缩略图并入库。
3. **选择查询图**：左侧点击「选择图片」，选中一张图片。
4. **设置参数**：工具栏「方法」选 VGG16 或 OpenCLIP，「搜索」选 slow / swift，滑杆设置 TOP-K。
5. **开始搜索**：点击「开始搜索」，右侧展示相似图片（含相似度百分比）。
6. **框选搜索**（可选）：工具栏「框选」后在查询图上拖动框选局部区域，自动用裁剪图检索。

---

## API 接口

统一前缀 `/retrieve`，响应格式 `{ status, message, data }`。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/retrieve/get/localImage` | 返回本地图片文件 |
| POST | `/retrieve/upload/local/gallery` | 登记本地目录（扫盘 + 缩略图 + 入库） |
| GET | `/retrieve/display/gallery` | 分页获取图库图片 |
| GET | `/retrieve/select/target` | 登记选中的查询图 |
| GET | `/retrieve/display/model` | 获取已注册的特征方法列表 |
| POST | `/retrieve/generate/features` | 为图库批量提取特征向量 |
| POST | `/retrieve/slow/search/images` | 全量相似度搜索 |
| POST | `/retrieve/swift/search/images` | FAISS 快速搜索 |
| POST | `/retrieve/anchor/box/image` | 框选图片搜索（multipart） |

---

## 数据库设计

- **folders**：已登记的本地目录（`folder_path` 唯一，`indicate` 作为缩略图子目录名）。
- **images**：图片记录（绝对 `path`、`thumbnail_path`、`extension`）。
- **imagefeatures**：特征向量 `.npy` 路径（`model` + `path` 唯一）。
- **models**：注册的特征方法（预置 `vgg16`、`openclip`）。

特征向量以 `.npy` 落盘，目录结构为 `vector/<model>/<folder_id>/<相对路径>.npy`。

---

## 注意事项

- 特征向量、上传图片、缩略图、模型权重均在 `.gitignore` 中被忽略，clone 后需重新准备权重并生成特征。
- 首次搜索前需先 `generate/features` 为图库提取特征（前端「开始搜索」会自动先调用）。
- `slow` 搜索为全量遍历，图库较大时耗时明显；`swift`（FAISS）每次搜索会重建索引，适合图库规模固定的场景。
