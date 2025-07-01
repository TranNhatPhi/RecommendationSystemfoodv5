#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để sửa chữa các lỗi còn lại trong dữ liệu customer
"""

import pandas as pd
import random


def fix_remaining_issues():
    """Sửa các vấn đề còn lại"""

    print("🔧 SỬA CHỮA CÁC VẤN ĐỀ CÒN LẠI")
    print("=" * 40)

    # Đọc dữ liệu
    df = pd.read_csv('customers_data.csv', encoding='utf-8')

    # Danh sách dietary restrictions hợp lệ
    valid_dietary_restrictions = [
        'vegetarian', 'vegan', 'buddhist_vegetarian', 'no_seafood',
        'no_pork', 'no_beef', 'low_sodium', 'diabetic', 'no_spicy', 'light_meals'
    ]

    fixed_count = 0

    for idx, row in df.iterrows():
        if pd.notna(row['dietary_restrictions']) and row['dietary_restrictions'] != '':
            restrictions = [r.strip() for r in str(
                row['dietary_restrictions']).split(',')]

            # 1. Loại bỏ dietary restrictions không hợp lệ
            valid_restrictions = [
                r for r in restrictions if r in valid_dietary_restrictions]

            # 2. Sửa xung đột vegetarian options
            veg_options = [r for r in valid_restrictions if r in [
                'vegetarian', 'vegan', 'buddhist_vegetarian']]
            if len(veg_options) > 1:
                # Chỉ giữ lại một option vegetarian
                chosen_veg = random.choice(veg_options)
                valid_restrictions = [r for r in valid_restrictions if r not in [
                    'vegetarian', 'vegan', 'buddhist_vegetarian']]
                valid_restrictions.append(chosen_veg)
                fixed_count += 1
                print(
                    f"  🔧 Fixed {row['customer_id']}: Chọn {chosen_veg} từ {veg_options}")

            # 3. Loại bỏ restrictions không hợp lệ
            if len(valid_restrictions) != len(restrictions):
                invalid_removed = [
                    r for r in restrictions if r not in valid_restrictions]
                print(
                    f"  🗑️ Removed invalid restrictions from {row['customer_id']}: {invalid_removed}")
                fixed_count += 1

            # Cập nhật dữ liệu
            df.at[idx, 'dietary_restrictions'] = ','.join(
                valid_restrictions) if valid_restrictions else ''

    # Lưu dữ liệu đã sửa
    df.to_csv('customers_data.csv', index=False, encoding='utf-8')

    print(f"✅ Đã sửa {fixed_count} vấn đề")
    print("🔍 Kiểm tra lại:")

    # Kiểm tra lại
    issues_remaining = 0
    for idx, row in df.iterrows():
        if pd.notna(row['dietary_restrictions']) and row['dietary_restrictions'] != '':
            restrictions = [r.strip() for r in str(
                row['dietary_restrictions']).split(',')]

            # Kiểm tra restrictions không hợp lệ
            invalid_restrictions = [
                r for r in restrictions if r not in valid_dietary_restrictions]
            if invalid_restrictions:
                print(
                    f"  ⚠️ Still invalid: {row['customer_id']} - {invalid_restrictions}")
                issues_remaining += 1

            # Kiểm tra xung đột vegetarian
            veg_options = [r for r in restrictions if r in [
                'vegetarian', 'vegan', 'buddhist_vegetarian']]
            if len(veg_options) > 1:
                print(
                    f"  ⚠️ Still conflicting: {row['customer_id']} - {veg_options}")
                issues_remaining += 1

    if issues_remaining == 0:
        print("  ✅ Tất cả vấn đề đã được sửa!")
    else:
        print(f"  ⚠️ Còn {issues_remaining} vấn đề")

    return df


def create_data_summary():
    """Tạo báo cáo tóm tắt dữ liệu"""

    df = pd.read_csv('customers_data.csv', encoding='utf-8')

    print("\n📊 BÁO CÁO TỔNG KẾT DỮ LIỆU CUSTOMER:")
    print("=" * 50)

    print(f"👥 Tổng số customers: {len(df)}")
    print(f"👨 Nam: {(df['gender'] == 'male').sum()}")
    print(f"👩 Nữ: {(df['gender'] == 'female').sum()}")
    print(f"🏳️ Khác: {(df['gender'] == 'other').sum()}")

    print(f"\n🎯 Health Goals:")
    health_goals_count = {}
    for _, row in df.iterrows():
        if pd.notna(row['health_goals']) and row['health_goals'] != '':
            goals = [g.strip() for g in str(row['health_goals']).split(',')]
            for goal in goals:
                health_goals_count[goal] = health_goals_count.get(goal, 0) + 1

    for goal, count in health_goals_count.items():
        print(f"  - {goal}: {count}")

    print(f"\n🚫 Dietary Restrictions:")
    restrictions_count = {}
    customers_with_restrictions = 0
    for _, row in df.iterrows():
        if pd.notna(row['dietary_restrictions']) and row['dietary_restrictions'] != '':
            customers_with_restrictions += 1
            restrictions = [r.strip() for r in str(
                row['dietary_restrictions']).split(',')]
            for restriction in restrictions:
                restrictions_count[restriction] = restrictions_count.get(
                    restriction, 0) + 1

    print(f"  Customers có hạn chế: {customers_with_restrictions}/{len(df)}")
    for restriction, count in restrictions_count.items():
        print(f"  - {restriction}: {count}")

    print(f"\n🗺️ Regional Preferences:")
    regional_count = df['regional_preferences'].value_counts()
    for region, count in regional_count.items():
        print(f"  - {region}: {count}")

    print(f"\n💰 Budget Range:")
    budget_count = df['budget_range'].value_counts()
    for budget, count in budget_count.items():
        print(f"  - {budget}: {count}")

    print(f"\n👨‍🍳 Cooking Skills:")
    skill_count = df['cooking_skill_level'].value_counts()
    for skill, count in skill_count.items():
        print(f"  - {skill}: {count}")


if __name__ == "__main__":
    # Sửa các vấn đề còn lại
    df = fix_remaining_issues()

    # Tạo báo cáo tổng kết
    create_data_summary()

    print("\n🎉 DỮ LIỆU ĐÃ ĐƯỢC CHUẨN HÓA HOÀN TOÀN!")
