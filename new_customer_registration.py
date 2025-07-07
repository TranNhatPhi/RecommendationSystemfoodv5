"""
🆕 NEW CUSTOMER REGISTRATION SYSTEM
==================================

Flask routes for handling new customer registration with immediate recommendations.

Author: AI Assistant  
Date: June 19, 2025
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import uuid
import re

# Import hybrid recommendation system
try:
    from hybrid_integration import get_hybrid_service
    HYBRID_AVAILABLE = True
except ImportError:
    HYBRID_AVAILABLE = False
    print("⚠️ Hybrid system not available")


# def validate_dietary_restrictions(dietary_restrictions):
#     """Validate dietary restrictions to ensure they match form options"""
#     if not dietary_restrictions:
#         return []

#     valid_restrictions = [
#         'vegetarian',           # Ăn chay
#         'vegan',               # Thuần chay
#         'buddhist_vegetarian',  # Chay Phật giáo
#         'no_seafood',          # Không hải sản
#         'no_pork',             # Không thịt heo
#         'no_beef',             # Không thịt bò
#         'low_sodium',          # Ít muối/mặn
#         'diabetic',            # Tiểu đường (ít đường)
#         'no_spicy',            # Không ăn cay
#         'light_meals'          # Thích món nhẹ
#     ]

#     # Ensure only valid restrictions
#     validated = [r for r in dietary_restrictions if r in valid_restrictions]

#     # Ensure only one vegetarian type is selected
#     veg_options = ['vegetarian', 'vegan', 'buddhist_vegetarian']
#     veg_selected = [r for r in validated if r in veg_options]

#     if len(veg_selected) > 1:
#         # Keep only the first vegetarian option
#         first_veg = veg_selected[0]
#         validated = [r for r in validated if r not in veg_options]
#         validated.append(first_veg)

#     return validated


def validate_regional_preferences(regional_preferences):
    """Validate regional preferences for Vietnamese cuisine"""
    if not regional_preferences:
        return []

    valid_regions = ['northern', 'central', 'southern', 'all_regions']
    return [r for r in regional_preferences if r in valid_regions]


def validate_health_goals(health_goals):
    """Validate health goals"""
    if not health_goals:
        return []

    valid_goals = ['weight_loss', 'muscle_gain',
                   'healthy_eating', 'maintain_weight']
    return [g for g in health_goals if g in valid_goals]


def validate_meal_times(meal_times):
    """Validate preferred meal times"""
    if not meal_times:
        return []

    valid_times = ['breakfast', 'lunch', 'dinner', 'snack']
    return [t for t in meal_times if t in valid_times]


def validate_customer_data(data):
    """Validate customer registration data"""
    errors = []

    # Required fields
    required_fields = ['full_name', 'email', 'phone', 'age', 'gender']
    for field in required_fields:
        if not data.get(field) or str(data[field]).strip() == '':
            errors.append(f'{field} là bắt buộc')

    # Email validation
    email = str(data.get('email', '')).strip()
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if email and not re.match(email_pattern, email):
        errors.append('Email không hợp lệ')

    # Phone validation
    phone = str(data.get('phone', '')).strip()
    if phone and not re.match(r'^[0-9]{10,11}$', phone):
        errors.append('Số điện thoại phải có 10-11 chữ số')

    # Age validation
    try:
        age = int(data.get('age', 0))
        if age < 13 or age > 120:
            errors.append('Tuổi phải từ 13-120')
    except (ValueError, TypeError):
        errors.append('Tuổi phải là số')

    return errors


def generate_customer_id():
    """Generate unique customer ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = str(uuid.uuid4())[-6:]
    return f"CUS{timestamp}{random_part.upper()}"


def save_customer_to_csv(customer_data, filename='customers_data.csv'):
    """Save customer data to CSV file"""
    try:
        # Load existing data or create new DataFrame
        if os.path.exists(filename):
            df = pd.read_csv(filename)
        else:
            df = pd.DataFrame()

        # Add new customer
        new_row = pd.DataFrame([customer_data])
        df = pd.concat([df, new_row], ignore_index=True)

        # Save to CSV
        df.to_csv(filename, index=False, encoding='utf-8')
        return True

    except Exception as e:
        print(f"Error saving customer: {e}")
        return False


