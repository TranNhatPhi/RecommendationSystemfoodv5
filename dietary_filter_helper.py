
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
