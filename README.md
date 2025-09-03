## DATA_SHARK 一个高效的SPARK工作开发平台


能力:
1. 用户权限管理  
2. livy restapi  , kyuubi
3. 资源管理
4. sql, coding模式
5. 流批处理
6. 监控  资源观测
7. duckdb对接
8. 插件机制
9. session模式
10. 运行环境 - oss, 镜像
11. ray对接, dask对接
12. airflow 任务编排, 发布
13. 数据湖开发
14. 变量管理
15. ml, dl, llm, ai 集成
16. pipline coding mode => toolz 管道模式
17. 算子构造
17. 处理大数据集方案, hdfs, oss, s3
16. 系统事件
17. 诊断信息
18. 日志探查
19. 部署方案
21. spark加速方案 todo
22. k8s动态扩缩资源, 水平和垂直扩展
23. 资源队列
24. udf管理
25. graphx图计算
26. 元数据管理
27. 审计日志
28. 字典管理
29. profile



  
strcuture: litestar async api
orm: sqlalchemy
cache: redis
service_: nacos / etcd

load 需要放在平台外侧, 只做request的分发工作
以单体pod部署模式




workspace 级别
rbac 权限控制
secret-key  aksk   openapi集成
dingding, feishu集成



日志: logging
orm: sqlalchemy



```angular2html
project/
├── app/                          # 主应用目录
│   ├── api/                      # API 层
│   │   ├── v1/                   # API 版本
│   │   │   ├── endpoints/        # 端点模块
│   │   │   │   ├── __init__.py
│   │   │   │   ├── users.py
│   │   │   │   ├── items.py
│   │   │   │   └── spark_jobs.py
│   │   │   ├── dependencies.py   # API 依赖
│   │   │   └── router.py         # 路由配置
│   │   └── __init__.py
│   ├── core/                     # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py             # 配置管理
│   │   ├── security.py           # 安全配置
│   │   ├── database.py           # 数据库配置
│   │   └── spark.py              # Spark 配置
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── base.py               # 基础模型
│   │   ├── relational/           # 关系型数据库模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   └── item.py
│   │   └── spark/                # Spark 数据模型
│   │       ├── __init__.py
│   │       ├── analytics.py
│   │       └── etl.py
│   ├── schemas/                  # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── item.py
│   │   └── spark.py
│   ├── services/                 # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── item_service.py
│   │   └── spark_service.py      # Spark 服务
│   ├── crud/                     # CRUD 操作
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   └── item.py
│   ├── jobs/                     # Spark 作业
│   │   ├── __init__.py
│   │   ├── etl/                  # ETL 作业
│   │   │   ├── __init__.py
│   │   │   ├── data_ingestion.py
│   │   │   └── data_transformation.py
│   │   ├── analytics/            # 分析作业
│   │   │   ├── __init__.py
│   │   │   ├── user_analytics.py
│   │   │   └── item_analytics.py
│   │   └── utils/                # 作业工具
│   │       ├── __init__.py
│   │       └── spark_utils.py
│   ├── utils/                    # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py             # 日志配置
│   │   ├── password.py           # 密码工具
│   │   └── date_utils.py         # 日期工具
│   ├── tasks/                    # 异步任务
│   │   ├── __init__.py
│   │   ├── celery_app.py         # Celery 配置
│   │   └── spark_tasks.py        # Spark 异步任务
│   ├── main.py                   # 应用入口
│   └── __init__.py
├── spark/                        # Spark 相关配置
│   ├── config/                   # Spark 配置文件
│   │   ├── spark-local.conf
│   │   ├── spark-cluster.conf
│   │   └── log4j.properties
│   ├── jars/                     # 依赖 jar 包
│   └── scripts/                  # 部署脚本
├── tests/                        # 测试目录
│   ├── __init__.py
│   ├── unit/                     # 单元测试
│   │   ├── test_services.py
│   │   └── test_crud.py
│   ├── integration/              # 集成测试
│   │   ├── test_api.py
│   │   └── test_spark.py
│   └── conftest.py               # 测试配置
├── alembic/                      # 数据库迁移
│   ├── versions/
│   ├── env.py  
│   └── script.py.mako
├── docker/                       # Docker 配置
│   ├── app/
│   │   └── Dockerfile
│   ├── spark/
│   │   └── Dockerfile
│   └── docker-compose.yml
├── scripts/                      # 部署脚本
│   ├── deploy.sh
│   ├── start_spark.sh
│   └── run_migrations.sh
├── requirements/                 # 依赖管理
│   ├── base.txt
│   ├── app.txt
│   ├── spark.txt
│   └── dev.txt
├── .env                          # 环境变量
├── .env.production
├── .env.spark
└── README.md
```

错误码设计