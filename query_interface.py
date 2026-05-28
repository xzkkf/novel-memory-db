#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剧情记忆数据库查询接口
用于漫剧改编时的剧情回溯和查询
"""

import json

DB_PATH = "novel_memory_db.json"

def load_db():
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_chapter_scenes(chapter_num):
    """获取指定章节的所有场景"""
    db = load_db()
    ch_key = str(chapter_num)
    if ch_key in db['chapter_tree']:
        return db['chapter_tree'][ch_key]['scenes']
    return []

def get_story_recap(chapter_num, scene_index=None, max_events=10):
    """获取前情提要"""
    db = load_db()
    context = []
    for card in db['memory_cards']:
        if card['chapter_num'] < chapter_num:
            if card['event_type'] in ['进化/觉醒', '契约/获得', '揭露/真相', '情感/关系', '对战/战斗']:
                context.append(card)
        elif card['chapter_num'] == chapter_num and scene_index and card['scene_index'] <= scene_index:
            if card['event_type'] in ['进化/觉醒', '契约/获得', '揭露/真相', '情感/关系', '对战/战斗']:
                context.append(card)
    
    context.sort(key=lambda x: (x['chapter_num'], x['scene_index']))
    return context[-max_events:]

def search_by_keyword(keyword, max_results=20):
    """按关键词搜索场景"""
    db = load_db()
    results = []
    for card in db['memory_cards']:
        if keyword in card['full_text'] or keyword in card['chapter_title']:
            results.append(card)
    return results[:max_results]

def get_character_arc(character_name):
    """获取角色的剧情线"""
    db = load_db()
    arc = []
    for card in db['memory_cards']:
        if character_name in card['full_text']:
            if card['event_type'] in ['进化/觉醒', '契约/获得', '揭露/真相', '情感/关系']:
                arc.append(card)
    arc.sort(key=lambda x: (x['chapter_num'], x['scene_index']))
    return arc

if __name__ == '__main__':
    print("剧情记忆数据库查询接口已加载")
    print("可用函数：")
    print("  - get_chapter_scenes(chapter_num) - 获取章节场景")
    print("  - get_story_recap(chapter_num, scene_index) - 获取前情提要")
    print("  - search_by_keyword(keyword) - 关键词搜索")
    print("  - get_character_arc(character_name) - 角色剧情线")
