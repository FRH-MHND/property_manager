// Enhanced JavaScript for Tabbed Rental Unit Doctype
// Copyright (c) 2025, Farah and contributors

frappe.ui.form.on('Rental Unit', {
    refresh: function(frm) {
        // Load unit features dashboard
        load_unit_features_dashboard(frm);
        
        // Load rental rates analysis
        load_rental_rates_analysis(frm);
        
        // Load financial summary
        load_unit_financial_summary(frm);
        
        // Load lease status
        load_lease_status_dashboard(frm);
        
        // Load lease history
        load_lease_history_dashboard(frm);
        
        // Load maintenance schedule
        load_maintenance_schedule_dashboard(frm);
        
        // Load maintenance history
        load_maintenance_history_dashboard(frm);
        
        // Load unit gallery
        load_unit_gallery_dashboard(frm);
        
        // Update tab badges
        update_rental_unit_tab_badges(frm);
        
        // Add custom buttons
        add_rental_unit_management_buttons(frm);
    },
    
    onload: function(frm) {
        // Initialize tab content
        initialize_rental_unit_tab_content(frm);
    },
    
    unit_status: function(frm) {
        // Update tab badges when status changes
        update_rental_unit_tab_badges(frm);
    },
    
    monthly_rent: function(frm) {
        // Recalculate financial metrics when rent changes
        load_unit_financial_summary(frm);
        load_rental_rates_analysis(frm);
    },
    
    maintenance_status: function(frm) {
        // Update maintenance dashboard when status changes
        load_maintenance_schedule_dashboard(frm);
        update_rental_unit_tab_badges(frm);
    }
});

function load_unit_features_dashboard(frm) {
    let features_html = generate_unit_features_html(frm);
    
    let html = `
        <div class="unit-features-dashboard">
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Unit Specifications</div>
                        <div class="card-body">
                            ${features_html}
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Unit Status</div>
                        <div class="card-body">
                            <h5 class="card-title">
                                <span class="badge badge-${get_unit_status_color(frm.doc.unit_status)}">
                                    ${frm.doc.unit_status || 'Unknown'}
                                </span>
                            </h5>
                            <p class="card-text">
                                <strong>Furnished:</strong> ${frm.doc.furnished_status || 'Not specified'}<br>
                                <strong>Square Footage:</strong> ${frm.doc.square_footage || 'Not specified'} sq ft
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Unit Amenities</div>
                        <div class="card-body">
                            <p class="card-text">
                                ${frm.doc.amenities || 'No amenities listed'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.unit_features_html.$wrapper.html(html);
}

function load_rental_rates_analysis(frm) {
    let monthly_rent = frm.doc.monthly_rent || 0;
    let weekly_rent = monthly_rent * 12 / 52;
    let daily_rent = monthly_rent / 30;
    let annual_rent = monthly_rent * 12;
    
    // Calculate per square foot rates
    let rent_per_sqft = frm.doc.square_footage ? monthly_rent / frm.doc.square_footage : 0;
    
    let html = `
        <div class="rental-rates-dashboard">
            <div class="row">
                <div class="col-md-3">
                    <div class="card text-center bg-primary text-white">
                        <div class="card-body">
                            <h5 class="card-title">${format_currency(monthly_rent)}</h5>
                            <p class="card-text">Monthly Rent</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center bg-info text-white">
                        <div class="card-body">
                            <h5 class="card-title">${format_currency(weekly_rent)}</h5>
                            <p class="card-text">Weekly Rent</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center bg-success text-white">
                        <div class="card-body">
                            <h5 class="card-title">${format_currency(daily_rent)}</h5>
                            <p class="card-text">Daily Rent</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center bg-warning text-white">
                        <div class="card-body">
                            <h5 class="card-title">${format_currency(annual_rent)}</h5>
                            <p class="card-text">Annual Rent</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Rate Analysis</div>
                        <div class="card-body">
                            <p class="card-text">
                                <strong>Per Square Foot:</strong> ${format_currency(rent_per_sqft)}/month<br>
                                <strong>Security Deposit:</strong> ${format_currency(frm.doc.security_deposit || 0)}<br>
                                <strong>Late Fee:</strong> ${format_currency(frm.doc.late_fee_amount || 0)}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Market Comparison</div>
                        <div class="card-body">
                            <div class="alert alert-info">
                                <i class="fa fa-chart-line"></i> 
                                Market rate comparison can be implemented here.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.rental_rates_html.$wrapper.html(html);
}

