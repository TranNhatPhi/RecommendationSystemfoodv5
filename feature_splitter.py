#!/usr/bin/env python3
"""
Feature Splitter - Tách dữ liệu thành các feature riêng biệt cho RAG system
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Any

class FeatureSplitter:
    def __init__(self, base_dir: str = "."):
        """Initialize feature splitter"""
        self.base_dir = base_dir
        self.output_dir = os.path.join(base_dir, "rag_features")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"📁 Output directory: {self.output_dir}")
    
    def split_customers_data(self, input_file: str = "customers_data.csv") -> Dict[str, Any]:
        """Split customers data into features"""
        try:
            df = pd.read_csv(os.path.join(self.base_dir, input_file))
            print(f"📊 Loading customers data: {df.shape}")
            
            # 1. Customer Profiles Feature
            customer_profiles = df[['customer_id', 'full_name', 'gender', 'age_group', 
                                  'region', 'location', 'registration_date']].copy()
            
            # Create text representation for embedding
            customer_profiles['profile_text'] = customer_profiles.apply(lambda row: 
                f"Khách hàng {row['full_name']} ({row['customer_id']}) là {row['gender']} "
                f"thuộc nhóm tuổi {row['age_group']}, đến từ {row['region']} - {row['location']}", 
                axis=1
            )
            
            output_file = os.path.join(self.output_dir, "customer_profiles.csv")
            customer_profiles.to_csv(output_file, index=False)
            print(f"✅ Saved customer profiles: {output_file}")
            
            # 2. Customer Demographics Feature
            demographics = df[['customer_id', 'age', 'gender', 'age_group', 
                             'region', 'regional_preferences']].copy()
            
            demographics['demographic_text'] = demographics.apply(lambda row:
                f"Nhân khẩu học: {row['age']} tuổi, {row['gender']}, "
                f"nhóm {row['age_group']}, khu vực {row['region']}, "
                f"sở thích: {row.get('regional_preferences', 'không xác định')}",
                axis=1
            )
            
            output_file = os.path.join(self.output_dir, "customer_demographics.csv")
            demographics.to_csv(output_file, index=False)
            print(f"✅ Saved demographics: {output_file}")
            
            return {
                'success': True,
                'customer_profiles': len(customer_profiles),
                'demographics': len(demographics),
                'source': input_file
            }
            
        except Exception as e:
            print(f"❌ Error splitting customers data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def split_interactions_data(self, input_file: str = "interactions_enhanced_with_recommendations.csv") -> Dict[str, Any]:
        """Split interactions data into features"""
        try:
            df = pd.read_csv(os.path.join(self.base_dir, input_file))
            print(f"📊 Loading interactions data: {df.shape}")
            
            # 1. Recipe Information Feature
            recipe_cols = ['recipe_name', 'recipe_url', 'difficulty', 'meal_time', 
                          'nutrition_category', 'estimated_calories', 'preparation_time_minutes',
                          'ingredient_count', 'estimated_price_vnd']
            
            recipes = df[recipe_cols].drop_duplicates(subset=['recipe_name']).copy()
            
            # Create text representation
            recipes['recipe_text'] = recipes.apply(lambda row:
                f"Món {row['recipe_name']} là món {row.get('meal_time', 'không xác định')} "
                f"có độ khó {row.get('difficulty', 'trung bình')}, "
                f"thuộc loại {row.get('nutrition_category', 'hỗn hợp')}, "
                f"khoảng {row.get('estimated_calories', 0)} calo, "
                f"thời gian chế biến {row.get('preparation_time_minutes', 0)} phút, "
                f"giá ước tính {row.get('estimated_price_vnd', 0)} VND",
                axis=1
            )
            
            output_file = os.path.join(self.output_dir, "recipes.csv")
            recipes.to_csv(output_file, index=False)
            print(f"✅ Saved recipes: {output_file}")
            
            # 2. Customer Interactions Feature
            interaction_cols = ['customer_id', 'recipe_name', 'interaction_type', 
                              'rating', 'interaction_date', 'comment']
            
            interactions = df[interaction_cols].copy()
            
            # Create text representation
            interactions['interaction_text'] = interactions.apply(lambda row:
                f"Khách hàng {row['customer_id']} đã {row['interaction_type']} "
                f"món {row['recipe_name']} với rating {row.get('rating', 0)}/5 "
                f"vào {row['interaction_date']}. "
                f"Nhận xét: {row.get('comment', 'Không có nhận xét')}",
                axis=1
            )
            
            output_file = os.path.join(self.output_dir, "customer_interactions.csv")
            interactions.to_csv(output_file, index=False)
            print(f"✅ Saved interactions: {output_file}")
            
            # 3. Nutrition Information Feature
            nutrition_cols = ['recipe_name', 'nutrition_category', 'estimated_calories',
                            'difficulty', 'meal_time', 'ingredient_count']
            
            nutrition = df[nutrition_cols].drop_duplicates(subset=['recipe_name']).copy()
            
            nutrition['nutrition_text'] = nutrition.apply(lambda row:
                f"Thông tin dinh dưỡng món {row['recipe_name']}: "
                f"loại {row.get('nutrition_category', 'hỗn hợp')}, "
                f"{row.get('estimated_calories', 0)} calo, "
                f"phù hợp cho {row.get('meal_time', 'mọi bữa')}, "
                f"độ phức tạp {row.get('difficulty', 'trung bình')}, "
                f"với {row.get('ingredient_count', 0)} nguyên liệu",
                axis=1
            )
            
            output_file = os.path.join(self.output_dir, "nutrition_info.csv")
            nutrition.to_csv(output_file, index=False)
            print(f"✅ Saved nutrition info: {output_file}")
            
            # 4. Recommendation Scores Feature
            if 'enhanced_recommendation_score' in df.columns:
                rec_cols = ['customer_id', 'recipe_name', 'content_score', 'cf_score',
                           'enhanced_recommendation_score', 'rating']
                
                recommendations = df[rec_cols].copy()
                
                recommendations['recommendation_text'] = recommendations.apply(lambda row:
                    f"Gợi ý cho khách hàng {row['customer_id']}: món {row['recipe_name']} "
                    f"với điểm content {row.get('content_score', 0):.2f}, "
                    f"điểm collaborative {row.get('cf_score', 0):.2f}, "
                    f"điểm tổng hợp {row.get('enhanced_recommendation_score', 0):.2f}, "
                    f"rating thực tế {row.get('rating', 0)}/5",
                    axis=1
                )
                
                output_file = os.path.join(self.output_dir, "recommendation_scores.csv")
                recommendations.to_csv(output_file, index=False)
                print(f"✅ Saved recommendation scores: {output_file}")
            
            return {
                'success': True,
                'recipes': len(recipes),
                'interactions': len(interactions),
                'nutrition': len(nutrition),
                'recommendations': len(recommendations) if 'enhanced_recommendation_score' in df.columns else 0,
                'source': input_file
            }
            
        except Exception as e:
            print(f"❌ Error splitting interactions data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_feature_summary(self) -> Dict[str, Any]:
        """Create summary of all features"""
        summary = {
            'created_at': datetime.now().isoformat(),
            'features': {}
        }
        
        # Check all CSV files in output directory
        for file in os.listdir(self.output_dir):
            if file.endswith('.csv'):
                file_path = os.path.join(self.output_dir, file)
                try:
                    df = pd.read_csv(file_path)
                    feature_name = file.replace('.csv', '')
                    
                    summary['features'][feature_name] = {
                        'file': file,
                        'rows': len(df),
                        'columns': list(df.columns),
                        'size_mb': round(os.path.getsize(file_path) / 1024 / 1024, 2),
                        'text_column': None
                    }
                    
                    # Find text column for embedding
                    text_cols = [col for col in df.columns if 'text' in col.lower()]
                    if text_cols:
                        summary['features'][feature_name]['text_column'] = text_cols[0]
                    
                    print(f"📊 {feature_name}: {len(df)} rows, {len(df.columns)} columns")
                    
                except Exception as e:
                    print(f"⚠️ Error reading {file}: {str(e)}")
        
        # Save summary
        summary_file = os.path.join(self.output_dir, "features_summary.json")
        import json
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Feature summary saved: {summary_file}")
        return summary
    
    def split_all_data(self) -> Dict[str, Any]:
        """Split all available data into features"""
        print("🚀 Starting feature splitting process...")
        
        results = {}
        
        # Split customers data
        customers_result = self.split_customers_data()
        results['customers'] = customers_result
        
        # Split interactions data
        interactions_result = self.split_interactions_data()
        results['interactions'] = interactions_result
        
        # Create summary
        summary = self.create_feature_summary()
        results['summary'] = summary
        
        print(f"\n✅ Feature splitting completed!")
        print(f"📁 Features saved in: {self.output_dir}")
        
        return results

def main():
    """Main function to run feature splitting"""
    print("🎯 Feature Splitter for RAG System")
    print("=" * 50)
    
    # Initialize splitter
    splitter = FeatureSplitter()
    
    # Split all data
    results = splitter.split_all_data()
    
    # Show results
    print(f"\n📈 Results Summary:")
    for key, result in results.items():
        if isinstance(result, dict) and 'success' in result:
            if result['success']:
                print(f"  ✅ {key}: Success")
                for sub_key, value in result.items():
                    if sub_key not in ['success', 'error', 'source']:
                        print(f"    - {sub_key}: {value}")
            else:
                print(f"  ❌ {key}: Failed - {result.get('error', 'Unknown error')}")
    
    return results

if __name__ == "__main__":
    results = main()
