#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import json


def test_api():
    print("🧪 Testing vegetarian customer API...")

    # Test data
    test_data = {
        "full_name": "Le Van Thao Test",
        "email": "test@email.com",
        "phone": "956729234",
        "age": 76,
        "gender": "male",
        "health_goals": ["muscle_gain", "healthy_eating"],
        "dietary_restrictions": ["no_seafood", "vegetarian"],
        "preferred_cuisines": ["vietnamese"],
        "preferred_meal_times": ["snack", "lunch", "dinner"],
        "cooking_skill_level": "advanced",
        "budget_range": "high",
        "generate_fresh": True,
        "randomize": True
    }

    print(f"📤 Dietary restrictions: {test_data['dietary_restrictions']}")

    try:
        # Convert to JSON
        json_data = json.dumps(test_data).encode('utf-8')

        # Create request
        req = urllib.request.Request(
            'http://127.0.0.1:5000/api/register-customer',
            data=json_data,
            headers={'Content-Type': 'application/json'}
        )

        # Send request
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))

        if result.get('success'):
            recommendations = result.get('recommendations', [])
            print(f"\n🍽️ Nhận được {len(recommendations)} recommendations:")

            # Load food classification
            with open('food_classification.json', 'r', encoding='utf-8') as f:
                food_data = json.load(f)

            violations = 0
            for i, rec in enumerate(recommendations[:10]):
                recipe_name = rec['recipe_name']
                food_info = food_data.get(recipe_name, {})
                is_vegetarian = food_info.get('is_vegetarian', False)
                contains_meat = food_info.get('contains_meat', False)
                contains_seafood = food_info.get('contains_seafood', False)

                status = "✅ OK"
                if contains_meat or contains_seafood:
                    status = "❌ VI PHẠM"
                    violations += 1

                print(f"{i+1}. {recipe_name} - {status}")
                if contains_meat:
                    print(f"   ⚠️ Chứa thịt!")
                if contains_seafood:
                    print(f"   ⚠️ Chứa hải sản!")

            if violations == 0:
                print(
                    f"\n✅ HOÀN HẢO: Tất cả {len(recommendations)} món đều phù hợp với ăn chay!")
            else:
                print(
                    f"\n❌ VẤN ĐỀ: {violations}/{len(recommendations)} món vi phạm dietary restrictions!")

        else:
            print(f"❌ API failed: {result}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_api()
