#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để sửa chữa và chuẩn hóa dữ liệu customer cho phù hợp với form đăng ký
Đảm bảo tính nhất quán và đúng đắn của dữ liệu
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os


def fix_customer_data():
    """Sửa chữa dữ liệu customer để phù hợp với form đăng ký"""

    print("🔧 BẮT ĐẦU SỬA CHỮA DỮ LIỆU CUSTOMER")
    print("=" * 50)

    # Đọc dữ liệu customer
    df = pd.read_csv('customers_data.csv', encoding='utf-8')
    print(f"📊 Số lượng customer: {len(df)}")

    # Backup dữ liệu gốc
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"customers_data_backup_{timestamp}.csv"
    df.to_csv(backup_file, index=False, encoding='utf-8')
    print(f"💾 Đã backup: {backup_file}")

    # Danh sách dietary restrictions phù hợp với form
    valid_dietary_restrictions = [
        'vegetarian',  # Ăn chay
        'vegan',       # Thuần chay
        'buddhist_vegetarian',  # Chay Phật giáo
        'no_seafood',  # Không hải sản
        'no_pork',     # Không thịt heo
        'no_beef',     # Không thịt bò
        'low_sodium',  # Ít muối/mặn
        'diabetic',    # Tiểu đường (ít đường)
        'no_spicy',    # Không ăn cay
        'light_meals'  # Thích món nhẹ
    ]

    # Danh sách health goals hợp lệ
    valid_health_goals = [
        'weight_loss',    # Giảm cân
        'muscle_gain',    # Tăng cơ
        'healthy_eating',  # Ăn uống lành mạnh
        'maintain_weight'  # Duy trì cân nặng
    ]

    # Danh sách regional preferences
    valid_regional_preferences = [
        'northern',     # Miền Bắc
        'central',      # Miền Trung
        'southern',     # Miền Nam
        'all_regions'   # Tất cả vùng miền
    ]

    # Danh sách meal times
    valid_meal_times = [
        'breakfast',  # Sáng
        'lunch',      # Trưa
        'dinner',     # Tối
        'snack'       # Ăn vặt
    ]

    # Danh sách cooking skill levels
    valid_cooking_skills = ['beginner', 'intermediate', 'advanced', 'expert']

    # Danh sách budget ranges
    valid_budget_ranges = ['low', 'medium', 'high']

    # Sửa chữa dữ liệu
    for idx, row in df.iterrows():
        # 1. Sửa gender data
        if pd.isna(row['gender']) or row['gender'] not in ['male', 'female', 'other']:
            # Dựa vào tên để đoán giới tính
            if any(word in str(row['full_name']).lower() for word in ['thị', 'nữ']):
                df.at[idx, 'gender'] = 'female'
            elif any(word in str(row['full_name']).lower() for word in ['văn', 'nam']):
                df.at[idx, 'gender'] = 'male'
            else:
                df.at[idx, 'gender'] = random.choice(['male', 'female'])

        # 2. Thêm tuổi nếu thiếu
        if pd.isna(row['age']) or row['age'] == '':
            age_group = row['age_group']
            if age_group == '18-24':
                df.at[idx, 'age'] = random.randint(18, 24)
            elif age_group == '25-34':
                df.at[idx, 'age'] = random.randint(25, 34)
            elif age_group == '35-44':
                df.at[idx, 'age'] = random.randint(35, 44)
            elif age_group == '45-54':
                df.at[idx, 'age'] = random.randint(45, 54)
            elif age_group == '55-64':
                df.at[idx, 'age'] = random.randint(55, 64)
            elif age_group == '65+':
                df.at[idx, 'age'] = random.randint(65, 80)
            else:
                df.at[idx, 'age'] = random.randint(25, 45)

        # 3. Tạo email và phone nếu thiếu
        if pd.isna(row['email']) or row['email'] == '':
            name_parts = str(row['full_name']).lower().replace(
                ' ', '').replace('thị', '').replace('văn', '')
            df.at[idx,
                  'email'] = f"{name_parts}{random.randint(100, 999)}@email.com"

        if pd.isna(row['phone']) or row['phone'] == '':
            df.at[idx, 'phone'] = f"09{random.randint(10000000, 99999999)}"

        # 4. Thêm health_goals
        if pd.isna(row['health_goals']) or row['health_goals'] == '':
            # Chọn 1-2 health goals ngẫu nhiên
            num_goals = random.choice([1, 2])
            selected_goals = random.sample(valid_health_goals, num_goals)
            df.at[idx, 'health_goals'] = ','.join(selected_goals)

        # 5. Thêm dietary_restrictions
        if pd.isna(row['dietary_restrictions']) or row['dietary_restrictions'] == '':
            # 70% không có hạn chế, 30% có hạn chế
            if random.random() < 0.3:
                num_restrictions = random.choice([1, 2])
                selected_restrictions = random.sample(
                    valid_dietary_restrictions, num_restrictions)
                # Đảm bảo không chọn cùng lúc vegetarian, vegan, và buddhist_vegetarian
                veg_options = ['vegetarian', 'vegan', 'buddhist_vegetarian']
                veg_in_selection = [
                    r for r in selected_restrictions if r in veg_options]
                if len(veg_in_selection) > 1:
                    selected_restrictions = [
                        r for r in selected_restrictions if r not in veg_options]
                    selected_restrictions.append(random.choice(veg_options))
                df.at[idx, 'dietary_restrictions'] = ','.join(
                    selected_restrictions)
            else:
                df.at[idx, 'dietary_restrictions'] = ''

        # 6. Thêm preferred_cuisines (luôn là vietnamese)
        df.at[idx, 'preferred_cuisines'] = 'vietnamese'

        # 7. Thêm regional_preferences
        if pd.isna(row.get('regional_preferences', '')) or row.get('regional_preferences', '') == '':
            # Dựa vào region để chọn regional preference
            region = str(row['region']).lower()
            if any(city in region for city in ['hà nội', 'hải phòng', 'hạ long', 'ninh bình']):
                regional_pref = 'northern'
            elif any(city in region for city in ['huế', 'đà nẵng', 'hội an', 'quảng nam']):
                regional_pref = 'central'
            elif any(city in region for city in ['tp.hcm', 'sài gòn', 'vũng tàu', 'cần thơ', 'đà lạt']):
                regional_pref = 'southern'
            else:
                regional_pref = random.choice(valid_regional_preferences)

            # Thêm cột regional_preferences nếu chưa có
            if 'regional_preferences' not in df.columns:
                df['regional_preferences'] = ''
            df.at[idx, 'regional_preferences'] = regional_pref

        # 8. Thêm preferred_meal_times
        if pd.isna(row['preferred_meal_times']) or row['preferred_meal_times'] == '':
            num_meals = random.choice([2, 3])
            selected_meals = random.sample(valid_meal_times, num_meals)
            df.at[idx, 'preferred_meal_times'] = ','.join(selected_meals)

        # 9. Thêm cooking_skill_level
        if pd.isna(row['cooking_skill_level']) or row['cooking_skill_level'] == '':
            df.at[idx, 'cooking_skill_level'] = random.choice(
                valid_cooking_skills)

        # 10. Thêm budget_range
        if pd.isna(row['budget_range']) or row['budget_range'] == '':
            df.at[idx, 'budget_range'] = random.choice(valid_budget_ranges)

        # 11. Thêm occupation nếu thiếu
        if pd.isna(row['occupation']) or row['occupation'] == '':
            occupations = ['Sinh viên', 'Nhân viên văn phòng', 'Giáo viên', 'Kế toán', 'Bán hàng',
                           'Y tá', 'Kỹ sư', 'Freelancer', 'Nội trợ', 'Hưu trí']
            df.at[idx, 'occupation'] = random.choice(occupations)

        # 12. Thêm location nếu thiếu
        if pd.isna(row['location']) or row['location'] == '':
            df.at[idx, 'location'] = row['region']

        # 13. Đảm bảo status
        if pd.isna(row['status']) or row['status'] == '':
            df.at[idx, 'status'] = 'active'

    # Thêm cột regional_preferences nếu chưa có
    if 'regional_preferences' not in df.columns:
        df['regional_preferences'] = ''
        for idx in range(len(df)):
            df.at[idx, 'regional_preferences'] = random.choice(
                valid_regional_preferences)

    # Lưu dữ liệu đã sửa
    df.to_csv('customers_data.csv', index=False, encoding='utf-8')

    print("✅ HOÀN THÀNH SỬA CHỮA DỮ LIỆU!")
    print(f"📊 Số lượng customer đã sửa: {len(df)}")
    print("🔍 Thống kê sau khi sửa:")

    # Thống kê
    print(f"  - Email: {df['email'].notna().sum()}/{len(df)}")
    print(f"  - Phone: {df['phone'].notna().sum()}/{len(df)}")
    print(f"  - Age: {df['age'].notna().sum()}/{len(df)}")
    print(f"  - Health goals: {df['health_goals'].notna().sum()}/{len(df)}")
    print(
        f"  - Dietary restrictions: {(df['dietary_restrictions'] != '').sum()}/{len(df)}")
    print(
        f"  - Regional preferences: {df['regional_preferences'].notna().sum()}/{len(df)}")

    return df


