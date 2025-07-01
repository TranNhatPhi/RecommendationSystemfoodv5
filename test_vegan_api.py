#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import json


def test_vegan_customer():
    print("🧪 Testing VEGAN customer API...")

    # Test data for VEGAN customer
    test_data = {
        "full_name": "Nguyen Thi Vegan Test",
        "email": "vegan@email.com",
        "phone": "987654321",
        "age": 30,
        "gender": "female",
        "health_goals": ["healthy_eating"],
        # ✅ THUẦN CHAY - KHÔNG THỊT, HẢI SẢN, SỮA, TRỨNG
        "dietary_restrictions": ["vegan"],
        "preferred_cuisines": ["vietnamese"],
        "preferred_meal_times": ["lunch", "dinner"],
        "cooking_skill_level": "beginner",
        "budget_range": "medium",
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
                is_vegan = food_info.get('is_vegan', False)
                contains_meat = food_info.get('contains_meat', False)
                contains_seafood = food_info.get('contains_seafood', False)
                contains_dairy = food_info.get('contains_dairy', False)
                contains_eggs = food_info.get('contains_eggs', False)

                status = "✅ OK"
                issues = []
                if contains_meat:
                    issues.append("thịt")
                if contains_seafood:
                    issues.append("hải sản")
                if contains_dairy:
                    issues.append("sữa")
                if contains_eggs:
                    issues.append("trứng")

                if issues:
                    status = f"❌ VI PHẠM ({', '.join(issues)})"
                    violations += 1

                print(f"{i+1}. {recipe_name} - {status}")
                print(f"   - Vegan: {is_vegan}")
                if issues:
                    print(f"   ⚠️ Chứa: {', '.join(issues)}")

            if violations == 0:
                print(
                    f"\n✅ HOÀN HẢO: Tất cả {len(recommendations)} món đều phù hợp với VEGAN!")
            else:
                print(
                    f"\n❌ VẤN ĐỀ: {violations}/{len(recommendations)} món vi phạm dietary restrictions!")

        else:
            print(f"❌ API failed: {result}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_vegan_customer()
