// Enhanced JavaScript for Tabbed Property Doctype
// Copyright (c) 2025, Farah and contributors

frappe.ui.form.on('Property', {
    refresh: function(frm) {
        // Load property performance dashboard
        load_property_performance_dashboard(frm);
        
        // Load management summary
        load_management_summary(frm);
        
        // Load financial analysis
        load_financial_analysis(frm);
        
        // Load location map
        load_location_map(frm);
        
        // Load property images
        load_property_images(frm);
        
        // Update tab badges
        update_property_tab_badges(frm);
        
        // Add custom buttons
        add_property_management_buttons(frm);
    },
    
    onload: function(frm) {
        // Initialize tab content
        initialize_property_tab_content(frm);
    },
    
    property_status: function(frm) {
        // Update tab badges when status changes
        update_property_tab_badges(frm);
    },
    
    total_units: function(frm) {
        // Recalculate occupancy rate when units change
        calculate_occupancy_rate(frm);
    },
    
    occupied_units: function(frm) {
        // Recalculate occupancy rate when occupied units change
        calculate_occupancy_rate(frm);
    }
});

function load_property_performance_dashboard(frm) {
    if (!frm.doc.name) return;
    
    frappe.call({
        method: 'property_manager.utils.reporting.get_property_performance',
        args: {
            property: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                render_property_performance(frm, r.message);
            }
        }
    });
}

