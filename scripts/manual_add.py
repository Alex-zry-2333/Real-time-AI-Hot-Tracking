#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动添加新项目
交互式脚本，输入GitHub URL后自动获取项目信息并选择分类
"""

import json
import os
import requests
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")
CONFIG_DIR = os.path.join(SCRIPT_DIR, "config")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_repo_info(repo_name):
    url = f"https://api.github.com/repos/{repo_name}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "stars": data.get("stargazers_count", 0),
                "last_updated": data.get("updated_at", ""),
                "description": data.get("description", "")
            }
        else:
            print(f"获取失败: HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"请求异常: {e}")
        return None

def manual_add():
    print("=" * 60)
    print("📝 手动添加新项目到实时AI热点追踪")
    print("=" * 60)
    print()
    
    url = input("请输入GitHub项目URL (例如: https://github.com/user/repo): ").strip()
    
    # 解析项目名
    if "github.com/" in url:
        parts = url.split("github.com/")[-1].split("/")
        if len(parts) >= 2:
            repo_name = f"{parts[0]}/{parts[1]}"
        else:
            print("❌ URL格式错误")
            return
    else:
        print("❌ 请输入有效的GitHub URL")
        return
    
    print(f"\n🔍 正在获取 {repo_name} 的信息...")
    info = fetch_repo_info(repo_name)
    
    if not info:
        print("❌ 无法获取项目信息，请检查URL是否正确")
        return
    
    print(f"✅ 获取成功!")
    print(f"   ⭐ Stars: {info['stars']:,}")
    print(f"   📝 描述: {info['description'] or '无'}")
    print(f"   🕐 最后更新: {info['last_updated'][:10] if info['last_updated'] else '未知'}")
    print()
    
    # 加载分类
    config = load_json(os.path.join(CONFIG_DIR, "categories.json"))
    categories = config["categories"]
    
    print("请选择分类:")
    for i, cat in enumerate(categories, 1):
        print(f"  {i}. {cat['icon']} {cat['name_cn']} ({cat['name_en']})")
    print()
    
    while True:
        try:
            choice = int(input("> 输入分类编号: ").strip())
            if 1 <= choice <= len(categories):
                selected_cat = categories[choice - 1]
                break
            else:
                print("❌ 请输入有效编号")
        except ValueError:
            print("❌ 请输入数字")
    
    print(f"\n已选择分类: {selected_cat['icon']} {selected_cat['name_cn']}")
    print()
    
    # 输入中文描述（如果获取到的描述是英文）
    desc_cn = input("请输入中文简介（直接回车使用英文描述）: ").strip()
    if not desc_cn:
        desc_cn = info["description"] or "暂无描述"
    
    desc_en = info["description"] or desc_cn
    
    # 添加到活跃列表
    active_path = os.path.join(DATA_DIR, "active_repos.json")
    active_repos = load_json(active_path)
    
    # 检查是否已存在
    for repo in active_repos:
        if repo["name"] == repo_name:
            print(f"⚠️ 项目 {repo_name} 已存在，跳过添加")
            return
    
    new_repo = {
        "name": repo_name,
        "category": selected_cat["id"],
        "description_cn": desc_cn,
        "description_en": desc_en,
        "stars": info["stars"],
        "last_updated": info["last_updated"],
        "added_date": datetime.now().isoformat(),
        "status": "active"
    }
    
    active_repos.append(new_repo)
    save_json(active_path, active_repos)
    
    # 更新批次状态
    state_path = os.path.join(CONFIG_DIR, "batch_state.json")
    state = load_json(state_path)
    state["total_projects"] = len(active_repos)
    state["active_count"] = len(active_repos)
    total_batches = (len(active_repos) + 10 - 1) // 10
    state["total_batches"] = total_batches
    save_json(state_path, state)
    
    print(f"\n✅ 项目 {repo_name} 已成功添加!")
    print(f"📊 当前活跃项目总数: {len(active_repos)}")
    print(f"📦 总批次已更新为: {total_batches}")
    print()
    print("💡 提示: 运行 'python auto_update.py' 可重新生成README")

if __name__ == "__main__":
    manual_add()
