"""
Web Server for Multi-Company Procurement Platform
Main Flask application with comprehensive routes and error handling
"""

import os
import json
import uuid
import threading
from datetime import datetime
from flask import Flask, request, render_template, jsonify, redirect, url_for, Response
from flask_socketio import SocketIO, emit
from werkzeug.exceptions import NotFound, InternalServerError

# Import our modules
from database import db
from ai_services import ai_service
from communication import comm_service
from procurement import procurement_engine
from models import Company, Vendor, ConversationEntry, ProcurementError

class ProcurementWebServer:
    """Main web server class with comprehensive error handling"""
    
    def __init__(self, host='0.0.0.0', port=5000):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = os.urandom(24)
        
        # Enable CORS for local development
        self.app.config['CORS_ORIGINS'] = ['http://localhost:5000', 'http://127.0.0.1:5000']
        
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        self.host = host
        self.port = port
        self.ngrok_url = None
        
        # Initialize routes and handlers
        self.setup_routes()
        self.setup_error_handlers()
        self.setup_socketio_events()
        
        print(f"🌐 Web server initialized on {host}:{port}")
    
    def setup_routes(self):
        """Setup all Flask routes"""
        
        # Main dashboard
        @self.app.route('/')
        def dashboard():
            try:
                # Get dashboard data
                companies = db.get_all_companies()
                vendors = db.get_all_vendors()
                metrics = db.get_metrics()
                
                # Get procurement analysis
                procurement_analysis = procurement_engine.analyze_procurement_requirements(companies)
                
                # Generate alerts
                alerts = self.generate_alerts(procurement_analysis)
                
                dashboard_data = {
                    'title': 'Procurement Dashboard',
                    'active_page': 'dashboard',
                    'page_icon': 'home',
                    'stats': {
                        'total_companies': len(companies),
                        'total_vendors': len(vendors),
                        'active_conversations': metrics.active_conversations,
                        'total_savings': metrics.total_savings,
                        'critical_items': procurement_analysis['summary']['critical_items'],
                        'urgent_items': procurement_analysis['summary']['urgent_items']
                    },
                    'companies': companies,
                    'alerts': alerts,
                    'procurement_summary': procurement_analysis['summary'],
                    'page_actions': [
                        {'type': 'primary', 'icon': 'phone', 'label': 'Make Call', 'onclick': 'initiateCall()'},
                        {'type': 'success', 'icon': 'whatsapp', 'label': 'WhatsApp', 'onclick': 'sendWhatsApp()'},
                        {'type': 'info', 'icon': 'chart-line', 'label': 'Analysis', 'onclick': 'runAnalysis()'}
                    ]
                }
                
                return render_template('dashboard.html', **dashboard_data)
                
            except Exception as e:
                print(f"❌ Dashboard error: {e}")
                return self.render_error_page("Dashboard Error", str(e))
        
        # Companies page
        @self.app.route('/companies')
        def companies_page():
            try:
                companies = db.get_all_companies()
                
                # Add additional computed fields to each company for display
                # but keep the dictionary structure that templates expect
                for company_id, company in companies.items():
                    low_stock_items = company.get_low_stock_items()
                    
                    # Add computed fields as attributes (non-persistent)
                    company._low_stock_count = len(low_stock_items)
                    company._inventory_value = company.get_total_inventory_value()
                    company._status = 'critical' if len(low_stock_items) > 2 else 'warning' if len(low_stock_items) > 0 else 'normal'
                    company._total_items = len(company.inventory) if company.inventory else 0
                
                return render_template('companies.html', 
                                     title='Companies Management',
                                     active_page='companies',
                                     page_icon='building',
                                     companies=companies)
                
            except Exception as e:
                print(f"❌ Companies page error: {e}")
                return self.render_error_page("Companies Error", str(e))
        
        # Vendors page
        @self.app.route('/vendors')
        def vendors_page():
            try:
                vendors = db.get_all_vendors()
                
                vendors_data = []
                for vendor in vendors.values():
                    vendors_data.append({
                        'vendor_id': vendor.vendor_id,
                        'name': vendor.name,
                        'phone': vendor.phone,
                        'email': vendor.email,
                        'specialties': vendor.specialties,
                        'rating': vendor.rating,
                        'response_time': vendor.response_time,
                        'price_competitiveness': vendor.price_competitiveness,
                        'success_rate': vendor.get_success_rate(),
                        'performance_score': self.calculate_vendor_performance(vendor),
                        'total_orders': vendor.total_orders,
                        'status': 'excellent' if vendor.rating >= 4.5 else 'good' if vendor.rating >= 4.0 else 'average'
                    })
                
                # Sort by performance score
                vendors_data.sort(key=lambda x: x['performance_score'], reverse=True)
                
                return render_template('vendors.html',
                                     title='Vendors Management',
                                     active_page='vendors',
                                     page_icon='handshake',
                                     vendors=vendors_data)
                
            except Exception as e:
                print(f"❌ Vendors page error: {e}")
                return self.render_error_page("Vendors Error", str(e))
        
        # Procurement page
        @self.app.route('/procurement')
        def procurement_page():
            try:
                companies = db.get_all_companies()
                vendors = db.get_all_vendors()
                
                print(f"💼 Loading procurement page - Companies: {len(companies)}, Vendors: {len(vendors)}")
                
                # Initialize default analysis structure
                analysis = {
                    'summary': {
                        'critical_items': 0,
                        'urgent_items': 0,
                        'companies_needing_procurement': 0,
                        'total_estimated_cost': 0,
                        'total_items': 0,
                        'budget_utilization': {}
                    },
                    'companies': {},
                    'recommendations': []
                }
                
                recommendations = {}
                
                # Process each company
                for company_id, company in companies.items():
                    print(f"📊 Analyzing {company.name}...")
                    
                    if not company.inventory:
                        print(f"   ⚠️ No inventory found for {company.name}")
                        continue
                    
                    low_stock_items = company.get_low_stock_items()
                    analysis['summary']['total_items'] += len(company.inventory)
                    
                    if low_stock_items:
                        analysis['summary']['companies_needing_procurement'] += 1
                        
                        # Count critical and urgent items
                        company_critical = 0
                        company_urgent = 0
                        company_cost = 0
                        items_needed = []
                        
                        for item in low_stock_items:
                            urgency = item.get_urgency()
                            shortage = item.get_shortage()
                            recommended_order = min(shortage * 2, item.maximum_capacity - item.current_stock) if shortage > 0 else 0
                            estimated_cost = item.average_price * recommended_order
                            
                            if urgency == 'critical':
                                company_critical += 1
                            elif urgency == 'urgent':
                                company_urgent += 1
                            
                            company_cost += estimated_cost
                            
                            items_needed.append({
                                'item': item,
                                'shortage': shortage,
                                'urgency': urgency,
                                'recommended_order': recommended_order,
                                'estimated_cost': estimated_cost
                            })
                        
                        analysis['summary']['critical_items'] += company_critical
                        analysis['summary']['urgent_items'] += company_urgent
                        analysis['summary']['total_estimated_cost'] += company_cost
                        
                        # Budget utilization
                        usage_percentage = (company_cost / company.budget_monthly * 100) if company.budget_monthly > 0 else 0
                        analysis['summary']['budget_utilization'][company_id] = {
                            'company_name': company.name,
                            'estimated_cost': company_cost,
                            'monthly_budget': company.budget_monthly,
                            'usage_percentage': usage_percentage
                        }
                        
                        # Company analysis
                        analysis['companies'][company_id] = {
                            'items_needed': items_needed
                        }
                        
                        # Generate vendor recommendations for this company
                        recommendations[company_id] = {}
                        for item_analysis in items_needed:
                            item = item_analysis['item']
                            try:
                                # Find suitable vendors using procurement engine
                                suitable_vendors = procurement_engine.find_suitable_vendors(item, vendors)
                                if suitable_vendors:
                                    vendor_data = suitable_vendors[0]
                                    # Extract vendor object from the analysis result
                                    vendor_obj = vendors.get(vendor_data['vendor_id'])
                                    if vendor_obj:
                                        recommendations[company_id][item.item_id] = {
                                            'vendor': vendor_obj
                                        }
                            except Exception as vendor_error:
                                print(f"   ⚠️ Error finding vendors for {item.name}: {vendor_error}")
                        
                        print(f"   📈 {company.name}: {company_critical} critical, {company_urgent} urgent, ₹{company_cost:,.0f} estimated cost")
                
                # Generate AI recommendations
                analysis['recommendations'] = [
                    "Consider consolidating orders from multiple companies for better vendor pricing",
                    "Schedule urgent calls to vendors for critical items", 
                    "Review vendor performance metrics for optimization opportunities",
                    "Implement automated reorder points to prevent future stockouts"
                ]
                
                if analysis['summary']['critical_items'] > 0:
                    analysis['recommendations'].insert(0, f"URGENT: {analysis['summary']['critical_items']} critical items require immediate procurement")
                
                print(f"✅ Procurement analysis complete: {analysis['summary']['companies_needing_procurement']} companies need procurement")
                
                return render_template('procurement.html',
                                     title='Procurement Analysis',
                                     active_page='procurement',
                                     page_icon='shopping-cart',
                                     analysis=analysis,
                                     companies=companies,
                                     recommendations=recommendations)
                
            except Exception as e:
                print(f"❌ Procurement page error: {e}")
                import traceback
                traceback.print_exc()
                
                # Return a safe fallback page
                fallback_analysis = {
                    'summary': {
                        'critical_items': 0,
                        'urgent_items': 0,
                        'companies_needing_procurement': 0,
                        'total_estimated_cost': 0,
                        'total_items': 0,
                        'budget_utilization': {}
                    },
                    'companies': {},
                    'recommendations': ["System initializing - please refresh in a moment"]
                }
                
                return render_template('procurement.html',
                                     title='Procurement Analysis',
                                     active_page='procurement',
                                     page_icon='shopping-cart',
                                     analysis=fallback_analysis,
                                     companies={},
                                     recommendations={})
        
        # Communication page
        @self.app.route('/communication')
        def communication_page():
            try:
                stats = comm_service.get_statistics()
                active_calls = comm_service.get_active_calls()
                whatsapp_conversations = comm_service.get_whatsapp_conversations()
                failed_calls = comm_service.get_failed_calls()
                
                return render_template('communication.html',
                                     title='Communication Center',
                                     active_page='communication',
                                     page_icon='phone',
                                     stats=stats,
                                     active_calls=active_calls,
                                     whatsapp_conversations=whatsapp_conversations,
                                     failed_calls=failed_calls)
                
            except Exception as e:
                print(f"❌ Communication page error: {e}")
                return self.render_error_page("Communication Error", str(e))
        
        # Analytics page
        @self.app.route('/analytics')
        def analytics_page():
            try:
                # Generate analytics data
                analytics_data = self.generate_analytics_data()
                
                return render_template('analytics.html',
                                     title='Analytics & Insights',
                                     active_page='analytics',
                                     page_icon='chart-bar',
                                     analytics=analytics_data)
                
            except Exception as e:
                print(f"❌ Analytics page error: {e}")
                return self.render_error_page("Analytics Error", str(e))
        
        # API Routes
        @self.app.route('/api/stats')
        def api_stats():
            try:
                companies = db.get_all_companies()
                metrics = db.get_metrics()
                comm_stats = comm_service.get_statistics()
                
                # Calculate budget utilization
                budget_utilization = []
                for company in companies.values():
                    low_stock = company.get_low_stock_items()
                    estimated_cost = sum(item.average_price * max(0, item.minimum_required - item.current_stock) 
                                       for item in low_stock)
                    usage_percentage = (estimated_cost / company.budget_monthly) * 100 if company.budget_monthly > 0 else 0
                    
                    budget_utilization.append({
                        'company_name': company.name,
                        'usage_percentage': usage_percentage,
                        'estimated_cost': estimated_cost,
                        'monthly_budget': company.budget_monthly
                    })
                
                return jsonify({
                    'total_companies': len(companies),
                    'total_vendors': len(db.get_all_vendors()),
                    'active_conversations': comm_stats['active_calls'] + comm_stats['whatsapp_conversations'],
                    'total_savings': metrics.total_savings,
                    'budget_utilization': budget_utilization,
                    'communication_stats': comm_stats
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/alerts')
        def api_alerts():
            try:
                companies = db.get_all_companies()
                analysis = procurement_engine.analyze_procurement_requirements(companies)
                alerts = self.generate_alerts(analysis)
                return jsonify(alerts)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/calls/initiate', methods=['POST'])
        def api_initiate_call():
            try:
                data = request.get_json()
                company_id = data.get('company_id')
                phone_number = data.get('phone_number')
                priority = data.get('priority', 'normal')
                
                if not company_id or not phone_number:
                    return jsonify({'error': 'Missing required fields'}), 400
                
                company = db.get_company(company_id)
                if not company:
                    return jsonify({'error': 'Company not found'}), 404
                
                # Make the call
                success, result = comm_service.make_voice_call(
                    phone_number, company, self.get_webhook_base_url()
                )
                
                if success:
                    return jsonify({
                        'success': True,
                        'call_sid': result,
                        'message': 'Call initiated successfully'
                    })
                else:
                    return jsonify({'error': result}), 400
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/whatsapp/send', methods=['POST'])
        def api_send_whatsapp():
            try:
                data = request.get_json()
                phone_number = data.get('phone_number')
                custom_message = data.get('message')
                
                if not phone_number:
                    return jsonify({'error': 'Phone number required'}), 400
                
                # Generate message if not provided
                if not custom_message:
                    # Use first company as default
                    companies = db.get_all_companies()
                    if companies:
                        company = next(iter(companies.values()))
                        custom_message = ai_service.generate_whatsapp_message(company)
                    else:
                        custom_message = "Hello! We're interested in your products. Please share your catalog."
                
                success, result = comm_service.send_whatsapp_message(phone_number, custom_message)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message_sid': result,
                        'message': 'WhatsApp sent successfully'
                    })
                else:
                    return jsonify({'error': result}), 400
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/calls/<call_sid>/status')
        def api_call_status(call_sid):
            try:
                active_calls = comm_service.get_active_calls()
                call_info = active_calls.get(call_sid)
                
                if not call_info:
                    return jsonify({'error': 'Call not found'}), 404
                
                return jsonify({
                    'call_sid': call_sid,
                    'status': call_info.get('status', 'unknown'),
                    'started_at': call_info.get('started_at'),
                    'last_update': call_info.get('last_update'),
                    'whatsapp_fallback': call_sid in comm_service.get_failed_calls()
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/procurement/analyze', methods=['POST'])
        def api_procurement_analyze():
            try:
                data = request.get_json() or {}
                company_id = data.get('company_id')
                
                companies = db.get_all_companies()
                
                if company_id:
                    # Analyze specific company
                    company = companies.get(company_id)
                    if not company:
                        return jsonify({'error': 'Company not found'}), 404
                    
                    low_stock_items = company.get_low_stock_items()
                    analysis = {
                        'company_id': company_id,
                        'company_name': company.name,
                        'low_stock_count': len(low_stock_items),
                        'critical_items': sum(1 for item in low_stock_items if item.get_urgency() == 'critical'),
                        'estimated_cost': sum(item.average_price * item.get_shortage() for item in low_stock_items)
                    }
                else:
                    # Analyze all companies
                    analysis = procurement_engine.analyze_procurement_requirements(companies)
                
                # Save analysis results
                analysis['timestamp'] = datetime.now().isoformat()
                
                return jsonify({
                    'success': True,
                    'analysis': analysis,
                    'message': 'Procurement analysis completed'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/procurement/generate-orders', methods=['POST'])
        def api_generate_orders():
            try:
                companies = db.get_all_companies()
                vendors = db.get_all_vendors()
                
                orders_generated = 0
                for company in companies.values():
                    low_stock_items = company.get_low_stock_items()
                    for item in low_stock_items:
                        if item.get_urgency() in ['critical', 'urgent']:
                            # Find suitable vendor
                            suitable_vendors = procurement_engine.find_suitable_vendors(item, vendors)
                            if suitable_vendors:
                                orders_generated += 1
                
                return jsonify({
                    'success': True,
                    'orders_count': orders_generated,
                    'message': f'{orders_generated} orders generated successfully'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/vendors/find/<company_id>')
        def api_find_vendors(company_id):
            try:
                company = db.get_company(company_id)
                if not company:
                    return jsonify({'error': 'Company not found'}), 404
                
                vendors = db.get_all_vendors()
                suitable_vendors = []
                
                if company.inventory:
                    for item in company.inventory.values():
                        item_vendors = procurement_engine.find_suitable_vendors(item, vendors)
                        suitable_vendors.extend(item_vendors)
                
                # Remove duplicates
                unique_vendors = list({v.vendor_id: v for v in suitable_vendors}.values())
                
                return jsonify({
                    'success': True,
                    'vendors_count': len(unique_vendors),
                    'vendors': [v.name for v in unique_vendors[:5]]
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/ai/recommendations', methods=['POST'])
        def api_ai_recommendations():
            try:
                companies = db.get_all_companies()
                vendors = db.get_all_vendors()
                
                recommendations = ai_service.generate_recommendations(companies, vendors)
                
                return jsonify({
                    'success': True,
                    'recommendations': recommendations,
                    'count': len(recommendations)
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/procurement/status')
        def api_procurement_status():
            try:
                companies = db.get_all_companies()
                
                critical_items = 0
                urgent_items = 0
                for company in companies.values():
                    low_stock = company.get_low_stock_items()
                    critical_items += sum(1 for item in low_stock if item.get_urgency() == 'critical')
                    urgent_items += sum(1 for item in low_stock if item.get_urgency() == 'urgent')
                
                return jsonify({
                    'critical_items': critical_items,
                    'urgent_items': urgent_items,
                    'companies_count': len(companies),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/companies')
        def api_companies():
            try:
                companies = db.get_all_companies()
                # Return list for API usage (form dropdowns, etc.)
                return jsonify([{
                    'company_id': company.company_id,
                    'name': company.name,
                    'industry': company.industry,
                    'contact_person': company.contact_person,
                    'phone': company.phone
                } for company in companies.values()])
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Webhook routes for Twilio
        @self.app.route('/webhook/voice', methods=['POST'])
        def webhook_voice():
            try:
                call_sid = request.form.get('CallSid', '')
                
                # Get company for this call
                active_calls = comm_service.get_active_calls()
                call_info = active_calls.get(call_sid, {})
                company_id = call_info.get('company_id')
                
                if company_id:
                    company = db.get_company(company_id)
                    if company:
                        greeting = ai_service.generate_company_greeting(company)
                    else:
                        greeting = "Hello! Thank you for answering our call."
                else:
                    greeting = "Hello! Thank you for answering our call."
                
                initial_question = "What laboratory supplies do you have available?"
                
                twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">{greeting}</Say>
    <Pause length="1"/>
    <Gather input="speech" 
            language="hi-IN" 
            speechTimeout="6" 
            timeout="12"
            action="/webhook/speech"
            method="POST">
        <Say voice="Polly.Aditi" language="hi-IN">{initial_question}</Say>
    </Gather>
    <Say voice="Polly.Aditi" language="hi-IN">
        Connection issue. Will call back later. Thank you!
    </Say>
    <Hangup/>
</Response>"""
                
                return Response(twiml_response, mimetype='text/xml')
                
            except Exception as e:
                print(f"❌ Voice webhook error: {e}")
                return Response(self.get_fallback_twiml(), mimetype='text/xml')
        
        @self.app.route('/webhook/speech', methods=['POST'])
        def webhook_speech():
            try:
                speech_result = request.form.get('SpeechResult', '')
                call_sid = request.form.get('CallSid', '')
                
                if not speech_result:
                    return Response(self.get_fallback_twiml(), mimetype='text/xml')
                
                print(f"📞 Speech: {speech_result}")
                
                # Get company context
                active_calls = comm_service.get_active_calls()
                call_info = active_calls.get(call_sid, {})
                company_id = call_info.get('company_id')
                company = db.get_company(company_id) if company_id else None
                
                # Extract information using AI
                extracted_data = ai_service.extract_vendor_information(speech_result, company)
                
                # Get conversation context
                context = comm_service.get_conversation_context(call_sid) or {
                    'stage': 'initial',
                    'turn_count': 0,
                    'items_discussed': [],
                    'prices_received': []
                }
                
                context['turn_count'] += 1
                
                # Update context with extracted data
                if extracted_data.get('items_mentioned'):
                    context['items_discussed'].extend(extracted_data['items_mentioned'])
                if extracted_data.get('prices'):
                    context['prices_received'].extend(extracted_data['prices'])
                
                # Generate AI response
                ai_response = ai_service.generate_intelligent_response(speech_result, context, company)
                
                # Update conversation context
                comm_service.update_conversation_context(call_sid, context)
                
                # Log conversation
                conversation_entry = ConversationEntry(
                    entry_id=str(uuid.uuid4()),
                    timestamp=datetime.now().isoformat(),
                    type='voice',
                    vendor_message=speech_result,
                    ai_response=ai_response,
                    extracted_data=extracted_data,
                    conversation_context=context,
                    call_sid=call_sid,
                    company_id=company_id
                )
                
                db.add_conversation(conversation_entry)
                
                # Determine if conversation should continue
                if context['turn_count'] >= 4 or len(context['items_discussed']) >= 3:
                    # End conversation
                    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">{ai_response}</Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" language="hi-IN">
        Thank you for the information. Our team will contact you soon. Good day!
    </Say>
    <Hangup/>
</Response>"""
                else:
                    # Continue conversation
                    follow_up = ai_service.generate_follow_up_question(context, company)
                    
                    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">{ai_response}</Say>
    <Pause length="1"/>
    <Gather input="speech" 
            language="hi-IN" 
            speechTimeout="6" 
            timeout="10"
            action="/webhook/speech"
            method="POST">
        <Say voice="Polly.Aditi" language="hi-IN">{follow_up}</Say>
    </Gather>
    <Say voice="Polly.Aditi" language="hi-IN">
        Thank you for your time. We will be in touch.
    </Say>
    <Hangup/>
</Response>"""
                
                # Emit real-time update
                self.socketio.emit('new_conversation', {
                    'call_sid': call_sid,
                    'vendor_message': speech_result,
                    'ai_response': ai_response,
                    'extracted_data': extracted_data
                })
                
                return Response(twiml_response, mimetype='text/xml')
                
            except Exception as e:
                print(f"❌ Speech webhook error: {e}")
                return Response(self.get_fallback_twiml(), mimetype='text/xml')
        
        @self.app.route('/webhook/status', methods=['POST'])
        def webhook_status():
            try:
                call_sid = request.form.get('CallSid', '')
                call_status = request.form.get('CallStatus', '')
                call_to = request.form.get('To', '')
                
                print(f"📞 Call {call_sid}: {call_status}")
                
                # Update call status
                comm_service.handle_call_status_update(call_sid, call_status, call_to)
                
                # Handle failed calls with WhatsApp fallback
                if call_status in ['no-answer', 'busy', 'failed', 'canceled']:
                    active_calls = comm_service.get_active_calls()
                    call_info = active_calls.get(call_sid, {})
                    company_id = call_info.get('company_id')
                    
                    if company_id:
                        company = db.get_company(company_id)
                        if company:
                            comm_service.initiate_whatsapp_fallback(call_sid, company)
                
                return "OK"
                
            except Exception as e:
                print(f"❌ Status webhook error: {e}")
                return "ERROR"
        
        @self.app.route('/webhook/whatsapp', methods=['POST'])
        def webhook_whatsapp():
            try:
                from_number = request.form.get('From', '').replace('whatsapp:', '')
                message_body = request.form.get('Body', '')
                
                if not from_number or not message_body:
                    return "OK"
                
                print(f"📱 WhatsApp from {from_number}: {message_body}")
                
                # Handle incoming message
                result = comm_service.handle_whatsapp_incoming(from_number, message_body)
                
                if result['success']:
                    # Get company context (use first company as default)
                    companies = db.get_all_companies()
                    company = next(iter(companies.values())) if companies else None
                    
                    # Extract information
                    extracted_data = ai_service.extract_vendor_information(message_body, company)
                    
                    # Get conversation context
                    context = comm_service.get_conversation_context(from_number) or {
                        'stage': 'initial',
                        'turn_count': 0,
                        'items_discussed': [],
                        'prices_received': []
                    }
                    
                    # Generate response
                    ai_response = ai_service.generate_intelligent_response(message_body, context, company)
                    
                    # Send response
                    comm_service.send_whatsapp_message(from_number, ai_response, company)
                    
                    # Log conversation
                    conversation_entry = ConversationEntry(
                        entry_id=str(uuid.uuid4()),
                        timestamp=datetime.now().isoformat(),
                        type='whatsapp',
                        vendor_message=message_body,
                        ai_response=ai_response,
                        extracted_data=extracted_data,
                        conversation_context=context,
                        vendor_number=from_number
                    )
                    
                    db.add_conversation(conversation_entry)
                    
                    # Emit real-time update
                    self.socketio.emit('new_conversation', {
                        'vendor_number': from_number,
                        'vendor_message': message_body,
                        'ai_response': ai_response,
                        'extracted_data': extracted_data
                    })
                
                return "OK"
                
            except Exception as e:
                print(f"❌ WhatsApp webhook error: {e}")
                return "ERROR"
        
        @self.app.route('/health')
        def health_check():
            try:
                return jsonify({
                    'status': 'healthy',
                    'database': 'connected',
                    'ai_service': ai_service.get_health_status(),
                    'communication': comm_service.get_statistics(),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
    
    def setup_error_handlers(self):
        """Setup error handlers"""
        
        @self.app.errorhandler(404)
        def not_found(error):
            return self.render_error_page("Page Not Found", "The requested page could not be found."), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return self.render_error_page("Internal Error", "An internal server error occurred."), 500
        
        @self.app.errorhandler(ProcurementError)
        def procurement_error(error):
            return self.render_error_page("Procurement Error", str(error)), 400
    
    def setup_socketio_events(self):
        """Setup SocketIO events for real-time updates"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print('Client connected')
            emit('status', {'status': 'connected'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('Client disconnected')
    
    def render_error_page(self, title, message):
        """Render error page"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title} - Procurement Platform</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 50px; text-align: center; }}
                .error-container {{ max-width: 600px; margin: 0 auto; }}
                h1 {{ color: #e74c3c; }}
                .btn {{ background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>{title}</h1>
                <p>{message}</p>
                <a href="/" class="btn">← Back to Dashboard</a>
            </div>
        </body>
        </html>
        """
    
    def get_fallback_twiml(self):
        """Get fallback TwiML response"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">
        Sorry, there was a technical issue. We will call you back. Thank you!
    </Say>
    <Hangup/>
</Response>"""
    
    def generate_alerts(self, procurement_analysis):
        """Generate system alerts"""
        alerts = []
        
        # Critical items alert
        if procurement_analysis['summary']['critical_items'] > 0:
            alerts.append({
                'type': 'danger',
                'icon': 'exclamation-triangle',
                'message': f"{procurement_analysis['summary']['critical_items']} critical items need immediate procurement"
            })
        
        # Budget alerts
        for company_id, budget_data in procurement_analysis['summary']['budget_utilization'].items():
            if budget_data['usage_percentage'] > 75:
                alerts.append({
                    'type': 'warning',
                    'icon': 'credit-card',
                    'message': f"{budget_data['company_name']} exceeding 75% budget utilization"
                })
        
        # Communication alerts
        comm_stats = comm_service.get_statistics()
        if not comm_stats['credentials_valid']:
            alerts.append({
                'type': 'danger',
                'icon': 'phone-slash',
                'message': 'Twilio credentials invalid - communication disabled'
            })
        
        return alerts
    
    def calculate_vendor_performance(self, vendor):
        """Calculate vendor performance score"""
        rating_score = (vendor.rating / 5.0) * 40
        success_rate_score = (vendor.get_success_rate() / 100.0) * 30
        
        # Response time score (lower is better)
        response_hours = {'12 hours': 12, '24 hours': 24, '48 hours': 48, '72 hours': 72}.get(vendor.response_time, 48)
        response_score = max(0, (72 - response_hours) / 72) * 20
        
        # Price competitiveness score
        price_scores = {'budget_friendly': 10, 'competitive': 7, 'premium': 4}
        price_score = price_scores.get(vendor.price_competitiveness, 5)
        
        return rating_score + success_rate_score + response_score + price_score
    
    def generate_analytics_data(self):
        """Generate analytics data for dashboard"""
        companies = db.get_all_companies()
        conversations = db.get_conversations(limit=100)
        
        # Conversation analytics
        conversation_types = {}
        vendor_responsiveness = {}
        
        for conv in conversations:
            conv_type = conv.type
            conversation_types[conv_type] = conversation_types.get(conv_type, 0) + 1
            
            if conv.vendor_number:
                vendor_responsiveness[conv.vendor_number] = True
        
        # Budget analytics
        budget_data = []
        for company in companies.values():
            low_stock = company.get_low_stock_items()
            estimated_cost = sum(item.average_price * max(0, item.minimum_required - item.current_stock) 
                               for item in low_stock)
            
            budget_data.append({
                'company': company.name,
                'budget': company.budget_monthly,
                'estimated_spend': estimated_cost,
                'utilization': (estimated_cost / company.budget_monthly * 100) if company.budget_monthly > 0 else 0
            })
        
        return {
            'conversation_types': conversation_types,
            'total_conversations': len(conversations),
            'responsive_vendors': len(vendor_responsiveness),
            'budget_analysis': budget_data,
            'total_companies': len(companies)
        }
    
    def get_webhook_base_url(self):
        """Get webhook base URL"""
        return self.ngrok_url or f"http://{self.host}:{self.port}"
    
    def set_ngrok_url(self, url):
        """Set ngrok URL for webhooks"""
        self.ngrok_url = url
        print(f"🔗 Webhook base URL set to: {url}")
    
    def run(self, debug=False):
        """Run the web server"""
        try:
            print(f"🚀 Starting Procurement Platform Web Server...")
            print(f"📊 Dashboard: http://{self.host}:{self.port}")
            
            self.socketio.run(self.app, 
                            host=self.host, 
                            port=self.port, 
                            debug=debug,
                            allow_unsafe_werkzeug=True)
        except Exception as e:
            print(f"❌ Failed to start web server: {e}")
            raise

# Global web server instance
web_server = ProcurementWebServer() 