function render_property_performance(frm, data) {
    let html = `
        <div class="property-performance-dashboard">
            <div class="row">
                <div class="col-md-3">
                    <div class="card text-center bg-primary text-white">
                        <div class="card-body">
                            <h4 class="card-title">${data.total_units || 0}</h4>
                            <p class="card-text">Total Units</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center bg-success text-white">
                        <div class="card-body">
                            <h4 class="card-title">${data.occupied_units || 0}</h4>
                            <p class="card-text">Occupied</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center bg-info text-white">
                        <div class="card-body">
                            <h4 class="card-title">${data.available_units || 0}</h4>
                            <p class="card-text">Available</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center bg-warning text-white">
                        <div class="card-body">
                            <h4 class="card-title">${(data.occupancy_rate || 0).toFixed(1)}%</h4>
                            <p class="card-text">Occupancy Rate</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Monthly Revenue</div>
                        <div class="card-body">
                            <h5 class="card-title">${format_currency(data.monthly_revenue || 0)}</h5>
                            <p class="card-text">Current monthly rental income</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Annual Revenue</div>
                        <div class="card-body">
                            <h5 class="card-title">${format_currency(data.annual_revenue || 0)}</h5>
                            <p class="card-text">Projected annual rental income</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="progress" style="height: 25px;">
                        <div class="progress-bar bg-success" role="progressbar" 
                             style="width: ${data.occupancy_rate || 0}%" 
                             aria-valuenow="${data.occupancy_rate || 0}" 
                             aria-valuemin="0" aria-valuemax="100">
                            ${(data.occupancy_rate || 0).toFixed(1)}% Occupied
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.property_performance_html.$wrapper.html(html);
}

function load_management_summary(frm) {
    let html = `
        <div class="management-summary-dashboard">
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Property Manager</div>
                        <div class="card-body">
                            <h6 class="card-title">${frm.doc.property_manager || 'Not Assigned'}</h6>
                            <p class="card-text">
                                <i class="fa fa-envelope"></i> ${frm.doc.manager_email || 'No email'}<br>
                                <i class="fa fa-phone"></i> ${frm.doc.manager_phone || 'No phone'}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Property Owner</div>
                        <div class="card-body">
                            <h6 class="card-title">${frm.doc.owner_name || 'Not Specified'}</h6>
                            <p class="card-text">
                                <i class="fa fa-envelope"></i> ${frm.doc.owner_email || 'No email'}<br>
                                <i class="fa fa-phone"></i> ${frm.doc.owner_contact || 'No phone'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="alert alert-info">
                        <strong>Management Structure:</strong>
                        The property manager handles day-to-day operations while the owner maintains overall ownership and strategic decisions.
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.management_summary_html.$wrapper.html(html);
}

function load_financial_analysis(frm) {
    let purchase_price = frm.doc.purchase_price || 0;
    let current_value = frm.doc.current_market_value || 0;
    let appreciation = current_value - purchase_price;
    let appreciation_percent = purchase_price > 0 ? (appreciation / purchase_price * 100) : 0;
    
    let html = `
        <div class="financial-analysis-dashboard">
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Purchase Information</div>
                        <div class="card-body">
                            <h5 class="card-title">${format_currency(purchase_price)}</h5>
                            <p class="card-text">
                                Purchase Price<br>
                                <small class="text-muted">Date: ${frm.doc.purchase_date || 'Not specified'}</small>
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Current Value</div>
                        <div class="card-body">
                            <h5 class="card-title">${format_currency(current_value)}</h5>
                            <p class="card-text">
                                Market Value<br>
                                <small class="text-muted">Last Valuation: ${frm.doc.last_valuation_date || 'Not specified'}</small>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Appreciation</div>
                        <div class="card-body">
                            <h5 class="card-title ${appreciation >= 0 ? 'text-success' : 'text-danger'}">
                                ${format_currency(appreciation)}
                            </h5>
                            <p class="card-text">
                                Total Appreciation<br>
                                <small class="text-muted">${appreciation_percent.toFixed(2)}% change</small>
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Investment Performance</div>
                        <div class="card-body">
                            <h5 class="card-title ${appreciation_percent >= 0 ? 'text-success' : 'text-danger'}">
                                ${appreciation_percent.toFixed(2)}%
                            </h5>
                            <p class="card-text">
                                Return on Investment<br>
                                <small class="text-muted">Since purchase</small>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.financial_analysis_html.$wrapper.html(html);
}

function load_location_map(frm) {
    let address = `${frm.doc.address || ''}, ${frm.doc.city || ''}, ${frm.doc.country || ''}`;
    
    let html = `
        <div class="location-map-dashboard">
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Property Location</div>
                        <div class="card-body">
                            <p><strong>Address:</strong> ${address}</p>
                            <div class="alert alert-info">
                                <i class="fa fa-map-marker"></i> 
                                Interactive map integration can be added here using Google Maps or similar service.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.location_map_html.$wrapper.html(html);
}

function load_property_images(frm) {
    let html = `
        <div class="property-images-dashboard">
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Property Gallery</div>
                        <div class="card-body">
                            <div class="alert alert-info">
                                <i class="fa fa-camera"></i> 
                                Property image gallery can be implemented here with file upload functionality.
                            </div>
                            <button type="button" class="btn btn-primary" onclick="upload_property_images('${frm.doc.name}')">
                                <i class="fa fa-upload"></i> Upload Images
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.property_images_html.$wrapper.html(html);
}

function update_property_tab_badges(frm) {
    setTimeout(() => {
        // Basic Information tab
        let basic_tab = $('a[data-fieldname="tab_break_basic"]');
        if (basic_tab.length) {
            let status_badge = '';
            switch(frm.doc.property_status) {
                case 'Active':
                    status_badge = '<span class="badge badge-success">Active</span>';
                    break;
                case 'Inactive':
                    status_badge = '<span class="badge badge-secondary">Inactive</span>';
                    break;
                case 'Under Renovation':
                    status_badge = '<span class="badge badge-warning">Renovation</span>';
                    break;
                case 'For Sale':
                    status_badge = '<span class="badge badge-info">For Sale</span>';
                    break;
                default:
                    status_badge = '<span class="badge badge-light">Unknown</span>';
            }
            basic_tab.html(`Basic Information ${status_badge}`);
        }
        
        // Financial Information tab
        let financial_tab = $('a[data-fieldname="tab_break_financial"]');
        if (financial_tab.length) {
            let has_financial_data = frm.doc.purchase_price || frm.doc.current_market_value;
            let badge_class = has_financial_data ? 'badge-success' : 'badge-warning';
            let badge_text = has_financial_data ? 'Complete' : 'Incomplete';
            financial_tab.html(`Financial Information <span class="badge ${badge_class}">${badge_text}</span>`);
        }
        
        // Management tab
        let management_tab = $('a[data-fieldname="tab_break_management"]');
        if (management_tab.length) {
            let has_manager = frm.doc.property_manager;
            let badge_class = has_manager ? 'badge-success' : 'badge-warning';
            let badge_text = has_manager ? 'Assigned' : 'Unassigned';
            management_tab.html(`Management & Ownership <span class="badge ${badge_class}">${badge_text}</span>`);
        }
        
        // Location tab
        let location_tab = $('a[data-fieldname="tab_break_location"]');
        if (location_tab.length) {
            let occupancy_rate = frm.doc.occupancy_rate || 0;
            let badge_class = occupancy_rate >= 80 ? 'badge-success' : occupancy_rate >= 50 ? 'badge-warning' : 'badge-danger';
            location_tab.html(`Location Details <span class="badge ${badge_class}">${occupancy_rate.toFixed(0)}% Occupied</span>`);
        }
    }, 100);
}

function add_property_management_buttons(frm) {
    if (frm.doc.name) {
        // View Units Button
        frm.add_custom_button(__('View Units'), function() {
            frappe.route_options = {"property": frm.doc.name};
            frappe.set_route("List", "Rental Unit");
        }, __('Property'));
        
        // View Contracts Button
        frm.add_custom_button(__('View Contracts'), function() {
            frappe.route_options = {"property": frm.doc.name};
            frappe.set_route("List", "Rental Contract");
        }, __('Property'));
        
        // Property Report Button
        frm.add_custom_button(__('Property Report'), function() {
            show_property_report(frm);
        }, __('Reports'));
        
        // Financial Analysis Button
        frm.add_custom_button(__('Financial Analysis'), function() {
            show_financial_analysis_report(frm);
        }, __('Reports'));
    }
}

function calculate_occupancy_rate(frm) {
    if (frm.doc.total_units && frm.doc.total_units > 0) {
        let occupancy_rate = (frm.doc.occupied_units || 0) / frm.doc.total_units * 100;
        frm.set_value('occupancy_rate', occupancy_rate);
    }
}

function initialize_property_tab_content(frm) {
    setTimeout(() => {
        if (frm.doc.name) {
            load_property_performance_dashboard(frm);
            load_management_summary(frm);
            load_financial_analysis(frm);
            load_location_map(frm);
            load_property_images(frm);
        }
    }, 500);
}

// Global functions
window.upload_property_images = function(property_name) {
    frappe.msgprint('Property image upload functionality can be implemented here.');
};

function show_property_report(frm) {
    frappe.msgprint('Property report functionality can be implemented here.');
}

function show_financial_analysis_report(frm) {
    frappe.msgprint('Financial analysis report functionality can be implemented here.');
}

// Utility functions
function format_currency(value) {
    return frappe.format(value, {fieldtype: 'Currency'});
}

// CSS for enhanced styling
frappe.ready(function() {
    $('head').append(`
        <style>
            .property-performance-dashboard .card,
            .management-summary-dashboard .card,
            .financial-analysis-dashboard .card,
            .location-map-dashboard .card,
            .property-images-dashboard .card {
                margin-bottom: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border: none;
            }
            
            .property-performance-dashboard .card-title,
            .financial-analysis-dashboard .card-title {
                font-size: 1.5em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .badge {
                font-size: 0.75em;
                margin-left: 5px;
            }
            
            .progress {
                background-color: #e9ecef;
            }
            
            .alert {
                border-radius: 5px;
                margin-bottom: 15px;
            }
            
            .card-header {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                font-weight: bold;
            }
        </style>
    `);
});