def get_initial_recommendations(customer_data, randomize=False):
    """Get initial recommendations for new customer based on profile"""
    try:
        # Load interactions data to find similar customers
        interactions_df = pd.read_csv('interactions_enhanced_final.csv')

        recommendations = []        # Basic demographic-based recommendations
        age = int(customer_data.get('age', 25))
        gender = customer_data.get('gender', '')
        health_goals = customer_data.get('health_goals', [])
        dietary_restrictions = customer_data.get('dietary_restrictions', [])
        preferred_meal_times = customer_data.get('preferred_meal_times', [])
        budget_range = customer_data.get('budget_range', 'medium')

        # Ensure lists are properly formatted
        if isinstance(health_goals, str):
            health_goals = health_goals.split(',') if health_goals else []
        if isinstance(dietary_restrictions, str):
            dietary_restrictions = dietary_restrictions.split(
                ',') if dietary_restrictions else []
        if isinstance(preferred_meal_times, str):
            preferred_meal_times = preferred_meal_times.split(
                ',') if preferred_meal_times else []

        # Filter based on preferences
        filtered_df = interactions_df.copy()

        print(f" Total recipes available: {len(filtered_df)}")

        # Filter by health goals (more flexible)
        health_filtered_df = filtered_df.copy()
        if health_goals and len(health_goals) > 0:
            if 'weight_loss' in health_goals:
                weight_loss_df = filtered_df[filtered_df['nutrition_category']
                                             == 'weight-loss']
                if len(weight_loss_df) > 0:
                    health_filtered_df = weight_loss_df
            elif 'muscle_gain' in health_goals:
                muscle_gain_df = filtered_df[filtered_df['nutrition_category']
                                             == 'blood-boost']
                if len(muscle_gain_df) > 0:
                    health_filtered_df = muscle_gain_df
            elif 'healthy_eating' in health_goals:
                healthy_df = filtered_df[filtered_df['nutrition_category'] == 'balanced']
                if len(healthy_df) > 0:
                    health_filtered_df = healthy_df

        print(
            f"📊 Recipes after health goals filtering: {len(health_filtered_df)}/{len(filtered_df)}")

        # Filter by meal times (more flexible)
        meal_filtered_df = health_filtered_df.copy()
        if preferred_meal_times and len(preferred_meal_times) > 0:
            meal_time_df = health_filtered_df[health_filtered_df['meal_time'].isin(
                preferred_meal_times)]
            if len(meal_time_df) > 0:
                meal_filtered_df = meal_time_df
            else:
                print(
                    f"⚠️ No recipes found for meal times {preferred_meal_times}, keeping all recipes")

        print(
            f"📊 Recipes after meal time filtering: {len(meal_filtered_df)}/{len(health_filtered_df)}")

        # Get top-rated recipes (more flexible rating requirement)
        recipe_ratings = meal_filtered_df.groupby('recipe_name').agg({
            'rating': 'mean',
            'customer_id': 'count'
        }).reset_index()

        recipe_ratings.columns = ['recipe_name', 'avg_rating', 'rating_count']

        # Try with minimum 3 ratings first, then fall back to lower requirements
        high_rated = recipe_ratings[recipe_ratings['rating_count'] >= 3]
        if len(high_rated) >= 5:
            recipe_ratings = high_rated
        else:
            # Fall back to recipes with at least 2 ratings
            medium_rated = recipe_ratings[recipe_ratings['rating_count'] >= 2]
            if len(medium_rated) >= 5:
                recipe_ratings = medium_rated
                print(
                    f"⚠️ Using recipes with 2+ ratings (found {len(medium_rated)})")
            else:
                # Fall back to any rated recipes
                any_rated = recipe_ratings[recipe_ratings['rating_count'] >= 1]
                if len(any_rated) >= 5:
                    recipe_ratings = any_rated
                    print(
                        f"⚠️ Using recipes with 1+ ratings (found {len(any_rated)})")
                else:
                    print(
                        f"⚠️ Using all available recipes (found {len(recipe_ratings)})")

        print(f"📊 Final recipes for recommendations: {len(recipe_ratings)}")

        # Apply budget filtering if specified
        budget_filtered_df = meal_filtered_df.copy()
        if budget_range and budget_range != 'medium':  # Apply filtering for low/high, keep medium as default
            print(f"💰 Filtering by budget: {budget_range}")

            if budget_range == 'low':
                # Low budget: < 50k/bữa
                budget_recipes = meal_filtered_df[meal_filtered_df['estimated_price_vnd'] < 50000]
            elif budget_range == 'high':
                # High budget: > 100k/bữa
                budget_recipes = meal_filtered_df[meal_filtered_df['estimated_price_vnd'] > 100000]
            else:
                budget_recipes = meal_filtered_df  # Default fallback

            if len(budget_recipes) > 0:
                budget_filtered_df = budget_recipes
                print(
                    f"💰 Budget filtering: {len(budget_filtered_df)}/{len(meal_filtered_df)} recipes remain")
            else:
                print(
                    f"⚠️ No recipes found for budget range {budget_range}, keeping all recipes")

        # Recalculate ratings based on budget-filtered data
        if budget_range and budget_range != 'medium':
            recipe_ratings = budget_filtered_df.groupby('recipe_name').agg({
                'rating': 'mean',
                'customer_id': 'count'
            }).reset_index()
            recipe_ratings.columns = [
                'recipe_name', 'avg_rating', 'rating_count']

        recipe_ratings = recipe_ratings.sort_values(
            'avg_rating', ascending=False)

        # Add randomization if requested
        if randomize:
            # Get top 20 recipes and randomize selection
            top_recipes = recipe_ratings.head(20)
            recipe_ratings = top_recipes.sample(frac=1).reset_index(drop=True)

        # Get top 5 recommendations
        final_filtered_df = budget_filtered_df if budget_range and budget_range != 'medium' else meal_filtered_df
        for _, row in recipe_ratings.head(5).iterrows():
            recipe_name = row['recipe_name']
            recipe_info = final_filtered_df[final_filtered_df['recipe_name']
                                            == recipe_name].iloc[0]

            recommendations.append({
                'recipe_name': recipe_name,
                'avg_rating': round(row['avg_rating'], 2),
                'rating_count': int(row['rating_count']),
                'nutrition_category': recipe_info.get('nutrition_category', 'balanced'),
                'estimated_calories': int(recipe_info.get('estimated_calories', 0)),
                'preparation_time_minutes': int(recipe_info.get('preparation_time_minutes', 0)),
                'difficulty': recipe_info.get('difficulty', 'Dễ'),
                'meal_time': recipe_info.get('meal_time', 'lunch'),
                'recipe_url': recipe_info.get('recipe_url', ''),
                'estimated_price_vnd': int(recipe_info.get('estimated_price_vnd', 0))
            })

        return recommendations

    except Exception as e:
        print(f"Error getting initial recommendations: {e}")
        return []


