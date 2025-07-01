#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import pandas as pd


def test_vegetarian_customer():
    print("🧪 Testing dietary restrictions filtering...")

    # Test với khách hàng vegetarian CUS00006
    customer_id = 'CUS00006'

    # Đọc thông tin khách hàng từ CSV
    df = pd.read_csv('customers_data.csv', encoding='utf-8')
    customer_row = df[df['customer_id'] == customer_id]

    if len(customer_row) == 0:
        print(f"❌ Customer {customer_id} not found")
        return

    customer = customer_row.iloc[0]
    print(f"✅ Testing customer: {customer['full_name']}")
    print(f"✅ Dietary restrictions: {customer['dietary_restrictions']}")

    # Chuẩn bị data để test API
    dietary_restrictions = customer['dietary_restrictions'].split(
        ',') if customer['dietary_restrictions'] else []

    reg_data = {
        'full_name': customer['full_name'],
        'email': customer['email'],
        'phone': customer['phone'],
        'age': int(customer['age']) if pd.notna(customer['age']) else 25,
        'gender': customer['gender'],
        'health_goals': customer['health_goals'].split(',') if customer['health_goals'] else [],
        'dietary_restrictions': dietary_restrictions,
        'preferred_cuisines': customer['preferred_cuisines'].split(',') if customer['preferred_cuisines'] else ['vietnamese'],
        'preferred_meal_times': customer['preferred_meal_times'].split(',') if customer['preferred_meal_times'] else ['lunch'],
        'cooking_skill_level': customer['cooking_skill_level'] or 'beginner',
        'budget_range': customer['budget_range'] or 'medium',
        'generate_fresh': True,
        'randomize': True
    }

    print(f"\n📤 Dietary restrictions being sent: {dietary_restrictions}")

    try:
        # Test API register-customer
        response = requests.post('http://127.0.0.1:5000/api/register-customer',
                                 json=reg_data,
                                 timeout=30)

        if response.status_code == 200:
            result = response.json()
            if result.get('success') and 'recommendations' in result:
                recommendations = result['recommendations']
                print(
                    f"\n🍽️ Nhận được {len(recommendations)} recommendations:")

                # Load food classification để kiểm tra
                with open('food_classification.json', 'r', encoding='utf-8') as f:
                    food_data = json.load(f)

                print("\n🔍 Kiểm tra từng món ăn:")
                for i, rec in enumerate(recommendations[:10]):
                    recipe_name = rec['recipe_name']
                    food_info = food_data.get(recipe_name, {})
                    is_vegetarian = food_info.get('is_vegetarian', False)
                    contains_meat = food_info.get('contains_meat', False)
                    contains_seafood = food_info.get('contains_seafood', False)

                    print(f"{i+1}. {recipe_name}")
                    print(f"   - Vegetarian: {is_vegetarian}")
                    print(f"   - Contains meat: {contains_meat}")
                    print(f"   - Contains seafood: {contains_seafood}")

                    # Kiểm tra xem có vi phạm dietary restrictions không
                    if 'vegetarian' in dietary_restrictions:
                        if contains_meat or contains_seafood:
                            print(
                                f"   ❌ VI PHẠM: Khách hàng vegetarian nhưng món có thịt/hải sản!")
                        else:
                            print(f"   ✅ OK: Phù hợp với vegetarian")
                    print()

            else:
                print("❌ No recommendations in response")
                print(f"Response: {result}")
        else:
            print(f"❌ API failed: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_vegetarian_customer()
