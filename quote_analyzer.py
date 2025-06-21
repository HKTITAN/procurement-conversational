#!/usr/bin/env python3
"""
Quote Analysis Tool - Find Cheapest Vendors
Analyzes collected quotes from Gemini Live conversations to identify best pricing
"""

import pandas as pd
import json
from datetime import datetime
import os

class QuoteAnalyzer:
    """Analyzes quotes and finds cheapest vendors"""
    
    def __init__(self, csv_file='gemini_live_quotes.csv'):
        self.csv_file = csv_file
        self.quotes_df = None
        
    def load_quotes(self):
        """Load quotes from CSV file"""
        try:
            if os.path.exists(self.csv_file):
                self.quotes_df = pd.read_csv(self.csv_file)
                print(f"✅ Loaded {len(self.quotes_df)} quotes from {self.csv_file}")
                return True
            else:
                print(f"❌ CSV file {self.csv_file} not found")
                return False
        except Exception as e:
            print(f"❌ Error loading quotes: {e}")
            return False
    
    def analyze_by_item(self):
        """Analyze quotes grouped by item"""
        if self.quotes_df is None or self.quotes_df.empty:
            print("📊 No quotes to analyze")
            return {}
        
        analysis = {}
        
        # Group by item
        grouped = self.quotes_df.groupby('item')
        
        for item_name, group in grouped:
            # Sort by price (ascending)
            sorted_quotes = group.sort_values('price')
            
            analysis[item_name] = {
                'total_quotes': len(group),
                'price_range': {
                    'min': float(sorted_quotes['price'].min()),
                    'max': float(sorted_quotes['price'].max()),
                    'avg': float(sorted_quotes['price'].mean())
                },
                'cheapest_vendor': {
                    'vendor': sorted_quotes.iloc[0]['vendor'],
                    'price': float(sorted_quotes.iloc[0]['price']),
                    'confidence': float(sorted_quotes.iloc[0]['confidence']),
                    'timestamp': sorted_quotes.iloc[0]['timestamp']
                },
                'all_quotes': []
            }
            
            # Add all quotes for this item
            for _, quote in sorted_quotes.iterrows():
                analysis[item_name]['all_quotes'].append({
                    'vendor': quote['vendor'],
                    'price': float(quote['price']),
                    'confidence': float(quote['confidence']),
                    'timestamp': quote['timestamp']
                })
        
        return analysis
    
    def generate_procurement_recommendation(self):
        """Generate procurement recommendations"""
        analysis = self.analyze_by_item()
        
        if not analysis:
            return None
        
        total_savings = 0
        recommendations = []
        
        print("\n🎯 PROCUREMENT RECOMMENDATIONS")
        print("=" * 60)
        
        for item_name, data in analysis.items():
            cheapest = data['cheapest_vendor']
            price_range = data['price_range']
            
            # Calculate potential savings
            potential_savings = price_range['max'] - price_range['min']
            savings_percentage = (potential_savings / price_range['max']) * 100 if price_range['max'] > 0 else 0
            
            recommendation = {
                'item': item_name,
                'recommended_vendor': cheapest['vendor'],
                'recommended_price': cheapest['price'],
                'confidence': cheapest['confidence'],
                'potential_savings': potential_savings,
                'savings_percentage': savings_percentage,
                'total_quotes_received': data['total_quotes']
            }
            
            recommendations.append(recommendation)
            total_savings += potential_savings
            
            print(f"\n📦 {item_name}")
            print(f"   🏆 Best Price: ₹{cheapest['price']} - {cheapest['vendor']}")
            print(f"   💰 Price Range: ₹{price_range['min']} - ₹{price_range['max']}")
            print(f"   📊 Quotes Received: {data['total_quotes']}")
            print(f"   💵 Potential Savings: ₹{potential_savings:.2f} ({savings_percentage:.1f}%)")
            print(f"   🎯 Confidence: {cheapest['confidence']*100:.0f}%")
        
        print(f"\n💰 TOTAL POTENTIAL SAVINGS: ₹{total_savings:.2f}")
        print("=" * 60)
        
        return {
            'recommendations': recommendations,
            'total_potential_savings': total_savings,
            'analysis_timestamp': datetime.now().isoformat(),
            'total_items_analyzed': len(analysis)
        }
    
    def export_recommendations(self, recommendations):
        """Export recommendations to JSON file"""
        try:
            output_file = f"procurement_recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(output_file, 'w') as f:
                json.dump(recommendations, f, indent=2)
            
            print(f"📄 Recommendations exported to: {output_file}")
            return output_file
        except Exception as e:
            print(f"❌ Export error: {e}")
            return None
    
    def create_vendor_comparison_csv(self):
        """Create a CSV file with vendor comparison"""
        if self.quotes_df is None or self.quotes_df.empty:
            return None
        
        try:
            # Create pivot table
            pivot = self.quotes_df.pivot_table(
                values='price',
                index='item',
                columns='vendor',
                aggfunc='min'  # Use minimum price if multiple quotes from same vendor
            )
            
            output_file = f"vendor_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            pivot.to_csv(output_file)
            
            print(f"📊 Vendor comparison exported to: {output_file}")
            return output_file
        except Exception as e:
            print(f"❌ Comparison export error: {e}")
            return None
    
    def get_vendor_summary(self):
        """Get summary by vendor"""
        if self.quotes_df is None or self.quotes_df.empty:
            return {}
        
        vendor_summary = {}
        grouped = self.quotes_df.groupby('vendor')
        
        for vendor, group in grouped:
            vendor_summary[vendor] = {
                'total_quotes': len(group),
                'items_quoted': list(group['item'].unique()),
                'average_price': float(group['price'].mean()),
                'price_range': {
                    'min': float(group['price'].min()),
                    'max': float(group['price'].max())
                },
                'average_confidence': float(group['confidence'].mean()),
                'last_quote_time': group['timestamp'].max()
            }
        
        return vendor_summary

def main():
    """Main analysis function"""
    print("🚀 Starting Quote Analysis...")
    
    analyzer = QuoteAnalyzer()
    
    # Load quotes
    if not analyzer.load_quotes():
        print("❌ Cannot proceed without quote data")
        return
    
    # Generate recommendations
    recommendations = analyzer.generate_procurement_recommendation()
    
    if recommendations:
        # Export recommendations
        analyzer.export_recommendations(recommendations)
        
        # Create vendor comparison
        analyzer.create_vendor_comparison_csv()
        
        # Show vendor summary
        print("\n📈 VENDOR SUMMARY")
        print("=" * 40)
        vendor_summary = analyzer.get_vendor_summary()
        
        for vendor, data in vendor_summary.items():
            print(f"\n🏪 {vendor}")
            print(f"   📦 Items Quoted: {len(data['items_quoted'])}")
            print(f"   💰 Avg Price: ₹{data['average_price']:.2f}")
            print(f"   📊 Confidence: {data['average_confidence']*100:.0f}%")
            print(f"   📅 Last Quote: {data['last_quote_time']}")
        
        print("\n✅ Analysis complete! Check the exported files for detailed reports.")
    else:
        print("❌ No recommendations could be generated")

if __name__ == "__main__":
    main() 