def add_new_customer_routes(app):
    """Add new customer routes to Flask app"""

    @app.route('/new-customer')
    def new_customer_form():
        """Display new customer registration form"""
        return render_template('new_customer_form.html')

    @app.route('/api/register-customer', methods=['POST'])
    def register_customer():
        """Handle customer registration"""
        try:
            data = request.get_json()

            # Check if this is a request for fresh recommendations only
            generate_fresh = data.get('generate_fresh', False)

            # Validate data (skip validation for fresh recommendation requests)
            if not generate_fresh:
                errors = validate_customer_data(data)
                if errors:
                    return jsonify({
                        'success': False,
                        'errors': errors
                    }), 400

            # Generate customer ID
            customer_id = generate_customer_id()            # Prepare customer data
            customer_data = {
                'customer_id': customer_id,
                'full_name': str(data['full_name']).strip(),
                'email': str(data['email']).strip().lower(),
                'phone': str(data['phone']).strip(),
                'age': int(data['age']),
                'gender': str(data['gender']).strip(),
                'location': str(data.get('location', '')).strip(),
                'occupation': str(data.get('occupation', '')).strip(),
                'health_goals': ','.join(validate_health_goals(data.get('health_goals', []))),
                'preferred_cuisines': 'vietnamese',  # Always Vietnamese as per form
                'regional_preferences': ','.join(validate_regional_preferences(data.get('regional_preferences', []))),
                'preferred_meal_times': ','.join(validate_meal_times(data.get('preferred_meal_times', []))),
                'cooking_skill_level': str(data.get('cooking_skill_level', 'beginner')).strip(),
                'budget_range': str(data.get('budget_range', 'medium')).strip(),
                'registration_date': datetime.now().isoformat(),
                'status': 'active'
            }

            # Save to CSV (only if not generating fresh recommendations)
            if not generate_fresh:
                success = save_customer_to_csv(customer_data)
                if not success:
                    return jsonify({
                        'success': False,
                        'error': 'Không thể lưu thông tin khách hàng'
                    }), 500

            # Get recommendations
            randomize = data.get('randomize', False)
            initial_recommendations = get_initial_recommendations(
                customer_data, randomize=randomize)

            return jsonify({
                'success': True,
                'customer_id': customer_id,
                'message': 'Đăng ký thành công!' if not generate_fresh else 'Tạo gợi ý mới thành công!',
                'customer_data': customer_data,
                'recommendations': initial_recommendations
            })

        except Exception as e:
            import traceback
            error_msg = f'Lỗi server: {str(e)}'
            print(f"❌ Error in register_customer: {error_msg}")
            print(f"📋 Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500

    @app.route('/api/check-email', methods=['POST'])
    def check_email_exists():
        """Check if email already exists"""
        try:
            data = request.get_json()
            email = data.get('email', '').strip().lower()

            if not email:
                return jsonify({'exists': False})

            # Check in customers CSV
            if os.path.exists('customers_data.csv'):
                df = pd.read_csv('customers_data.csv')
                exists = email in df['email'].str.lower().values
                return jsonify({'exists': exists})

            return jsonify({'exists': False})

        except Exception as e:
            return jsonify({'exists': False, 'error': str(e)})

    @app.route('/api/get-customer/<customer_id>')
    def get_customer_info(customer_id):
        """Get customer information"""
        try:
            if os.path.exists('customers_data.csv'):
                df = pd.read_csv('customers_data.csv')
                customer = df[df['customer_id'] == customer_id]

                if not customer.empty:
                    customer_data = customer.iloc[0].to_dict()

                    # Convert NaN to None/empty strings
                    for key, value in customer_data.items():
                        if pd.isna(value):
                            customer_data[key] = '' if isinstance(
                                value, str) else None

                    return jsonify({
                        'success': True,
                        'customer': customer_data
                    })

            return jsonify({
                'success': False,
                'error': 'Không tìm thấy khách hàng'
            }), 404

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/customer-welcome/<customer_id>')
    def customer_welcome(customer_id):
        """Welcome page for new customer with initial recommendations"""
        return render_template('customer_welcome.html', customer_id=customer_id)

    print("✅ New customer routes added to Flask app")


# Standalone testing
if __name__ == "__main__":
    # Test customer data validation
    test_data = {
        'full_name': 'Nguyễn Văn A',
        'email': 'nguyenvana@email.com',
        'phone': '0987654321',
        'age': 25,
        'gender': 'male',
        'health_goals': ['weight_loss'],
        'preferred_meal_times': ['lunch', 'dinner']
    }

    print("🧪 Testing customer registration system...")

    # Test validation
    errors = validate_customer_data(test_data)
    print(f"Validation errors: {errors}")

    # Test customer ID generation
    customer_id = generate_customer_id()
    print(f"Generated customer ID: {customer_id}")

    # Test initial recommendations
    recommendations = get_initial_recommendations(test_data)
    print(f"Initial recommendations: {len(recommendations)} recipes found")

    for i, rec in enumerate(recommendations[:3], 1):
        print(f"{i}. {rec['recipe_name']} - Rating: {rec['avg_rating']}")

    print("✅ Customer registration system test completed")