function load_unit_financial_summary(frm) {
    let monthly_rent = frm.doc.monthly_rent || 0;
    let annual_income = monthly_rent * 12;
    let security_deposit = frm.doc.security_deposit || 0;
    let total_fees = frm.doc.late_fee_amount || 0;
    
    // Calculate potential income based on occupancy
    let occupancy_months = 12; // Assume full occupancy for now
    let potential_income = monthly_rent * occupancy_months;
    
    let html = `
        <div class="unit-financial-summary">
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Income Potential</div>
                        <div class="card-body">
                            <h5 class="card-title">${format_currency(annual_income)}</h5>
                            <p class="card-text">
                                Annual Income Potential<br>
                                <small class="text-muted">Based on ${format_currency(monthly_rent)}/month</small>
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Security & Fees</div>
                        <div class="card-body">
                            <h5 class="card-title">${format_currency(security_deposit)}</h5>
                            <p class="card-text">
                                Security Deposit<br>
                                <small class="text-muted">Late Fee: ${format_currency(total_fees)}</small>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Financial Performance</div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-4">
                                    <h6>Monthly Income</h6>
                                    <h4 class="text-success">${format_currency(monthly_rent)}</h4>
                                </div>
                                <div class="col-md-4">
                                    <h6>Quarterly Income</h6>
                                    <h4 class="text-info">${format_currency(monthly_rent * 3)}</h4>
                                </div>
                                <div class="col-md-4">
                                    <h6>Annual Income</h6>
                                    <h4 class="text-primary">${format_currency(annual_income)}</h4>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.financial_summary_html.$wrapper.html(html);
}

function load_lease_status_dashboard(frm) {
    let lease_status = get_lease_status(frm);
    let days_remaining = calculate_days_remaining(frm.doc.lease_end_date);
    
    let html = `
        <div class="lease-status-dashboard">
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Current Lease</div>
                        <div class="card-body">
                            <h5 class="card-title">
                                <span class="badge badge-${lease_status.color}">
                                    ${lease_status.status}
                                </span>
                            </h5>
                            <p class="card-text">
                                <strong>Tenant:</strong> ${frm.doc.current_tenant || 'No current tenant'}<br>
                                <strong>Start Date:</strong> ${frm.doc.lease_start_date || 'Not specified'}<br>
                                <strong>End Date:</strong> ${frm.doc.lease_end_date || 'Not specified'}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Lease Timeline</div>
                        <div class="card-body">
                            <h5 class="card-title">${days_remaining.value}</h5>
                            <p class="card-text">
                                ${days_remaining.label}<br>
                                <small class="text-muted">${days_remaining.description}</small>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Lease Actions</div>
                        <div class="card-body">
                            <button type="button" class="btn btn-primary btn-sm" onclick="create_new_lease('${frm.doc.name}')">
                                <i class="fa fa-plus"></i> Create New Lease
                            </button>
                            <button type="button" class="btn btn-warning btn-sm ml-2" onclick="renew_lease('${frm.doc.name}')">
                                <i class="fa fa-refresh"></i> Renew Lease
                            </button>
                            <button type="button" class="btn btn-danger btn-sm ml-2" onclick="terminate_lease('${frm.doc.name}')">
                                <i class="fa fa-times"></i> Terminate Lease
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.lease_status_html.$wrapper.html(html);
}

