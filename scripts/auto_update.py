#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动更新脚本
分批检查项目状态，更新Stars和最后更新时间
当项目超过半年未更新且Stars<10k时归档
支持无Token的GitHub API调用（60次/小时限制）
"""

import json
import os
import time
import requests
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")
CONFIG_DIR = os.path.join(SCRIPT_DIR, "config")

GITHUB_API = "https://api.github.com/repos/"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_repo_info(repo_name):
    """通过GitHub API获取项目信息，无需Token"""
    url = f"{GITHUB_API}{repo_name}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "stars": data.get("stargazers_count", 0),
                "last_updated": data.get("updated_at", ""),
                "description": data.get("description", "")
            }
        elif resp.status_code == 403:
            print(f"⚠️  API限制 reached for {repo_name}")
            return None
        else:
            print(f"❌  获取 {repo_name} 失败: {resp.status_code}")
            return None
    except Exception as e:
        print(f"❌  请求异常 {repo_name}: {e}")
        return None

def should_archive(repo, config):
    """判断是否应该归档：半年未更新 且 Stars<10k"""
    threshold_days = config["update_schedule"]["archive_threshold"]["days_since_update"]
    max_stars = config["update_schedule"]["archive_threshold"]["max_stars"]
    
    if not repo.get("last_updated"):
        return False
    
    last_updated = datetime.fromisoformat(repo["last_updated"].replace("Z", "+00:00"))
    cutoff_date = datetime.now(last_updated.tzinfo) - timedelta(days=threshold_days)
    
    return (last_updated < cutoff_date) and (repo.get("stars", 0) < max_stars)

def update_batch():
    config = load_json(os.path.join(CONFIG_DIR, "categories.json"))
    state = load_json(os.path.join(CONFIG_DIR, "batch_state.json"))
    active_repos = load_json(os.path.join(DATA_DIR, "active_repos.json"))
    archived_repos = load_json(os.path.join(DATA_DIR, "archived_repos.json"))
    
    batch_size = config["update_schedule"]["projects_per_batch"]
    api_delay = config["update_schedule"]["api_delay_seconds"]
    current_batch = state["current_batch"]
    total_batches = state["total_batches"]
    
    if current_batch >= total_batches:
        print("🎉 本周所有批次已完成！准备生成README...")
        generate_readmes()
        # 重置批次状态为下周
        state["current_batch"] = 0
        state["week_start"] = datetime.now().isoformat()
        save_json(os.path.join(CONFIG_DIR, "batch_state.json"), state)
        return
    
    start_idx = current_batch * batch_size
    end_idx = min(start_idx + batch_size, len(active_repos))
    batch_repos = active_repos[start_idx:end_idx]
    
    print(f"📦 处理批次 {current_batch + 1}/{total_batches} (项目 {start_idx+1}-{end_idx})")
    
    updated_count = 0
    archived_count = 0
    
    for i, repo in enumerate(batch_repos):
        # 如果项目已有最新数据，跳过API调用
        if repo.get("stars", 0) > 0 and repo.get("last_updated"):
            # 但仍需检查是否需要归档
            if should_archive(repo, config):
                repo["status"] = "archived"
                archived_repos.append(repo)
                active_repos.remove(repo)
                archived_count += 1
                print(f"  📦 归档: {repo['name']} ({repo['stars']}⭐)")
            continue
        
        info = fetch_repo_info(repo["name"])
        if info:
            repo["stars"] = info["stars"]
            repo["last_updated"] = info["last_updated"]
            if info["description"] and not repo.get("description_en"):
                repo["description_en"] = info["description"]
            updated_count += 1
            
            # 检查是否需要归档
            if should_archive(repo, config):
                repo["status"] = "archived"
                archived_repos.append(repo)
                active_repos.remove(repo)
                archived_count += 1
                print(f"  📦 归档: {repo['name']} ({repo['stars']}⭐)")
        
        # API限速保护
        if i < len(batch_repos) - 1:
            time.sleep(api_delay)
    
    # 保存更新后的数据
    save_json(os.path.join(DATA_DIR, "active_repos.json"), active_repos)
    save_json(os.path.join(DATA_DIR, "archived_repos.json"), archived_repos)
    
    # 更新状态
    state["current_batch"] = current_batch + 1
    state["last_run"] = datetime.now().isoformat()
    state["active_count"] = len(active_repos)
    state["archived_count"] = len(archived_repos)
    save_json(os.path.join(CONFIG_DIR, "batch_state.json"), state)
    
    print(f"✅ 批次完成: 更新 {updated_count} 个, 归档 {archived_count} 个")
    print(f"📊 当前活跃: {len(active_repos)} 个, 已归档: {len(archived_repos)} 个")
    
    # 如果这是最后一批，自动生成README
    if state["current_batch"] >= total_batches:
        print("📝 正在生成README文件...")
        generate_readmes()

def generate_readmes():
    """生成中文和英文README"""
    active_repos = load_json(os.path.join(DATA_DIR, "active_repos.json"))
    archived_repos = load_json(os.path.join(DATA_DIR, "archived_repos.json"))
    config = load_json(os.path.join(CONFIG_DIR, "categories.json"))
    categories = {c["id"]: c for c in config["categories"]}
    
    now = datetime.now().strftime("%Y-%m-%d")
    
    # 按分类分组
    active_by_cat = {}
    for repo in active_repos:
        cat = repo["category"]
        if cat not in active_by_cat:
            active_by_cat[cat] = []
        active_by_cat[cat].append(repo)
    
    # 生成中文README
    cn_lines = [
        "# 🔥 实时AI热点追踪",
        "",
        "> 追踪GitHub上最热门的AI开源项目，每周自动更新",
        f"> 最后更新：{now}",
        "",
        "## 📌 项目简介",
        "",
        "本项目旨在实时追踪GitHub上AI领域的热门开源项目，按模型、Agent、工具、应用等维度进行分类汇总。",
        "每周自动检查项目状态，对超过半年未更新且Stars数小于1万的项目归档处理。",
        "",
        "## 📊 活跃项目",
        ""
    ]
    
    for cat_id in categories:
        if cat_id in active_by_cat:
            cat = categories[cat_id]
            repos = sorted(active_by_cat[cat_id], key=lambda x: x.get("stars", 0), reverse=True)
            cn_lines.append(f"### {cat['icon']} {cat['name_cn']}")
            cn_lines.append("")
            cn_lines.append("| 项目 | ⭐ Stars | 最后更新 | 功能简介 |")
            cn_lines.append("|------|---------|---------|---------|")
            for repo in repos:
                stars = repo.get("stars", 0)
                last = repo.get("last_updated", "未知")[:10] if repo.get("last_updated") else "未知"
                desc = repo.get("description_cn", "")
                cn_lines.append(f"| [{repo['name']}](https://github.com/{repo['name']}) | {stars:,} | {last} | {desc} |")
            cn_lines.append("")
    
    if archived_repos:
        cn_lines.append("## 📦 已停止更新")
        cn_lines.append("")
        cn_lines.append("> 以下项目超过半年未更新且Stars<10k，保留记录但不再追踪维护")
        cn_lines.append("")
        cn_lines.append("| 项目 | ⭐ Stars | 最后更新 | 功能简介 | 状态 |")
        cn_lines.append("|------|---------|---------|---------|------|")
        for repo in archived_repos:
            stars = repo.get("stars", 0)
            last = repo.get("last_updated", "未知")[:10] if repo.get("last_updated") else "未知"
            desc = repo.get("description_cn", "")
            cn_lines.append(f"| [{repo['name']}](https://github.com/{repo['name']}) | {stars:,} | {last} | {desc} | ⏹️ 已归档 |")
        cn_lines.append("")
    
    cn_lines.extend([
        "## 📝 更新说明",
        "",
        "- **更新频率**：每周一次，分批次检查",
        "- **归档条件**：超过半年未更新 且 Stars < 10,000",
        "- **数据获取**：通过GitHub API获取（支持无Token模式）",
        "",
        "## 🤝 贡献指南",
        "",
        "欢迎提交PR添加新项目！请参考 [CONTRIBUTING.md](CONTRIBUTING.md)",
        "",
        "## 📄 License",
        "",
        "本项目采用 MIT License"
    ])
    
    with open(os.path.join(PROJECT_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(cn_lines))
    
    # 生成英文README
    en_lines = [
        "# 🔥 Real-time AI Hot Tracking",
        "",
        "> Tracking the hottest AI open-source projects on GitHub, updated weekly",
        f"> Last updated: {now}",
        "",
        "## 📌 About",
        "",
        "This project tracks trending AI open-source projects on GitHub, categorized by models, agents, tools, applications, etc.",
        "Projects are checked weekly. Those inactive for over 6 months with <10k stars are archived.",
        "",
        "## 📊 Active Projects",
        ""
    ]
    
    for cat_id in categories:
        if cat_id in active_by_cat:
            cat = categories[cat_id]
            repos = sorted(active_by_cat[cat_id], key=lambda x: x.get("stars", 0), reverse=True)
            en_lines.append(f"### {cat['icon']} {cat['name_en']}")
            en_lines.append("")
            en_lines.append("| Project | ⭐ Stars | Last Updated | Description |")
            en_lines.append("|---------|---------|--------------|-------------|")
            for repo in repos:
                stars = repo.get("stars", 0)
                last = repo.get("last_updated", "N/A")[:10] if repo.get("last_updated") else "N/A"
                desc = repo.get("description_en", "")
                en_lines.append(f"| [{repo['name']}](https://github.com/{repo['name']}) | {stars:,} | {last} | {desc} |")
            en_lines.append("")
    
    if archived_repos:
        en_lines.append("## 📦 Archived Projects")
        en_lines.append("")
        en_lines.append("> Projects inactive for 6+ months with <10k stars. Kept for reference but no longer tracked.")
        en_lines.append("")
        en_lines.append("| Project | ⭐ Stars | Last Updated | Description | Status |")
        en_lines.append("|---------|---------|--------------|-------------|--------|")
        for repo in archived_repos:
            stars = repo.get("stars", 0)
            last = repo.get("last_updated", "N/A")[:10] if repo.get("last_updated") else "N/A"
            desc = repo.get("description_en", "")
            en_lines.append(f"| [{repo['name']}](https://github.com/{repo['name']}) | {stars:,} | {last} | {desc} | ⏹️ Archived |")
        en_lines.append("")
    
    en_lines.extend([
        "## 📝 Update Notes",
        "",
        "- **Frequency**: Weekly, processed in batches",
        "- **Archive Criteria**: Inactive for 6+ months AND Stars < 10,000",
        "- **Data Source**: GitHub API (supports token-free mode)",
        "",
        "## 🤝 Contributing",
        "",
        "Welcome to submit PRs to add new projects! See [CONTRIBUTING.md](CONTRIBUTING.md)",
        "",
        "## 📄 License",
        "",
        "MIT License"
    ])
    
    with open(os.path.join(PROJECT_DIR, "README_EN.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(en_lines))
    
    print("✅ README.md 和 README_EN.md 已生成")

if __name__ == "__main__":
    update_batch()