def validate_customer_data(df):
    """Kiểm tra tính nhất quán của dữ liệu"""
    print("\n🔍 KIỂM TRA TÍNH NHẤT QUÁN:")

    # Kiểm tra dietary restrictions
    valid_restrictions = ['vegetarian', 'vegan', 'buddhist_vegetarian', 'no_seafood',
                          'no_pork', 'no_beef', 'low_sodium', 'diabetic', 'no_spicy', 'light_meals']

    invalid_count = 0
    for idx, row in df.iterrows():
        if pd.notna(row['dietary_restrictions']) and row['dietary_restrictions'] != '':
            restrictions = [r.strip() for r in str(
                row['dietary_restrictions']).split(',')]
            invalid_restrictions = [
                r for r in restrictions if r not in valid_restrictions]
            if invalid_restrictions:
                print(
                    f"  ⚠️ Customer {row['customer_id']}: Invalid restrictions {invalid_restrictions}")
                invalid_count += 1

    if invalid_count == 0:
        print("  ✅ Tất cả dietary restrictions hợp lệ")

    # Kiểm tra vegetarian conflicts
    conflict_count = 0
    for idx, row in df.iterrows():
        if pd.notna(row['dietary_restrictions']) and row['dietary_restrictions'] != '':
            restrictions = [r.strip() for r in str(
                row['dietary_restrictions']).split(',')]
            veg_options = [r for r in restrictions if r in [
                'vegetarian', 'vegan', 'buddhist_vegetarian']]
            if len(veg_options) > 1:
                print(
                    f"  ⚠️ Customer {row['customer_id']}: Multiple vegetarian options {veg_options}")
                conflict_count += 1

    if conflict_count == 0:
        print("  ✅ Không có xung đột vegetarian options")

    print(f"📈 Dữ liệu đã được chuẩn hóa và nhất quán!")


if __name__ == "__main__":
    # Sửa chữa dữ liệu
    df = fix_customer_data()

    # Kiểm tra tính nhất quán
    validate_customer_data(df)

    print("\n🎉 HOÀN THÀNH TẤT CẢ!")