function load_lease_history_dashboard(frm) {
    let html = `
        <div class="lease-history-dashboard">
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Lease History</div>
                        <div class="card-body">
                            <div class="alert alert-info">
                                <i class="fa fa-history"></i> 
                                Lease history functionality can be implemented here to show past tenants and lease terms.
                            </div>
                            <button type="button" class="btn btn-info btn-sm" onclick="view_lease_history('${frm.doc.name}')">
                                <i class="fa fa-list"></i> View Full History
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.lease_history_html.$wrapper.html(html);
}

function load_maintenance_schedule_dashboard(frm) {
    let maintenance_status_color = get_maintenance_status_color(frm.doc.maintenance_status);
    let next_maintenance_days = calculate_days_until(frm.doc.next_maintenance_date);
    
    let html = `
        <div class="maintenance-schedule-dashboard">
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Maintenance Status</div>
                        <div class="card-body">
                            <h5 class="card-title">
                                <span class="badge badge-${maintenance_status_color}">
                                    ${frm.doc.maintenance_status || 'Unknown'}
                                </span>
                            </h5>
                            <p class="card-text">
                                <strong>Last Maintenance:</strong> ${frm.doc.last_maintenance_date || 'Not recorded'}<br>
                                <strong>Next Scheduled:</strong> ${frm.doc.next_maintenance_date || 'Not scheduled'}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Next Maintenance</div>
                        <div class="card-body">
                            <h5 class="card-title">${next_maintenance_days.value}</h5>
                            <p class="card-text">
                                ${next_maintenance_days.label}<br>
                                <small class="text-muted">${next_maintenance_days.description}</small>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Maintenance Actions</div>
                        <div class="card-body">
                            <button type="button" class="btn btn-primary btn-sm" onclick="schedule_maintenance('${frm.doc.name}')">
                                <i class="fa fa-calendar"></i> Schedule Maintenance
                            </button>
                            <button type="button" class="btn btn-success btn-sm ml-2" onclick="complete_maintenance('${frm.doc.name}')">
                                <i class="fa fa-check"></i> Mark Complete
                            </button>
                            <button type="button" class="btn btn-warning btn-sm ml-2" onclick="request_maintenance('${frm.doc.name}')">
                                <i class="fa fa-wrench"></i> Request Maintenance
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.maintenance_schedule_html.$wrapper.html(html);
}

function load_maintenance_history_dashboard(frm) {
    let html = `
        <div class="maintenance-history-dashboard">
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Maintenance History</div>
                        <div class="card-body">
                            <div class="alert alert-info">
                                <i class="fa fa-wrench"></i> 
                                Maintenance history functionality can be implemented here to track all maintenance activities.
                            </div>
                            <button type="button" class="btn btn-info btn-sm" onclick="view_maintenance_history('${frm.doc.name}')">
                                <i class="fa fa-list"></i> View Full History
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.maintenance_history_html.$wrapper.html(html);
}

function load_unit_gallery_dashboard(frm) {
    let html = `
        <div class="unit-gallery-dashboard">
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Unit Gallery</div>
                        <div class="card-body">
                            <div class="alert alert-info">
                                <i class="fa fa-camera"></i> 
                                Unit image gallery can be implemented here with file upload functionality.
                            </div>
                            <button type="button" class="btn btn-primary btn-sm" onclick="upload_unit_images('${frm.doc.name}')">
                                <i class="fa fa-upload"></i> Upload Images
                            </button>
                            <button type="button" class="btn btn-secondary btn-sm ml-2" onclick="view_unit_gallery('${frm.doc.name}')">
                                <i class="fa fa-images"></i> View Gallery
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.unit_gallery_html.$wrapper.html(html);
}

