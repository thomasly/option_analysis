# 金融数据分析模块

这是一个独立的金融数据分析模块，提供FFT分析和相关性分析功能。

## 功能特性

### FFT分析
- 股票数据的傅里叶变换分析
- 线性趋势拟合和残差分析
- 周期成分提取和重建
- 综合趋势预测

### 相关性分析
- 柯西波函数与股票价格的相关性分析
- 透明度映射可视化
- 多参数相关性计算

## 安装依赖

```bash
pip install -r requirements.txt
```

## 环境配置

1. 复制环境变量文件：
```bash
cp ../env_example.txt .env
```

2. 在`.env`文件中配置Tushare API Token：
```
TUSHARE_TOKEN=your_tushare_token_here
```

## 使用方法

### 运行所有分析
```bash
python main.py
```

### 只运行FFT分析
```bash
python main.py --analysis-type fft
```

### 只运行相关性分析
```bash
python main.py --analysis-type correlation
```

### 设置日志级别
```bash
python main.py --log-level DEBUG
```

## 项目结构

```
analysis_module/
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py          # 配置管理
│   └── core/
│       ├── __init__.py
│       ├── data_fetcher.py    # 数据获取
│       ├── fft_analyzer.py    # FFT分析器
│       ├── quantum_model.py   # 量子模型
│       └── correlation_analyzer.py  # 相关性分析器
├── data/                      # 数据缓存目录
├── analysis_results/          # 分析结果输出目录
├── main.py                    # 主入口文件
├── requirements.txt           # 依赖文件
└── README.md                  # 说明文档
```

## 配置说明

### FFT分析配置
- `analysis_years`: 分析年数（默认15年）
- `num_components`: 周期成分数量（默认6个）
- `frequencies`: 分析频率（日线、周线）

### 相关性分析配置
- `index_code`: 指数代码（默认399006.SZ）
- `years`: 数据年数（默认2年）
- `n_days`: 分析天数（默认11天）
- `n_centers`: 中心点数量（默认11个）
- `n_gammas`: 伽马参数数量（默认8个）

## 输出文件

### FFT分析输出
- `{股票代码}_{频率}_linear_residuals.png`: 线性拟合残差图
- `{股票代码}_{频率}_residual_cycles.png`: 残差周期分析图
- `{日期}_{股票代码}_{频率}_combined_analysis.png`: 综合趋势分析图

### 相关性分析输出
- `step13_transparency.png`: 柯西波函数透明度图

## 注意事项

1. 首次运行需要从Tushare API获取数据，可能需要较长时间
2. 数据会自动缓存到`data/`目录，后续运行会更快
3. 分析结果保存在`analysis_results/`目录
4. 确保有足够的磁盘空间存储数据和结果 