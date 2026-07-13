# CrewAI Workstation

Dockerized CrewAI personal work assistant.

## 快速开始

```bash
# 构建镜像
docker build -t crewai-workstation .

# 运行交互式容器
docker run -it --rm \
  -e DEEPSEEK_API_KEY=你的key \
  -v $(pwd)/work:/workspace/work \
  crewai-workstation
```

进入容器后：

```bash
# 运行工作助手
python assistant.py
```

## Docker Compose

```bash
# 创建 .env 文件
echo "DEEPSEEK_API_KEY=你的key" > .env

# 启动
docker compose up -d

# 进入容器
docker exec -it crewai-workstation bash
```

## 架构

- **项目经理** - 拆解任务、分配工作
- **执行专员** - 执行任务、产出成果
- **质量审核员** - 审核质量、打回修改