function update_rental_unit_tab_badges(frm) {
    setTimeout(() => {
        // Specifications tab
        let specs_tab = $('a[data-fieldname="tab_break_specifications"]');
        if (specs_tab.length) {
            let unit_status_badge = `<span class="badge badge-${get_unit_status_color(frm.doc.unit_status)}">${frm.doc.unit_status || 'Unknown'}</span>`;
            specs_tab.html(`Specifications ${unit_status_badge}`);
        }
        
        // Financial Terms tab
        let financial_tab = $('a[data-fieldname="tab_break_financial"]');
        if (financial_tab.length) {
            let has_rent = frm.doc.monthly_rent > 0;
            let badge_class = has_rent ? 'badge-success' : 'badge-warning';
            let badge_text = has_rent ? format_currency(frm.doc.monthly_rent) : 'No Rent Set';
            financial_tab.html(`Financial Terms <span class="badge ${badge_class}">${badge_text}</span>`);
        }
        
        // Lease Information tab
        let lease_tab = $('a[data-fieldname="tab_break_lease"]');
        if (lease_tab.length) {
            let lease_status = get_lease_status(frm);
            lease_tab.html(`Lease Information <span class="badge badge-${lease_status.color}">${lease_status.status}</span>`);
        }
        
        // Maintenance tab
        let maintenance_tab = $('a[data-fieldname="tab_break_maintenance"]');
        if (maintenance_tab.length) {
            let maintenance_color = get_maintenance_status_color(frm.doc.maintenance_status);
            maintenance_tab.html(`Maintenance <span class="badge badge-${maintenance_color}">${frm.doc.maintenance_status || 'Unknown'}</span>`);
        }
    }, 100);
}

function add_rental_unit_management_buttons(frm) {
    if (frm.doc.name) {
        // Create Contract Button
        frm.add_custom_button(__('Create Contract'), function() {
            create_rental_contract(frm);
        }, __('Unit'));
        
        // View Contracts Button
        frm.add_custom_button(__('View Contracts'), function() {
            frappe.route_options = {"rental_unit": frm.doc.name};
            frappe.set_route("List", "Rental Contract");
        }, __('Unit'));
        
        // Unit Report Button
        frm.add_custom_button(__('Unit Report'), function() {
            show_unit_report(frm);
        }, __('Reports'));
        
        // Maintenance Request Button
        frm.add_custom_button(__('Maintenance Request'), function() {
            create_maintenance_request(frm);
        }, __('Maintenance'));
    }
}

function initialize_rental_unit_tab_content(frm) {
    setTimeout(() => {
        if (frm.doc.name) {
            load_unit_features_dashboard(frm);
            load_rental_rates_analysis(frm);
            load_unit_financial_summary(frm);
            load_lease_status_dashboard(frm);
            load_lease_history_dashboard(frm);
            load_maintenance_schedule_dashboard(frm);
            load_maintenance_history_dashboard(frm);
            load_unit_gallery_dashboard(frm);
        }
    }, 500);
}

// Utility functions
function generate_unit_features_html(frm) {
    let features = [];
    
    if (frm.doc.bedrooms) features.push(`${frm.doc.bedrooms} Bedroom${frm.doc.bedrooms > 1 ? 's' : ''}`);
    if (frm.doc.bathrooms) features.push(`${frm.doc.bathrooms} Bathroom${frm.doc.bathrooms > 1 ? 's' : ''}`);
    if (frm.doc.parking_spaces) features.push(`${frm.doc.parking_spaces} Parking Space${frm.doc.parking_spaces > 1 ? 's' : ''}`);
    
    return features.length > 0 ? features.join('<br>') : 'No specific features listed';
}

function get_unit_status_color(status) {
    switch(status) {
        case 'Available': return 'success';
        case 'Occupied': return 'primary';
        case 'Maintenance': return 'warning';
        case 'Renovation': return 'info';
        case 'Out of Service': return 'danger';
        default: return 'secondary';
    }
}

function get_lease_status(frm) {
    if (!frm.doc.current_tenant) {
        return {status: 'Vacant', color: 'warning'};
    }
    
    if (frm.doc.lease_end_date) {
        let end_date = new Date(frm.doc.lease_end_date);
        let today = new Date();
        
        if (end_date < today) {
            return {status: 'Expired', color: 'danger'};
        } else {
            return {status: 'Active', color: 'success'};
        }
    }
    
    return {status: 'Occupied', color: 'primary'};
}

