# 脚本文件路径假设为 c:\Users\user\.myproject\remove_quotes.py
import os

# 定义 keywords.txt 文件的路径
file_path = r'c:\Users\user\.myproject\keywords.txt'

try:
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 去除每行首尾的单引号
    new_lines = [line.strip().strip("'") + '\n' for line in lines]

    # 将处理后的内容写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print("文件处理完成，首尾单引号已去除。")
except Exception as e:
    print(f"处理文件时出现错误: {e}")