#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化种子项目数据
读取 seed_repos.json 并生成 active_repos.json
为每个项目添加初始状态字段
"""

import json
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")

def init_seed_data():
    seed_path = os.path.join(DATA_DIR, "seed_repos.json")
    active_path = os.path.join(DATA_DIR, "active_repos.json")
    archived_path = os.path.join(DATA_DIR, "archived_repos.json")
    state_path = os.path.join(PROJECT_DIR, "scripts", "config", "batch_state.json")
    
    with open(seed_path, "r", encoding="utf-8") as f:
        seed_data = json.load(f)
    
    repos = seed_data["seed_repos"]
    active_repos = []
    
    now = datetime.now().isoformat()
    
    for repo in repos:
        active_repos.append({
            "name": repo["name"],
            "category": repo["category"],
            "description_cn": repo["description_cn"],
            "description_en": repo["description_en"],
            "stars": 0,
            "last_updated": None,
            "added_date": now,
            "status": "active"
        })
    
    # 保存活跃项目
    with open(active_path, "w", encoding="utf-8") as f:
        json.dump(active_repos, f, ensure_ascii=False, indent=2)
    
    # 初始化归档项目（空列表）
    with open(archived_path, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    
    # 更新批次状态
    total = len(active_repos)
    batch_size = 10
    total_batches = (total + batch_size - 1) // batch_size
    
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    
    state["total_projects"] = total
    state["active_count"] = total
    state["archived_count"] = 0
    state["total_batches"] = total_batches
    
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已初始化 {total} 个种子项目到 active_repos.json")
    print(f"📦 批次配置: {total_batches} 批, 每批 {batch_size} 个")

if __name__ == "__main__":
    init_seed_data()
