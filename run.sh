#!/bin/bash
# Work Assistant 启动脚本

# 进入项目目录
cd /home/wang/work-assistant

# 激活conda环境并运行
source /home/wang/miniconda3/etc/profile.d/conda.sh
conda activate work-assistant

python src/main.py "$@"
