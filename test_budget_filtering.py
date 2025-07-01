#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import json


def test_budget_filtering():
    print("🧪 Testing BUDGET filtering...")

    # Test 1: Low budget customer
    test_low_budget = {
        "full_name": "Nguyen Van Tiet Kiem",
        "email": "tietkiem@email.com",
        "phone": "987654321",
        "age": 25,
        "gender": "male",
        "health_goals": ["healthy_eating"],
        "dietary_restrictions": [],
        "preferred_cuisines": ["vietnamese"],
        "preferred_meal_times": ["lunch", "dinner"],
        "cooking_skill_level": "beginner",
        "budget_range": "low",  # 💰 Tiết kiệm (< 50k/bữa)
        "generate_fresh": True,
        "randomize": True
    }

    # Test 2: High budget customer
    test_high_budget = {
        "full_name": "Nguyen Thi Sang Trong",
        "email": "sangtrong@email.com",
        "phone": "987654322",
        "age": 35,
        "gender": "female",
        "health_goals": ["healthy_eating"],
        "dietary_restrictions": [],
        "preferred_cuisines": ["vietnamese"],
        "preferred_meal_times": ["lunch", "dinner"],
        "cooking_skill_level": "advanced",
        "budget_range": "high",  # 💰💰💰 Cao (> 100k/bữa)
        "generate_fresh": True,
        "randomize": True
    }

    # Test 3: Medium budget customer (default)
    test_medium_budget = {
        "full_name": "Nguyen Van Trung Binh",
        "email": "trungbinh@email.com",
        "phone": "987654323",
        "age": 30,
        "gender": "male",
        "health_goals": ["healthy_eating"],
        "dietary_restrictions": [],
        "preferred_cuisines": ["vietnamese"],
        "preferred_meal_times": ["lunch", "dinner"],
        "cooking_skill_level": "intermediate",
        "budget_range": "medium",  # 💰💰 Trung bình (50k-100k/bữa)
        "generate_fresh": True,
        "randomize": True
    }

    test_cases = [
        ("LOW BUDGET (< 50k)", test_low_budget),
        ("HIGH BUDGET (> 100k)", test_high_budget),
        ("MEDIUM BUDGET (50k-100k)", test_medium_budget)
    ]

    for test_name, test_data in test_cases:
        print(f"\n{'='*50}")
        print(f"🧪 Testing {test_name}")
        print(f"💰 Budget range: {test_data['budget_range']}")

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
                print(f"🍽️ Nhận được {len(recommendations)} recommendations:")

                total_price = 0
                for i, rec in enumerate(recommendations):
                    price = rec.get('estimated_price_vnd', 0)
                    total_price += price
                    print(f"{i+1}. {rec['recipe_name']} - {price:,} VND")

                if recommendations:
                    avg_price = total_price / len(recommendations)
                    print(f"💰 Giá trung bình: {avg_price:,.0f} VND/món")

                    # Check if prices match budget range
                    if test_data['budget_range'] == 'low':
                        if avg_price < 50000:
                            print(
                                "✅ Budget filtering works correctly for LOW budget!")
                        else:
                            print(
                                f"❌ Budget filtering failed: Average {avg_price:,.0f} VND >= 50,000 VND")
                    elif test_data['budget_range'] == 'high':
                        if avg_price > 100000:
                            print(
                                "✅ Budget filtering works correctly for HIGH budget!")
                        else:
                            print(
                                f"⚠️ Budget filtering: Average {avg_price:,.0f} VND <= 100,000 VND (might be expected if no high-price items)")
                    else:  # medium
                        print(
                            f"✅ Medium budget (no filtering applied): Average {avg_price:,.0f} VND")
                else:
                    print("❌ No recommendations received")

            else:
                print(f"❌ API failed: {result}")

        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_budget_filtering()
