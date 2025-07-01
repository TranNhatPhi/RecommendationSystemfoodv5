#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để loại bỏ dữ liệu không phù hợp với món ăn
Loại bỏ: "Chính sách bảo vệ dữ liệu cá nhân" và các bản ghi không liên quan đến món ăn
"""

import pandas as pd
import os
import shutil
from datetime import datetime


def backup_files(file_paths):
    """Tạo backup cho các file trước khi chỉnh sửa"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)

    for file_path in file_paths:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, os.path.basename(file_path))
            shutil.copy2(file_path, backup_path)
            print(f"✅ Đã backup: {file_path} -> {backup_path}")

    return backup_dir


def clean_food_data():
    """Loại bỏ dữ liệu không phù hợp với món ăn"""

    # Danh sách các file cần kiểm tra
    files_to_clean = [
        'interactions_enhanced_with_recommendations.csv',
        'interactions_enhanced_final.csv',
        'interactions_enhanced.csv',
        'interactions_encoded.csv'
    ]

    # Keywords để nhận diện dữ liệu không phải món ăn
    invalid_food_keywords = [
        'chính sách bảo vệ',
        'chinh sach bao ve',
        'bảo vệ dữ liệu',
        'bao ve du lieu',
        'privacy policy',
        'terms of service',
        'điều khoản sử dụng',
        'dieu khoan su dung',
        'liên hệ',
        'lien he',
        'contact',
        'about us',
        'về chúng tôi',
        've chung toi',
        'danh mục thực đơn',
        'danh muc thuc don',
        'tìm kiếm',
        'tim kiem',
        'search'
    ]

    # Tạo backup
    existing_files = [f for f in files_to_clean if os.path.exists(f)]
    backup_dir = backup_files(existing_files)

    total_removed = 0

    for file_name in files_to_clean:
        if not os.path.exists(file_name):
            print(f"⚠️ File không tồn tại: {file_name}")
            continue

        print(f"\n🔍 Đang xử lý file: {file_name}")

        try:
            # Đọc file CSV
            df = pd.read_csv(file_name, encoding='utf-8')
            original_count = len(df)
            print(f"📊 Số bản ghi ban đầu: {original_count}")

            # Lọc dữ liệu không hợp lệ
            if 'food_name' in df.columns:
                food_col = 'food_name'
            elif 'dish_name' in df.columns:
                food_col = 'dish_name'
            else:
                # Tìm cột thứ 2 (thường là tên món ăn)
                food_col = df.columns[1] if len(
                    df.columns) > 1 else df.columns[0]

            print(f"🍽️ Sử dụng cột: {food_col}")

            # Tạo mask để loại bỏ dữ liệu không hợp lệ
            mask = pd.Series([True] * len(df))

            for keyword in invalid_food_keywords:
                keyword_mask = ~df[food_col].str.lower(
                ).str.contains(keyword, na=False)
                mask = mask & keyword_mask
                removed_by_keyword = (~keyword_mask).sum()
                if removed_by_keyword > 0:
                    print(
                        f"  🗑️ Loại bỏ {removed_by_keyword} bản ghi chứa '{keyword}'")

            # Áp dụng filter
            df_cleaned = df[mask].copy()
            removed_count = original_count - len(df_cleaned)
            total_removed += removed_count

            print(f"📉 Đã loại bỏ: {removed_count} bản ghi")
            print(f"📈 Còn lại: {len(df_cleaned)} bản ghi")

            # Lưu file đã được làm sạch
            df_cleaned.to_csv(file_name, index=False, encoding='utf-8')
            print(f"✅ Đã lưu file sạch: {file_name}")

        except Exception as e:
            print(f"❌ Lỗi khi xử lý {file_name}: {str(e)}")

    print(f"\n🎉 HOÀN THÀNH!")
    print(f"📊 Tổng số bản ghi đã loại bỏ: {total_removed}")
    print(f"💾 Backup được lưu tại: {backup_dir}")

    return total_removed, backup_dir


def verify_cleaned_data():
    """Kiểm tra dữ liệu sau khi làm sạch"""
    print("\n🔍 KIỂM TRA DỮ LIỆU SAU KHI LÀM SẠCH:")

    files_to_check = [
        'interactions_enhanced_with_recommendations.csv',
        'interactions_enhanced_final.csv',
        'interactions_enhanced.csv'
    ]

    for file_name in files_to_check:
        if os.path.exists(file_name):
            df = pd.read_csv(file_name, encoding='utf-8')
            food_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

            # Kiểm tra xem còn dữ liệu không hợp lệ không
            invalid_entries = df[df[food_col].str.lower().str.contains(
                'chính sách|chinh sach|privacy|contact', na=False)]

            print(f"📄 {file_name}:")
            print(f"  📊 Tổng số bản ghi: {len(df)}")
            print(f"  ⚠️ Bản ghi không hợp lệ còn lại: {len(invalid_entries)}")

            if len(invalid_entries) > 0:
                print(f"  🔍 Các bản ghi không hợp lệ:")
                for _, row in invalid_entries.head(3).iterrows():
                    print(f"    - {row[food_col]}")


if __name__ == "__main__":
    print("🧹 BẮT ĐẦU LÀM SẠCH DỮ LIỆU KHÔNG PHẢI MÓN ĂN")
    print("=" * 60)

    # Thực hiện làm sạch
    total_removed, backup_dir = clean_food_data()

    # Kiểm tra kết quả
    verify_cleaned_data()

    print(f"\n✨ KẾT THÚC! Đã loại bỏ {total_removed} bản ghi không hợp lệ.")
    print(f"📁 Backup: {backup_dir}")
