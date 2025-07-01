#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import json

print("🔍 Kiểm tra dữ liệu khách hàng và dietary restrictions...")

# Đọc dữ liệu khách hàng
try:
    df = pd.read_csv('customers_data.csv', encoding='utf-8')
    print(f"✅ Đọc được {len(df)} khách hàng")
except:
    try:
        df = pd.read_csv('customers_data.csv', encoding='latin-1')
        print(f"✅ Đọc được {len(df)} khách hàng (latin-1)")
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")
        exit()

# Kiểm tra dietary restrictions
print("\n📊 Thống kê dietary restrictions:")
restrictions_counts = df['dietary_restrictions'].value_counts()
print(restrictions_counts.head(10))

# Tìm khách hàng vegetarian
vegetarian_customers = df[df['dietary_restrictions'].str.contains(
    'vegetarian', na=False)]
print(f"\n🥬 Số khách hàng ăn chay: {len(vegetarian_customers)}")

if len(vegetarian_customers) > 0:
    print("\nVí dụ khách hàng ăn chay:")
    for i, row in vegetarian_customers.head(3).iterrows():
        print(
            f"- {row['customer_id']}: {row['full_name']} - {row['dietary_restrictions']}")

# Tìm khách hàng vegan
vegan_customers = df[df['dietary_restrictions'].str.contains(
    'vegan', na=False)]
print(f"\n🌱 Số khách hàng ăn thuần chay: {len(vegan_customers)}")

# Kiểm tra customer từ URL (CUS20250629094939)
test_customer_id = "CUS20250629094939"
test_customer = df[df['customer_id'] == test_customer_id]
if len(test_customer) > 0:
    customer = test_customer.iloc[0]
    print(f"\n👤 Thông tin khách hàng {test_customer_id}:")
    print(f"  - Tên: {customer['full_name']}")
    print(f"  - Dietary restrictions: {customer['dietary_restrictions']}")
    print(f"  - Health goals: {customer['health_goals']}")
else:
    print(f"\n❌ Không tìm thấy khách hàng {test_customer_id}")

# Kiểm tra food classification
print("\n🍽️ Kiểm tra food classification...")
try:
    with open('food_classification.json', 'r', encoding='utf-8') as f:
        food_data = json.load(f)

    vegetarian_foods = []
    vegan_foods = []
    total_foods = len(food_data)

    for food_name, info in food_data.items():
        if info.get('is_vegetarian', False):
            vegetarian_foods.append(food_name)
        if info.get('is_vegan', False):
            vegan_foods.append(food_name)

    print(f"✅ Tổng số món ăn: {total_foods}")
    print(f"🥬 Món ăn chay: {len(vegetarian_foods)}")
    print(f"🌱 Món ăn thuần chay: {len(vegan_foods)}")

    if len(vegetarian_foods) > 0:
        print("\nVí dụ món ăn chay:")
        for food in vegetarian_foods[:3]:
            print(f"- {food}")

except Exception as e:
    print(f"❌ Lỗi đọc food classification: {e}")

print("\n✅ Hoàn thành kiểm tra!")
