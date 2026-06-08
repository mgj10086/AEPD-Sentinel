#!/usr/bin/env python
"""FAERS Data Download Script
下载 FDA FAERS 公开数据文件

用法:
    python download_faers.py              # 下载最新季度ASCII数据
    python download_faers.py --year 2024  # 下载指定年份数据
    python download_faers.py --all        # 下载所有可用年份数据（约5-8GB）
"""

import os
import sys
import urllib.request
import zipfile
import argparse

# 下载目标目录
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "downloads")

# FAERS 数据URL模板
BASE_URL = "https://fis.fda.gov/content/Exports"

# 可供下载的季度
QUARTERS = {
    "2024q4": f"{BASE_URL}/faers_ascii_2024q4.zip",
    "2024q3": f"{BASE_URL}/faers_ascii_2024q3.zip",
    "2024q2": f"{BASE_URL}/faers_ascii_2024q2.zip",
    "2024q1": f"{BASE_URL}/faers_ascii_2024q1.zip",
    "2023q4": f"{BASE_URL}/faers_ascii_2023q4.zip",
    "2023q3": f"{BASE_URL}/faers_ascii_2023q3.zip",
}


def download_file(url, dest_path):
    """下载文件并显示进度"""
    print(f"正在下载: {url}")
    print(f"保存到: {dest_path}")

    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 / total_size)
            sys.stdout.write(f"\r进度: {downloaded / 1024 / 1024:.1f}MB / {total_size / 1024 / 1024:.1f}MB ({percent:.1f}%)")
            sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, dest_path, progress_hook)
        print(f"\n下载完成!")
        return True
    except Exception as e:
        print(f"\n下载失败: {e}")
        return False


def extract_zip(zip_path, extract_dir):
    """解压ZIP文件"""
    print(f"正在解压: {zip_path}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)
        print(f"解压完成: {extract_dir}")
        return True
    except Exception as e:
        print(f"解压失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="下载FDA FAERS公开数据")
    parser.add_argument("--year", type=str, help="指定年份 (如 2024)")
    parser.add_argument("--quarter", type=str, help="指定季度 (如 q4)")
    parser.add_argument("--all", action="store_true", help="下载所有可用数据")
    parser.add_argument("--extract", action="store_true", help="下载后自动解压")
    args = parser.parse_args()

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # 确定要下载的季度
    to_download = {}
    if args.all:
        to_download = QUARTERS
    elif args.year and args.quarter:
        key = f"{args.year}{args.quarter}"
        if key in QUARTERS:
            to_download[key] = QUARTERS[key]
        else:
            print(f"未找到: {key}")
            print(f"可用季度: {', '.join(QUARTERS.keys())}")
            return
    elif args.year:
        to_download = {k: v for k, v in QUARTERS.items() if k.startswith(args.year)}
    else:
        # 默认下载最新季度
        latest = list(QUARTERS.keys())[0]
        to_download = {latest: QUARTERS[latest]}

    if not to_download:
        print("没有找到匹配的季度数据")
        return

    print(f"将下载 {len(to_download)} 个季度数据")
    print(f"保存目录: {DOWNLOAD_DIR}")

    for key, url in to_download.items():
        zip_name = f"faers_ascii_{key}.zip"
        zip_path = os.path.join(DOWNLOAD_DIR, zip_name)

        if os.path.exists(zip_path):
            print(f"文件已存在，跳过: {zip_name}")
        else:
            if not download_file(url, zip_path):
                continue

        if args.extract:
            extract_dir = os.path.join(DOWNLOAD_DIR, key)
            if not os.path.exists(extract_dir):
                extract_zip(zip_path, extract_dir)

    print("\n全部完成!")


if __name__ == "__main__":
    main()