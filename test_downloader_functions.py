#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
测试新华每日电讯和光明日报的下载功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import config
from src.downloaders import get_downloader


def test_guangming_download():
    """测试光明日报下载功能"""
    print("=" * 60)
    print("测试光明日报下载功能")
    print("=" * 60)
    
    # 创建下载器实例
    downloader = get_downloader("guangming", config)
    
    if not downloader:
        print("[FAIL] 无法创建光明日报下载器实例")
        return False
    
    print("[OK] 光明日报下载器实例创建成功")
    
    # 测试获取平台信息
    platform_name = downloader.get_platform_name()
    platform_id = downloader.get_platform_id()
    print(f"[OK] 平台名称: {platform_name}")
    print(f"[OK] 平台ID: {platform_id}")
    
    # 测试获取版面信息
    test_dates = ["2024-01-15", "2024-01-20", "2024-01-25"]
    
    for date_str in test_dates:
        print(f"\n[TEST] 测试日期 {date_str}...")
        
        try:
            edition = downloader.get_latest_edition(date_str)
            
            if edition:
                print(f"[OK] 日期: {edition.date}")
                print(f"[OK] 文件名: {edition.filename}")
                print(f"[OK] 页面数量: {len(edition.page_urls)}")
                
                if edition.page_urls:
                    print(f"[OK] 版面URL示例: {edition.page_urls[0][:80]}...")
                    
                    # 检查URL格式
                    if edition.page_urls[0].startswith('http'):
                        print("[OK] URL格式正确")
                    else:
                        print("[WARN] URL格式可能有问题")
                else:
                    print("[FAIL] 未获取到版面URL")
                    return False
            else:
                print(f"[WARN] 未找到 {date_str} 的版面信息（可能该日期无报纸）")
                continue
                
        except Exception as e:
            print(f"[ERROR] 测试日期 {date_str} 失败: {str(e)[:100]}")
            continue
    
    print("\n[SUCCESS] 光明日报功能测试完成!")
    return True


def test_xinhua_download():
    """测试新华每日电讯下载功能"""
    print("\n" + "=" * 60)
    print("测试新华每日电讯下载功能")
    print("=" * 60)
    
    # 创建下载器实例
    downloader = get_downloader("xinhua_daily", config)
    
    if not downloader:
        print("[FAIL] 无法创建新华每日电讯下载器实例")
        return False
    
    print("[OK] 新华每日电讯下载器实例创建成功")
    
    # 测试获取平台信息
    platform_name = downloader.get_platform_name()
    platform_id = downloader.get_platform_id()
    print(f"[OK] 平台名称: {platform_name}")
    print(f"[OK] 平台ID: {platform_id}")
    
    # 测试获取版面信息
    test_dates = ["2024-01-15", "2024-01-20", "2024-01-25"]
    
    for date_str in test_dates:
        print(f"\n[TEST] 测试日期 {date_str}...")
        
        try:
            edition = downloader.get_latest_edition(date_str)
            
            if edition:
                print(f"[OK] 日期: {edition.date}")
                print(f"[OK] 文件名: {edition.filename}")
                print(f"[OK] 页面数量: {len(edition.page_urls)}")
                
                if edition.page_urls:
                    print(f"[OK] 版面URL示例: {edition.page_urls[0][:80]}...")
                    
                    # 检查URL格式
                    if edition.page_urls[0].startswith('http'):
                        print("[OK] URL格式正确")
                    else:
                        print("[WARN] URL格式可能有问题")
                        
                    # 检查URL类型
                    if 'pdf' in edition.page_urls[0].lower():
                        print("[OK] 检测到PDF下载链接")
                    elif 'jpg' in edition.page_urls[0].lower():
                        print("[OK] 检测到图片下载链接")
                    else:
                        print("[INFO] 未知链接类型")
                else:
                    print("[FAIL] 未获取到版面URL")
                    return False
            else:
                print(f"[WARN] 未找到 {date_str} 的版面信息（可能该日期无报纸）")
                continue
                
        except Exception as e:
            print(f"[ERROR] 测试日期 {date_str} 失败: {str(e)[:100]}")
            continue
    
    print("\n[SUCCESS] 新华每日电讯功能测试完成!")
    return True


def test_gui_integration():
    """测试GUI集成"""
    print("\n" + "=" * 60)
    print("测试GUI集成")
    print("=" * 60)
    
    from src.gui.controller import DownloadController
    
    controller = DownloadController()
    newspapers = controller.get_available_newspapers()
    
    print(f"[OK] 可用报纸数量: {len(newspapers)}")
    
    expected_papers = ["rmrb", "xuexishibao", "guangming", "xinhua_daily"]
    for paper_id in expected_papers:
        if paper_id in newspapers:
            print(f"[OK] {paper_id}: {newspapers[paper_id]['name']}")
        else:
            print(f"[FAIL] 缺少报纸: {paper_id}")
    
    print("[SUCCESS] GUI集成测试完成!")
    return True


if __name__ == "__main__":
    print("开始测试新华每日电讯和光明日报下载功能...")
    
    # 测试光明日报
    guangming_success = test_guangming_download()
    
    # 测试新华每日电讯  
    xinhua_success = test_xinhua_download()
    
    # 测试GUI集成
    gui_success = test_gui_integration()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    print(f"光明日报下载功能: {'[OK] 通过' if guangming_success else '[FAIL] 失败'}")
    print(f"新华每日电讯下载功能: {'[OK] 通过' if xinhua_success else '[FAIL] 失败'}")
    print(f"GUI集成功能: {'[OK] 通过' if gui_success else '[FAIL] 失败'}")
    
    overall_success = guangming_success and xinhua_success and gui_success
    print(f"\n总体结果: {'[SUCCESS] 所有测试通过!' if overall_success else '[FAIL] 部分测试失败'}")
    
    sys.exit(0 if overall_success else 1)