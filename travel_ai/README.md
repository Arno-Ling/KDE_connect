## travel_ai（自驾旅行 AI 助手骨架）

这是一个可运行的最小闭环（MVP）服务端骨架，包含：

- **Gateway**：统一编排入口（意图/路由/缓存/结构化输出）
- **Agents**
  - `InformationAgent`：聚合地图/天气等工具数据，产出候选
  - `StrategyAgent`：在约束（预算/偏好/时间）下做排序与计划生成
- **Tools**：地图与天气工具（支持无 Key 的 mock，后续可接入高德/其他 API）
- **Storage**：本地 SQLite（偏好、POI 缓存、访问记录）

### 快速开始（Windows / PowerShell）

1) 创建虚拟环境并安装依赖

```powershell
cd travel_ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) 启动服务

```powershell
uvicorn travel_ai.api:app --reload --port 8000
```

3) 打开 API 文档

- `http://127.0.0.1:8000/docs`

### 试一下「我饿了」

```powershell
$body = @{
  user_id = "arno"
  lat = 39.9042
  lng = 116.4074
  query = "我饿了，想找小众咖啡馆"
  budget_cny_per_person = 60
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/v1/recommend/food" -ContentType "application/json" -Body $body
```

### 配置（可选）

默认不需要任何 key 也能跑（会使用 mock 数据）。后续你可以在环境变量中配置：

- `AMAP_KEY`：高德 Web 服务 Key（接入真实 POI/路线/逆地理）

