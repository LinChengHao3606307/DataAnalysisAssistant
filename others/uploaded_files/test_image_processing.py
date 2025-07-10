#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图片处理测试脚本
演示如何使用get_blue.py处理图片
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from get_blue import process_image

def test_image_processing():
    """测试图片处理功能"""
    
    # 测试图片路径（你需要提供一个实际的PNG图片）
    test_image = "test_image.png"
    
    # 检查测试图片是否存在
    if not os.path.exists(test_image):
        print(f"测试图片 {test_image} 不存在")
        print("请将PNG图片重命名为 test_image.png 并放在同一目录下")
        return
    
    print("开始测试图片处理...")
    print("=" * 50)
    
    # 处理图片
    success = process_image(test_image)
    
    if success:
        print("=" * 50)
        print("测试完成！")
        print(f"处理后的图片保存为: {os.path.splitext(test_image)[0]}_processed.png")
    else:
        print("测试失败！")

if __name__ == "__main__":
    test_image_processing() 