function get_maintenance_status_color(status) {
    switch(status) {
        case 'Good': return 'success';
        case 'Needs Attention': return 'warning';
        case 'Scheduled': return 'info';
        case 'In Progress': return 'primary';
        case 'Completed': return 'success';
        default: return 'secondary';
    }
}

function calculate_days_remaining(end_date) {
    if (!end_date) {
        return {value: 'N/A', label: 'No end date', description: 'Lease end date not specified'};
    }
    
    let end = new Date(end_date);
    let today = new Date();
    let diff = Math.ceil((end - today) / (1000 * 60 * 60 * 24));
    
    if (diff < 0) {
        return {value: Math.abs(diff), label: 'Days Overdue', description: 'Lease has expired'};
    } else if (diff === 0) {
        return {value: 'Today', label: 'Expires Today', description: 'Lease expires today'};
    } else {
        return {value: diff, label: 'Days Remaining', description: 'Until lease expiration'};
    }
}

function calculate_days_until(target_date) {
    if (!target_date) {
        return {value: 'N/A', label: 'Not scheduled', description: 'No date specified'};
    }
    
    let target = new Date(target_date);
    let today = new Date();
    let diff = Math.ceil((target - today) / (1000 * 60 * 60 * 24));
    
    if (diff < 0) {
        return {value: Math.abs(diff), label: 'Days Overdue', description: 'Past due date'};
    } else if (diff === 0) {
        return {value: 'Today', label: 'Due Today', description: 'Scheduled for today'};
    } else {
        return {value: diff, label: 'Days Until', description: 'Until scheduled date'};
    }
}

// Global functions
window.create_new_lease = function(unit_name) {
    frappe.new_doc('Rental Contract', {rental_unit: unit_name});
};

window.renew_lease = function(unit_name) {
    frappe.msgprint('Lease renewal functionality can be implemented here.');
};

window.terminate_lease = function(unit_name) {
    frappe.msgprint('Lease termination functionality can be implemented here.');
};

window.schedule_maintenance = function(unit_name) {
    frappe.msgprint('Maintenance scheduling functionality can be implemented here.');
};

window.complete_maintenance = function(unit_name) {
    frappe.msgprint('Maintenance completion functionality can be implemented here.');
};

window.request_maintenance = function(unit_name) {
    frappe.msgprint('Maintenance request functionality can be implemented here.');
};

window.upload_unit_images = function(unit_name) {
    frappe.msgprint('Unit image upload functionality can be implemented here.');
};

window.view_unit_gallery = function(unit_name) {
    frappe.msgprint('Unit gallery view functionality can be implemented here.');
};

window.view_lease_history = function(unit_name) {
    frappe.msgprint('Lease history functionality can be implemented here.');
};

window.view_maintenance_history = function(unit_name) {
    frappe.msgprint('Maintenance history functionality can be implemented here.');
};

function create_rental_contract(frm) {
    frappe.new_doc('Rental Contract', {
        rental_unit: frm.doc.name,
        property: frm.doc.property
    });
}

function show_unit_report(frm) {
    frappe.msgprint('Unit report functionality can be implemented here.');
}

function create_maintenance_request(frm) {
    frappe.msgprint('Maintenance request creation functionality can be implemented here.');
}

function format_currency(value) {
    return frappe.format(value, {fieldtype: 'Currency'});
}

// CSS for enhanced styling
frappe.ready(function() {
    $('head').append(`
        <style>
            .unit-features-dashboard .card,
            .rental-rates-dashboard .card,
            .unit-financial-summary .card,
            .lease-status-dashboard .card,
            .lease-history-dashboard .card,
            .maintenance-schedule-dashboard .card,
            .maintenance-history-dashboard .card,
            .unit-gallery-dashboard .card {
                margin-bottom: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border: none;
            }
            
            .rental-rates-dashboard .card-title,
            .unit-financial-summary .card-title {
                font-size: 1.2em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .badge {
                font-size: 0.75em;
                margin-left: 5px;
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
            
            .btn-sm {
                margin-right: 5px;
                margin-bottom: 5px;
            }
        </style>
    `);
});

