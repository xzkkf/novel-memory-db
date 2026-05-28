#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说结构化处理引擎 - 剧情记忆数据库构建器
"""

import os
import re
import json
from pathlib import Path

CHAPTERS_DIR = "E:/cozi/project_20260527_163636/projects/chapters"
OUTPUT_FILE = "E:/WORKBUDDY/2026-05-27-17-14-22/novel_memory_db.json"

def extract_chapter_number(filename):
    """从文件名提取章节数字"""
    match = re.search(r'第(\d+)章', filename)
    if match:
        return int(match.group(1))
    return 0

def extract_chapter_title(filename):
    """从文件名提取章节标题"""
    # 移除.txt后缀和"第X章"前缀
    title = filename.replace('.txt', '')
    title = re.sub(r'第\d+章\s*', '', title)
    return title.strip()

def split_into_scenes(content, chapter_num, chapter_title):
    """
    将章节内容拆分为场景
    基于以下边界：
    1. 时间跳跃（如"片刻之后"、"数小时后"、"第二天"等）
    2. 地点转换（如"——"分隔线、地点名称变化）
    3. 视角切换
    4. 战斗开始/结束标记
    5. 段落间的空行分隔（可能是场景切换）
    """
    scenes = []
    
    # 先按段落分割
    paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
    
    if not paragraphs:
        return scenes
    
    # 场景边界检测模式
    scene_boundary_patterns = [
        r'^——+',  # 分隔线
        r'^(片刻之后|数秒之后|数分钟之后|数小时之后|不久之后|随后|紧接着|然后|接下来|第二天|当天|此时此刻|就在这时|与此同时)',
        r'^(位于|在.*[之中|里面|区域|地方]|回到|前往|来到|进入)',
        r'^(【|「).*',  # 系统提示或特殊标记
        r'^(对战|战斗|比赛|挑战).*开始',
        r'^(.*章\s+.*)$',  # 章节标题本身
    ]
    
    current_scene_texts = []
    scene_index = 1
    
    for i, para in enumerate(paragraphs):
        # 检查是否是场景边界
        is_boundary = False
        
        # 检查分隔线
        if re.match(r'^——+$', para) and len(para) >= 2:
            is_boundary = True
        
        # 检查时间/地点转换词
        if re.match(r'^(片刻之后|数秒之后|数分钟之后|数小时之后|不久之后|随后|紧接着|然后|接下来|第二天|当天|此时此刻|就在这时|与此同时|下一秒|不一会|不久|之后|紧接着|随后)', para):
            is_boundary = True
        
        # 检查地点转换
        if re.match(r'^(位于|在.*[之中|里面|区域|地方]|回到|前往|来到|进入|离开|走出|回到|前往)', para):
            is_boundary = True
        
        # 检查对战/战斗开始
        if re.match(r'^(【.*开始|对战开始|战斗开始|比赛开始)', para):
            is_boundary = True
        
        # 检查系统提示
        if para.startswith('【') and ('提示' in para or '系统' in para or '开始' in para or '结束' in para):
            is_boundary = True
        
        # 如果是边界且当前场景有内容，保存当前场景
        if is_boundary and current_scene_texts:
            scene_text = '\n'.join(current_scene_texts)
            scenes.append({
                'chapter_num': chapter_num,
                'chapter_title': chapter_title,
                'scene_index': scene_index,
                'text': scene_text
            })
            scene_index += 1
            current_scene_texts = []
        
        current_scene_texts.append(para)
    
    # 保存最后一个场景
    if current_scene_texts:
        scene_text = '\n'.join(current_scene_texts)
        scenes.append({
            'chapter_num': chapter_num,
            'chapter_title': chapter_title,
            'scene_index': scene_index,
            'text': scene_text
        })
    
    # 如果整个章节只有一个场景，尝试按更细粒度分割
    if len(scenes) <= 1 and len(paragraphs) > 5:
        scenes = []
        # 按约每3-5个段落一个场景来分
        chunk_size = max(3, len(paragraphs) // 3)
        for i in range(0, len(paragraphs), chunk_size):
            chunk = paragraphs[i:i+chunk_size]
            scene_text = '\n'.join(chunk)
            scenes.append({
                'chapter_num': chapter_num,
                'chapter_title': chapter_title,
                'scene_index': len(scenes) + 1,
                'text': scene_text
            })
    
    return scenes

def generate_memory_card(scene):
    """
    为场景生成剧情记忆卡
    提取：谁，在什么情境下，发生了什么核心事件
    """
    text = scene['text']
    chapter_num = scene['chapter_num']
    scene_index = scene['scene_index']
    chapter_title = scene['chapter_title']
    
    # 提取关键信息
    lines = text.split('\n')
    first_line = lines[0][:50] if lines else ""
    
    # 检测核心事件类型
    event_type = "一般叙事"
    
    # 检测对战/战斗
    if any(kw in text for kw in ['对战', '战斗', 'VS', '胜利', '失败', '击败', '秒杀', '攻击', '战技', '进化']):
        if '进化' in text and ('觉醒' in text or '形态' in text or '路线' in text):
            event_type = "进化/觉醒"
        else:
            event_type = "对战/战斗"
    
    # 检测契约/收服
    if any(kw in text for kw in ['契约', '收服', '签订', '获得', '得到']):
        event_type = "契约/获得"
    
    # 检测情感/关系
    if any(kw in text for kw in ['吻', '喜欢', '爱', '老婆', '结婚', '婚宠', '感情', '心动']):
        event_type = "情感/关系"
    
    # 检测揭露/真相
    if any(kw in text for kw in ['暴露', '揭露', '真相', '身份', '秘密', '发现']):
        event_type = "揭露/真相"
    
    # 检测训练/成长
    if any(kw in text for kw in ['训练', '练级', '强化', '锻炼', '提升', '突破']):
        event_type = "训练/成长"
    
    # 生成简洁摘要（取前100字作为摘要基础）
    summary = text[:120].replace('\n', ' ').strip()
    if len(summary) > 100:
        summary = summary[:97] + "..."
    
    return {
        'chapter_num': chapter_num,
        'chapter_title': chapter_title,
        'scene_index': scene_index,
        'event_type': event_type,
        'summary': summary,
        'full_text': text
    }

def main():
    # 获取所有章节文件
    chapters_dir = Path(CHAPTERS_DIR)
    chapter_files = sorted(
        [f for f in chapters_dir.iterdir() if f.suffix == '.txt'],
        key=lambda f: extract_chapter_number(f.name)
    )
    
    print(f"发现 {len(chapter_files)} 个章节文件")
    
    all_scenes = []
    all_memory_cards = []
    
    for chapter_file in chapter_files:
        chapter_num = extract_chapter_number(chapter_file.name)
        chapter_title = extract_chapter_title(chapter_file.name)
        
        try:
            with open(chapter_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败 {chapter_file.name}: {e}")
            continue
        
        # 拆分场景
        scenes = split_into_scenes(content, chapter_num, chapter_title)
        
        if not scenes:
            # 如果无法拆分，整个章节作为一个场景
            scenes = [{
                'chapter_num': chapter_num,
                'chapter_title': chapter_title,
                'scene_index': 1,
                'text': content
            }]
        
        all_scenes.extend(scenes)
        
        # 生成记忆卡
        for scene in scenes:
            memory_card = generate_memory_card(scene)
            all_memory_cards.append(memory_card)
        
        print(f"第{chapter_num}章 '{chapter_title}' -> {len(scenes)} 个场景")
    
    # 构建数据库
    database = {
        'metadata': {
            'total_chapters': len(chapter_files),
            'total_scenes': len(all_scenes),
            'novel_title': '月光兔传奇',
            'processed_date': '2026-05-27'
        },
        'chapter_tree': {},
        'memory_cards': all_memory_cards,
        'scene_index': {}
    }
    
    # 构建章节树
    for card in all_memory_cards:
        ch_num = card['chapter_num']
        if ch_num not in database['chapter_tree']:
            database['chapter_tree'][ch_num] = {
                'title': card['chapter_title'],
                'scenes': []
            }
        database['chapter_tree'][ch_num]['scenes'].append({
            'scene_index': card['scene_index'],
            'event_type': card['event_type'],
            'summary': card['summary']
        })
    
    # 构建场景索引
    for i, card in enumerate(all_memory_cards):
        key = f"{card['chapter_num']}-{card['scene_index']}"
        database['scene_index'][key] = i
    
    # 保存数据库
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
    
    print(f"\n处理完成！")
    print(f"总章节数: {database['metadata']['total_chapters']}")
    print(f"总场景数: {database['metadata']['total_scenes']}")
    print(f"数据库已保存至: {OUTPUT_FILE}")
    
    return database

if __name__ == '__main__':
    main()
