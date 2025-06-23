"""
Procurement Logic for Multi-Company Procurement Platform
Handles business logic for inventory management, vendor selection, and procurement analysis
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from models import Company, Vendor, InventoryItem, Quote, Negotiation, ProcurementError

class ProcurementEngine:
    """Main procurement business logic engine"""
    
    def __init__(self):
        self.procurement_rules = self._load_procurement_rules()
        self.pricing_thresholds = self._load_pricing_thresholds()
        self.vendor_performance_weights = {
            'rating': 0.3,
            'response_time': 0.2,
            'price_competitiveness': 0.25,
            'delivery_reliability': 0.15,
            'specialty_match': 0.1
        }
    
    def _load_procurement_rules(self) -> Dict[str, Any]:
        """Load procurement business rules"""
        return {
            'urgency_thresholds': {
                'critical': 0.5,  # Below 50% of minimum stock
                'urgent': 1.0,    # At or below minimum stock
                'normal': 1.2     # Above minimum but less than 120%
            },
            'budget_allocation': {
                'critical_items_percentage': 0.6,  # 60% budget for critical items
                'buffer_percentage': 0.1          # 10% buffer for emergencies
            },
            'vendor_selection_criteria': {
                'min_rating': 3.0,
                'max_response_time_hours': 72,
                'preferred_vendor_bonus': 0.1
            },
            'negotiation_limits': {
                'max_discount_request': 0.15,  # Max 15% discount request
                'min_order_multiplier': 2.0    # Minimum order 2x current shortage
            }
        }
    
    def _load_pricing_thresholds(self) -> Dict[str, float]:
        """Load pricing thresholds for different categories"""
        return {
            'Laboratory Consumables': 5.0,     # ₹5 per unit average
            'Chemicals': 500.0,                # ₹500 per bottle average
            'Medical Supplies': 100.0,         # ₹100 per unit average
            'Laboratory Equipment': 10000.0,   # ₹10K per unit average
            'Glassware': 50.0                  # ₹50 per unit average
        }
    
    def analyze_procurement_requirements(self, companies: Dict[str, Company]) -> Dict[str, Any]:
        """Analyze procurement requirements across all companies"""
        try:
            analysis = {
                'companies': {},
                'summary': {
                    'total_companies': len(companies),
                    'companies_needing_procurement': 0,
                    'critical_items': 0,
                    'urgent_items': 0,
                    'total_estimated_cost': 0.0,
                    'budget_utilization': {}
                },
                'recommendations': [],
                'risk_assessment': {}
            }
            
            for company_id, company in companies.items():
                company_analysis = self._analyze_company_requirements(company)
                analysis['companies'][company_id] = company_analysis
                
                # Update summary
                if company_analysis['needs_procurement']:
                    analysis['summary']['companies_needing_procurement'] += 1
                
                analysis['summary']['critical_items'] += company_analysis['critical_items_count']
                analysis['summary']['urgent_items'] += company_analysis['urgent_items_count']
                analysis['summary']['total_estimated_cost'] += company_analysis['estimated_cost']
                
                # Budget utilization
                budget_usage = (company_analysis['estimated_cost'] / company.budget_monthly) * 100
                analysis['summary']['budget_utilization'][company_id] = {
                    'company_name': company.name,
                    'usage_percentage': budget_usage,
                    'estimated_cost': company_analysis['estimated_cost'],
                    'monthly_budget': company.budget_monthly
                }
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_procurement_recommendations(analysis)
            
            # Risk assessment
            analysis['risk_assessment'] = self._assess_procurement_risks(analysis)
            
            return analysis
            
        except Exception as e:
            raise ProcurementError(f"Failed to analyze procurement requirements: {e}")
    
    def _analyze_company_requirements(self, company: Company) -> Dict[str, Any]:
        """Analyze procurement requirements for a single company"""
        analysis = {
            'company_id': company.company_id,
            'company_name': company.name,
            'needs_procurement': False,
            'critical_items': [],
            'urgent_items': [],
            'normal_items': [],
            'critical_items_count': 0,
            'urgent_items_count': 0,
            'estimated_cost': 0.0,
            'priority_items': [],
            'budget_impact': 'low'
        }
        
        if not company.inventory:
            return analysis
        
        for item_id, item in company.inventory.items():
            item_analysis = self._analyze_inventory_item(item, company)
            
            if item_analysis['urgency'] == 'critical':
                analysis['critical_items'].append(item_analysis)
                analysis['critical_items_count'] += 1
                analysis['needs_procurement'] = True
            elif item_analysis['urgency'] == 'urgent':
                analysis['urgent_items'].append(item_analysis)
                analysis['urgent_items_count'] += 1
                analysis['needs_procurement'] = True
            else:
                analysis['normal_items'].append(item_analysis)
            
            analysis['estimated_cost'] += item_analysis['estimated_cost']
            
            # Identify priority items (high priority + low stock)
            if item.priority == 'high' and item_analysis['urgency'] in ['critical', 'urgent']:
                analysis['priority_items'].append(item_analysis)
        
        # Determine budget impact
        budget_percentage = (analysis['estimated_cost'] / company.budget_monthly) * 100
        if budget_percentage > 50:
            analysis['budget_impact'] = 'high'
        elif budget_percentage > 25:
            analysis['budget_impact'] = 'medium'
        else:
            analysis['budget_impact'] = 'low'
        
        return analysis
    
    def _analyze_inventory_item(self, item: InventoryItem, company: Company) -> Dict[str, Any]:
        """Analyze individual inventory item"""
        shortage = max(0, item.minimum_required - item.current_stock)
        stock_ratio = item.current_stock / item.minimum_required if item.minimum_required > 0 else 1.0
        
        # Determine urgency based on stock ratio
        if stock_ratio < self.procurement_rules['urgency_thresholds']['critical']:
            urgency = 'critical'
        elif stock_ratio <= self.procurement_rules['urgency_thresholds']['urgent']:
            urgency = 'urgent'
        else:
            urgency = 'normal'
        
        # Calculate recommended order quantity
        if urgency in ['critical', 'urgent']:
            # Order enough to reach 150% of minimum required
            recommended_order = max(shortage, int(item.minimum_required * 0.5))
            recommended_order = min(recommended_order, item.maximum_capacity - item.current_stock)
        else:
            recommended_order = 0
        
        # Estimate cost
        estimated_cost = recommended_order * item.average_price if recommended_order > 0 else 0.0
        
        return {
            'item': item.to_dict(),
            'urgency': urgency,
            'shortage': shortage,
            'stock_ratio': stock_ratio,
            'recommended_order': recommended_order,
            'estimated_cost': estimated_cost,
            'days_until_stockout': self._calculate_days_until_stockout(item),
            'company_priority': company.procurement_priority
        }
    
    def _calculate_days_until_stockout(self, item: InventoryItem) -> Optional[int]:
        """Calculate estimated days until stockout (simplified calculation)"""
        # This is a simplified calculation - in real scenarios, you'd use consumption patterns
        if item.current_stock <= 0:
            return 0
        
        # Assume consumption based on category
        daily_consumption_estimates = {
            'Laboratory Consumables': 5,  # 5 units per day
            'Chemicals': 1,               # 1 bottle per day
            'Medical Supplies': 10,       # 10 units per day
            'Laboratory Equipment': 0.1,  # 1 unit per 10 days
            'Glassware': 2                # 2 units per day
        }
        
        daily_consumption = daily_consumption_estimates.get(item.category, 1)
        return int(item.current_stock / daily_consumption) if daily_consumption > 0 else None
    
    def find_suitable_vendors(self, item: InventoryItem, vendors: Dict[str, Vendor]) -> List[Dict[str, Any]]:
        """Find and rank suitable vendors for an item"""
        suitable_vendors = []
        
        for vendor_id, vendor in vendors.items():
            suitability_score = self._calculate_vendor_suitability(vendor, item)
            
            if suitability_score > 0:
                vendor_analysis = {
                    'vendor': vendor.to_dict(),
                    'vendor_id': vendor_id,
                    'suitability_score': suitability_score,
                    'specialty_match': vendor.can_supply_category(item.category),
                    'is_preferred': vendor_id in (item.preferred_vendors or []),
                    'estimated_response_time': vendor.response_time,
                    'price_competitiveness': vendor.price_competitiveness,
                    'rating': vendor.rating
                }
                suitable_vendors.append(vendor_analysis)
        
        # Sort by suitability score (highest first)
        suitable_vendors.sort(key=lambda x: x['suitability_score'], reverse=True)
        
        return suitable_vendors
    
    def _calculate_vendor_suitability(self, vendor: Vendor, item: InventoryItem) -> float:
        """Calculate vendor suitability score for an item"""
        score = 0.0
        weights = self.vendor_performance_weights
        
        # Rating score (0-5 scale, normalize to 0-1)
        if vendor.rating >= self.procurement_rules['vendor_selection_criteria']['min_rating']:
            score += (vendor.rating / 5.0) * weights['rating']
        else:
            return 0.0  # Below minimum rating threshold
        
        # Response time score (convert to hours and score inversely)
        response_hours = self._parse_response_time(vendor.response_time)
        max_acceptable_hours = self.procurement_rules['vendor_selection_criteria']['max_response_time_hours']
        
        if response_hours <= max_acceptable_hours:
            response_score = 1.0 - (response_hours / max_acceptable_hours)
            score += response_score * weights['response_time']
        
        # Price competitiveness score
        price_scores = {
            'budget_friendly': 1.0,
            'competitive': 0.8,
            'premium': 0.5
        }
        score += price_scores.get(vendor.price_competitiveness, 0.3) * weights['price_competitiveness']
        
        # Delivery reliability (based on success rate)
        delivery_score = vendor.get_success_rate() / 100.0
        score += delivery_score * weights['delivery_reliability']
        
        # Specialty match bonus
        if vendor.can_supply_category(item.category):
            score += weights['specialty_match']
        
        # Preferred vendor bonus
        if item.preferred_vendors and vendor.vendor_id in item.preferred_vendors:
            score += self.procurement_rules['vendor_selection_criteria']['preferred_vendor_bonus']
        
        return score
    
    def _parse_response_time(self, response_time: str) -> int:
        """Parse response time string to hours"""
        time_map = {
            '12 hours': 12,
            '24 hours': 24,
            '36 hours': 36,
            '48 hours': 48,
            '72 hours': 72
        }
        return time_map.get(response_time, 48)  # Default to 48 hours
    
    def generate_procurement_recommendations(self, company: Company, analysis: Dict[str, Any], vendors: Dict[str, Vendor]) -> List[Dict[str, Any]]:
        """Generate specific procurement recommendations for a company"""
        recommendations = []
        
        # Process critical items first
        for item_analysis in analysis.get('critical_items', []):
            item_dict = item_analysis['item']
            item = InventoryItem(**item_dict)
            
            suitable_vendors = self.find_suitable_vendors(item, vendors)
            
            if suitable_vendors:
                recommendation = {
                    'item': item_dict,
                    'urgency': 'critical',
                    'recommended_quantity': item_analysis['recommended_order'],
                    'estimated_cost': item_analysis['estimated_cost'],
                    'recommended_vendors': suitable_vendors[:3],  # Top 3 vendors
                    'action': 'immediate_procurement',
                    'justification': f"Critical shortage: {item_analysis['shortage']} units below minimum",
                    'timeline': 'Within 24 hours',
                    'budget_impact': (item_analysis['estimated_cost'] / company.budget_monthly) * 100
                }
                recommendations.append(recommendation)
        
        # Process urgent items
        for item_analysis in analysis.get('urgent_items', []):
            item_dict = item_analysis['item']
            item = InventoryItem(**item_dict)
            
            suitable_vendors = self.find_suitable_vendors(item, vendors)
            
            if suitable_vendors:
                recommendation = {
                    'item': item_dict,
                    'urgency': 'urgent',
                    'recommended_quantity': item_analysis['recommended_order'],
                    'estimated_cost': item_analysis['estimated_cost'],
                    'recommended_vendors': suitable_vendors[:2],  # Top 2 vendors
                    'action': 'priority_procurement',
                    'justification': f"Below minimum stock: {item_analysis['shortage']} units needed",
                    'timeline': 'Within 72 hours',
                    'budget_impact': (item_analysis['estimated_cost'] / company.budget_monthly) * 100
                }
                recommendations.append(recommendation)
        
        # Sort recommendations by urgency and budget impact
        recommendations.sort(key=lambda x: (
            0 if x['urgency'] == 'critical' else 1,
            -x['budget_impact']
        ))
        
        return recommendations
    
    def _generate_procurement_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate high-level procurement recommendations"""
        recommendations = []
        
        # Budget utilization recommendations
        high_budget_companies = [
            comp for comp, data in analysis['summary']['budget_utilization'].items()
            if data['usage_percentage'] > 50
        ]
        
        if high_budget_companies:
            recommendations.append(
                f"High budget utilization alert: {len(high_budget_companies)} companies exceeding 50% monthly budget"
            )
        
        # Critical items recommendations
        if analysis['summary']['critical_items'] > 0:
            recommendations.append(
                f"Immediate action required: {analysis['summary']['critical_items']} critical items across all companies"
            )
        
        # Cost optimization recommendations
        if analysis['summary']['total_estimated_cost'] > 100000:  # ₹1 lakh
            recommendations.append(
                "Consider bulk procurement negotiations for cost optimization"
            )
        
        return recommendations
    
    def _assess_procurement_risks(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess procurement risks"""
        risks = {
            'budget_risks': [],
            'supply_risks': [],
            'operational_risks': [],
            'overall_risk_level': 'low'
        }
        
        # Budget risks
        for company_id, budget_data in analysis['summary']['budget_utilization'].items():
            if budget_data['usage_percentage'] > 75:
                risks['budget_risks'].append(
                    f"{budget_data['company_name']}: {budget_data['usage_percentage']:.1f}% budget utilization"
                )
        
        # Supply risks
        if analysis['summary']['critical_items'] > 3:
            risks['supply_risks'].append(
                f"Multiple critical items ({analysis['summary']['critical_items']}) may impact operations"
            )
        
        # Determine overall risk level
        total_risk_factors = len(risks['budget_risks']) + len(risks['supply_risks']) + len(risks['operational_risks'])
        
        if total_risk_factors >= 3:
            risks['overall_risk_level'] = 'high'
        elif total_risk_factors >= 1:
            risks['overall_risk_level'] = 'medium'
        
        return risks
    
    def create_procurement_quote(self, vendor: Vendor, company: Company, items: List[Dict], total_amount: float) -> Quote:
        """Create a new procurement quote"""
        quote = Quote(
            quote_id=str(uuid.uuid4()),
            vendor_id=vendor.vendor_id,
            company_id=company.company_id,
            items=items,
            total_amount=total_amount,
            validity_days=30,  # Default 30 days validity
            delivery_time=vendor.response_time,
            payment_terms="Net 30",  # Default payment terms
            timestamp=datetime.now().isoformat(),
            status="pending"
        )
        
        return quote
    
    def analyze_quote_competitiveness(self, quote: Quote, item_category: str) -> Dict[str, Any]:
        """Analyze quote competitiveness against market rates"""
        analysis = {
            'quote_id': quote.quote_id,
            'competitiveness': 'unknown',
            'price_per_unit': 0.0,
            'market_comparison': 'no_data',
            'savings_potential': 0.0,
            'recommendations': []
        }
        
        if not quote.items:
            return analysis
        
        # Calculate average price per unit
        total_units = sum(item.get('quantity', 0) for item in quote.items)
        if total_units > 0:
            analysis['price_per_unit'] = quote.total_amount / total_units
        
        # Compare with market threshold
        market_threshold = self.pricing_thresholds.get(item_category, 100.0)
        
        if analysis['price_per_unit'] <= market_threshold * 0.8:  # 20% below market
            analysis['competitiveness'] = 'excellent'
            analysis['market_comparison'] = 'below_market'
        elif analysis['price_per_unit'] <= market_threshold:
            analysis['competitiveness'] = 'good'
            analysis['market_comparison'] = 'at_market'
        elif analysis['price_per_unit'] <= market_threshold * 1.2:  # 20% above market
            analysis['competitiveness'] = 'fair'
            analysis['market_comparison'] = 'above_market'
            analysis['savings_potential'] = analysis['price_per_unit'] - market_threshold
        else:
            analysis['competitiveness'] = 'poor'
            analysis['market_comparison'] = 'significantly_above_market'
            analysis['savings_potential'] = analysis['price_per_unit'] - market_threshold
        
        # Generate recommendations
        if analysis['competitiveness'] in ['fair', 'poor']:
            analysis['recommendations'].append("Consider negotiating for better pricing")
            if analysis['savings_potential'] > 0:
                analysis['recommendations'].append(f"Potential savings: ₹{analysis['savings_potential']:.2f} per unit")
        
        return analysis
    
    def suggest_negotiation_strategy(self, quote: Quote, vendor: Vendor, company: Company) -> Dict[str, Any]:
        """Suggest negotiation strategy for a quote"""
        strategy = {
            'approach': 'standard',
            'target_discount': 0.0,
            'negotiation_points': [],
            'fallback_options': [],
            'timeline': 'standard'
        }
        
        # Determine negotiation approach based on vendor rating and relationship
        if vendor.rating >= 4.5:
            strategy['approach'] = 'partnership'
            strategy['negotiation_points'].append("Emphasize long-term partnership value")
        elif vendor.rating < 3.5:
            strategy['approach'] = 'competitive'
            strategy['negotiation_points'].append("Leverage competitive alternatives")
        
        # Calculate target discount based on quote analysis
        quote_analysis = self.analyze_quote_competitiveness(quote, "Laboratory Consumables")  # Default category
        
        if quote_analysis['competitiveness'] in ['fair', 'poor']:
            max_discount = self.procurement_rules['negotiation_limits']['max_discount_request']
            strategy['target_discount'] = min(max_discount, quote_analysis['savings_potential'] / quote.total_amount)
            strategy['negotiation_points'].append(f"Request {strategy['target_discount']*100:.1f}% discount")
        
        # Add volume-based negotiation points
        total_items = sum(item.get('quantity', 0) for item in quote.items)
        if total_items >= 100:  # Large order
            strategy['negotiation_points'].append("Leverage order volume for bulk discount")
        
        # Timeline considerations
        if company.procurement_priority == 'urgent_delivery':
            strategy['timeline'] = 'expedited'
            strategy['negotiation_points'].append("Prioritize delivery speed over price")
        elif company.procurement_priority == 'cost_effective':
            strategy['timeline'] = 'extended'
            strategy['negotiation_points'].append("Extended payment terms for better pricing")
        
        return strategy

# Global procurement engine instance
procurement_engine = ProcurementEngine() 