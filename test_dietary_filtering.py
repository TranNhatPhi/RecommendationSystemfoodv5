#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để kiểm tra dietary restrictions filtering
"""

import requests
import json


def test_vegetarian_recommendation():
    """Test recommendation cho người ăn chay"""

    print("🧪 TESTING VEGETARIAN RECOMMENDATION")
    print("=" * 50)

    # Tạo customer data với dietary restriction là vegetarian
    customer_data = {
        "full_name": "Trần Nhật Phi (Test)",
        "email": "test.vegetarian@email.com",
        "phone": "0987654321",
        "age": 25,
        "gender": "male",
        "location": "TP.HCM",
        "occupation": "Tester",
        "health_goals": ["weight_loss"],
        "dietary_restrictions": ["vegetarian"],  # ✅ ĂN CHAY
        "regional_preferences": ["southern"],
        "preferred_meal_times": ["lunch", "dinner"],
        "cooking_skill_level": "beginner",
        "budget_range": "medium"
    }

    try:
        # Gửi request đến API
        response = requests.post(
            'http://localhost:5000/api/register-customer',
            json=customer_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Registration successful!")
            print(f"🆔 Customer ID: {result.get('customer_id')}")

            # Kiểm tra recommendations
            recommendations = result.get('recommendations', [])
            print(f"\n🍽️ RECOMMENDATIONS ({len(recommendations)} items):")

            # Check xem có món thịt không
            meat_keywords = ['thịt', 'heo', 'bò',
                             'gà', 'tôm', 'cua', 'cá', 'sườn']

            vegetarian_count = 0
            non_vegetarian_count = 0

            for i, rec in enumerate(recommendations[:10], 1):
                recipe_name = rec.get('recipe_name', 'Unknown')
                rating = rec.get('avg_rating', 0)

                # Check if contains meat
                contains_meat = any(keyword in recipe_name.lower()
                                    for keyword in meat_keywords)

                if contains_meat:
                    status = "❌ NON-VEGETARIAN"
                    non_vegetarian_count += 1
                else:
                    status = "✅ VEGETARIAN"
                    vegetarian_count += 1

                print(f"  {i:2d}. {recipe_name} (⭐{rating:.1f}) - {status}")

            print(f"\n📊 SUMMARY:")
            print(f"  ✅ Vegetarian dishes: {vegetarian_count}")
            print(f"  ❌ Non-vegetarian dishes: {non_vegetarian_count}")

            if non_vegetarian_count > 0:
                print(f"  🚨 ERROR: Hệ thống vẫn gợi ý món không chay!")
                return False
            else:
                print(f"  🎉 SUCCESS: Tất cả gợi ý đều phù hợp với ăn chay!")
                return True

        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_vegan_recommendation():
    """Test recommendation cho người ăn thuần chay"""

    print("\n🧪 TESTING VEGAN RECOMMENDATION")
    print("=" * 50)

    customer_data = {
        "full_name": "Nguyễn Vegan Test",
        "email": "test.vegan@email.com",
        "phone": "0987654322",
        "age": 30,
        "gender": "female",
        "health_goals": ["healthy_eating"],
        "dietary_restrictions": ["vegan"],  # ✅ THUẦN CHAY
        "preferred_meal_times": ["breakfast", "lunch"],
        "cooking_skill_level": "intermediate",
        "budget_range": "medium"
    }

    try:
        response = requests.post(
            'http://localhost:5000/api/register-customer',
            json=customer_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            result = response.json()
            recommendations = result.get('recommendations', [])

            print(f"🍽️ VEGAN RECOMMENDATIONS ({len(recommendations)} items):")

            # Check for animal products
            animal_keywords = ['thịt', 'heo', 'bò', 'gà',
                               'tôm', 'cua', 'cá', 'trứng', 'sữa', 'kem']

            vegan_count = 0
            non_vegan_count = 0

            for i, rec in enumerate(recommendations[:10], 1):
                recipe_name = rec.get('recipe_name', 'Unknown')
                rating = rec.get('avg_rating', 0)

                contains_animal = any(keyword in recipe_name.lower()
                                      for keyword in animal_keywords)

                if contains_animal:
                    status = "❌ NON-VEGAN"
                    non_vegan_count += 1
                else:
                    status = "✅ VEGAN"
                    vegan_count += 1

                print(f"  {i:2d}. {recipe_name} (⭐{rating:.1f}) - {status}")

            print(f"\n📊 VEGAN SUMMARY:")
            print(f"  ✅ Vegan dishes: {vegan_count}")
            print(f"  ❌ Non-vegan dishes: {non_vegan_count}")

            return non_vegan_count == 0

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    print("🧪 DIETARY RESTRICTIONS FILTERING TEST")
    print("=" * 60)

    # Test vegetarian
    vegetarian_success = test_vegetarian_recommendation()

    # Test vegan
    vegan_success = test_vegan_recommendation()

    print(f"\n🏁 FINAL RESULTS:")
    print(
        f"  Vegetarian filtering: {'✅ PASS' if vegetarian_success else '❌ FAIL'}")
    print(f"  Vegan filtering: {'✅ PASS' if vegan_success else '❌ FAIL'}")

    if vegetarian_success and vegan_success:
        print(f"\n🎉 ALL TESTS PASSED! Dietary restrictions filtering hoạt động chính xác!")
    else:
        print(f"\n🚨 SOME TESTS FAILED! Cần điều chỉnh thêm logic filtering.")
