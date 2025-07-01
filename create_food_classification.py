#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để tạo database phân loại món ăn theo dietary restrictions
Giúp hệ thống recommendation filter chính xác hơn
"""

import pandas as pd
import json


def create_food_classification():
    """Tạo database phân loại món ăn"""

    print("🍽️ TẠO DATABASE PHÂN LOẠI MÓN ĂN")
    print("=" * 40)

    # Đọc dữ liệu interactions để lấy danh sách món ăn
    interactions_df = pd.read_csv(
        'interactions_enhanced_final.csv', encoding='utf-8')
    unique_foods = interactions_df['recipe_name'].unique()

    print(f"📊 Tổng số món ăn: {len(unique_foods)}")

    # Tạo classification database
    food_classification = {}

    # Định nghĩa keywords để phân loại
    meat_keywords = [
        'thịt', 'heo', 'bò', 'gà', 'vịt', 'sườn', 'nem', 'chả', 'lạp xưởng',
        'xúc xích', 'thịt nướng', 'thịt kho', 'thịt xào', 'gà luộc', 'gà nướng',
        'bò nướng', 'bò kho', 'heo quay', 'chả cá', 'thăn', 'ba chỉ'
    ]

    seafood_keywords = [
        'tôm', 'cua', 'cá', 'mực', 'nghêu', 'sò', 'ốc', 'hàu', 'tép',
        'chả cá', 'cá nướng', 'cá kho', 'tôm nướng', 'cua rang', 'mực xào',
        'hải sản', 'cá thu', 'cá ngừ', 'cá hồi'
    ]

    dairy_keywords = [
        'sữa', 'kem', 'phô mai', 'bơ', 'yaourt', 'sữa chua', 'cheese',
        'cream', 'milk', 'yogurt'
    ]

    egg_keywords = [
        'trứng', 'trứng gà', 'trứng vịt', 'trứng cút', 'ốp la', 'trứng chiên',
        'trứng luộc', 'bánh flan'
    ]

    spicy_keywords = [
        'cay', 'ớt', 'tiêu', 'tắc', 'kim chi', 'chua cay', 'cay nồng',
        'ớt hiểm', 'bún bò huế', 'mì quảng'
    ]

    sweet_keywords = [
        'bánh ngọt', 'kẹo', 'đường', 'mật ong', 'bánh kem', 'chocolate',
        'bánh quy ngọt', 'bánh su kem', 'bánh flan', 'chè', 'kem'
    ]

    # Các món ăn chay được xác định tích cực
    vegetarian_positive = [
        'chè', 'bánh chưng chay', 'nem chay', 'phở chay', 'bún chay',
        'cơm chay', 'canh chua chay', 'đậu phụ', 'măng', 'nấm',
        'rau muống', 'cải thảo', 'súp lơ', 'cà rót', 'đậu que'
    ]

    # Phân loại từng món ăn
    for food in unique_foods:
        food_lower = food.lower()

        classification = {
            'name': food,
            'is_vegetarian': True,  # Mặc định là chay
            'is_vegan': True,
            'is_buddhist_vegetarian': True,
            'contains_meat': False,
            'contains_seafood': False,
            'contains_dairy': False,
            'contains_eggs': False,
            'is_spicy': False,
            'is_sweet': False,
            'dietary_tags': []
        }

        # Kiểm tra thịt
        if any(keyword in food_lower for keyword in meat_keywords):
            classification['contains_meat'] = True
            classification['is_vegetarian'] = False
            classification['is_vegan'] = False
            classification['is_buddhist_vegetarian'] = False
            classification['dietary_tags'].append('contains_meat')

        # Kiểm tra hải sản
        if any(keyword in food_lower for keyword in seafood_keywords):
            classification['contains_seafood'] = True
            classification['is_vegetarian'] = False
            classification['is_vegan'] = False
            classification['is_buddhist_vegetarian'] = False
            classification['dietary_tags'].append('contains_seafood')

        # Kiểm tra sữa
        if any(keyword in food_lower for keyword in dairy_keywords):
            classification['contains_dairy'] = True
            classification['is_vegan'] = False
            classification['dietary_tags'].append('contains_dairy')

        # Kiểm tra trứng
        if any(keyword in food_lower for keyword in egg_keywords):
            classification['contains_eggs'] = True
            classification['is_vegan'] = False
            classification['dietary_tags'].append('contains_eggs')

        # Kiểm tra cay
        if any(keyword in food_lower for keyword in spicy_keywords):
            classification['is_spicy'] = True
            classification['dietary_tags'].append('spicy')

        # Kiểm tra ngọt
        if any(keyword in food_lower for keyword in sweet_keywords):
            classification['is_sweet'] = True
            classification['dietary_tags'].append('sweet')

        # Kiểm tra hành tỏi (cấm trong chay Phật giáo)
        if any(keyword in food_lower for keyword in ['hành', 'tỏi', 'kiệu', 'răm']):
            classification['is_buddhist_vegetarian'] = False
            classification['dietary_tags'].append('contains_pungent')

        # Thêm vào database
        food_classification[food] = classification

    # Thống kê
    vegetarian_count = sum(
        1 for f in food_classification.values() if f['is_vegetarian'])
    vegan_count = sum(1 for f in food_classification.values() if f['is_vegan'])
    buddhist_veg_count = sum(
        1 for f in food_classification.values() if f['is_buddhist_vegetarian'])
    meat_count = sum(1 for f in food_classification.values()
                     if f['contains_meat'])
    seafood_count = sum(
        1 for f in food_classification.values() if f['contains_seafood'])

    print(f"\n📊 THỐNG KÊ PHÂN LOẠI:")
    print(
        f"  🥬 Vegetarian: {vegetarian_count}/{len(unique_foods)} ({vegetarian_count/len(unique_foods)*100:.1f}%)")
    print(
        f"  🌱 Vegan: {vegan_count}/{len(unique_foods)} ({vegan_count/len(unique_foods)*100:.1f}%)")
    print(
        f"  🧘 Buddhist Vegetarian: {buddhist_veg_count}/{len(unique_foods)} ({buddhist_veg_count/len(unique_foods)*100:.1f}%)")
    print(
        f"  🥩 Contains Meat: {meat_count}/{len(unique_foods)} ({meat_count/len(unique_foods)*100:.1f}%)")
    print(
        f"  🐟 Contains Seafood: {seafood_count}/{len(unique_foods)} ({seafood_count/len(unique_foods)*100:.1f}%)")

    # Lưu database
    with open('food_classification.json', 'w', encoding='utf-8') as f:
        json.dump(food_classification, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Đã lưu database: food_classification.json")

    # Tạo danh sách món chay
    vegetarian_foods = [
        name for name, data in food_classification.items() if data['is_vegetarian']]
    vegan_foods = [name for name,
                   data in food_classification.items() if data['is_vegan']]
    buddhist_foods = [name for name, data in food_classification.items(
    ) if data['is_buddhist_vegetarian']]

    print(f"\n🥬 CÁC MÓN CHAY (Top 10):")
    for i, food in enumerate(vegetarian_foods[:10], 1):
        print(f"  {i:2d}. {food}")

    print(f"\n🌱 CÁC MÓN THUẦN CHAY (Top 10):")
    for i, food in enumerate(vegan_foods[:10], 1):
        print(f"  {i:2d}. {food}")

    return food_classification


def create_recommendation_filter():
    """Tạo helper function để filter recommendations"""

    filter_code = '''
def filter_by_dietary_restrictions(df, dietary_restrictions):
    """Filter dataframe based on dietary restrictions using classification database"""
    import json
    
    try:
        with open('food_classification.json', 'r', encoding='utf-8') as f:
            food_db = json.load(f)
    except FileNotFoundError:
        print("⚠️ Food classification database not found!")
        return df
    
    if not dietary_restrictions:
        return df
    
    filtered_df = df.copy()
    
    for restriction in dietary_restrictions:
        if restriction == 'vegetarian':
            # Chỉ giữ lại món chay
            vegetarian_foods = [name for name, data in food_db.items() if data['is_vegetarian']]
            filtered_df = filtered_df[filtered_df['recipe_name'].isin(vegetarian_foods)]
            
        elif restriction == 'vegan':
            # Chỉ giữ lại món thuần chay
            vegan_foods = [name for name, data in food_db.items() if data['is_vegan']]
            filtered_df = filtered_df[filtered_df['recipe_name'].isin(vegan_foods)]
            
        elif restriction == 'buddhist_vegetarian':
            # Chỉ giữ lại món chay Phật giáo
            buddhist_foods = [name for name, data in food_db.items() if data['is_buddhist_vegetarian']]
            filtered_df = filtered_df[filtered_df['recipe_name'].isin(buddhist_foods)]
            
        elif restriction == 'no_seafood':
            # Loại bỏ món có hải sản
            seafood_foods = [name for name, data in food_db.items() if data['contains_seafood']]
            filtered_df = filtered_df[~filtered_df['recipe_name'].isin(seafood_foods)]
            
        elif restriction == 'no_pork':
            # Loại bỏ món có thịt heo
            pork_foods = [name for name, data in food_db.items() 
                         if any('heo' in tag for tag in data.get('dietary_tags', []))]
            filtered_df = filtered_df[~filtered_df['recipe_name'].isin(pork_foods)]
            
        elif restriction == 'no_beef':
            # Loại bỏ món có thịt bò
            beef_foods = [name for name, data in food_db.items() 
                         if any('bò' in tag for tag in data.get('dietary_tags', []))]
            filtered_df = filtered_df[~filtered_df['recipe_name'].isin(beef_foods)]
            
        elif restriction == 'no_spicy':
            # Loại bỏ món cay
            spicy_foods = [name for name, data in food_db.items() if data['is_spicy']]
            filtered_df = filtered_df[~filtered_df['recipe_name'].isin(spicy_foods)]
            
        elif restriction == 'diabetic':
            # Loại bỏ món ngọt
            sweet_foods = [name for name, data in food_db.items() if data['is_sweet']]
            filtered_df = filtered_df[~filtered_df['recipe_name'].isin(sweet_foods)]
    
    return filtered_df
'''

    with open('dietary_filter_helper.py', 'w', encoding='utf-8') as f:
        f.write(filter_code)

    print(f"💾 Đã tạo helper function: dietary_filter_helper.py")


if __name__ == "__main__":
    # Tạo database phân loại
    food_db = create_food_classification()

    # Tạo helper function
    create_recommendation_filter()

    print(f"\n🎉 HOÀN THÀNH! Database và helper functions đã sẵn sàng.")
