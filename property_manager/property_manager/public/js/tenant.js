// Enhanced JavaScript for Tabbed Tenant Doctype
// Copyright (c) 2025, Farah and contributors

frappe.ui.form.on('Tenant', {
    refresh: function(frm) {
        // Load tenant summary dashboard
        load_tenant_summary_dashboard(frm);
        
        // Load employment verification
        load_employment_verification(frm);
        
        // Load business summary (for corporate tenants)
        load_business_summary(frm);
        
        // Load address map
        load_address_map(frm);
        
        // Load references dashboard
        load_references_dashboard(frm);
        
        // Update tab badges
        update_tenant_tab_badges(frm);
        
        // Add custom buttons
        add_tenant_management_buttons(frm);
        
        // Set up conditional field visibility
        setup_conditional_fields(frm);
    },
    
    onload: function(frm) {
        // Initialize tab content
        initialize_tenant_tab_content(frm);
    },
    
    tenant_type: function(frm) {
        // Update tab visibility and badges when tenant type changes
        setup_conditional_fields(frm);
        update_tenant_tab_badges(frm);
    },
    
    first_name: function(frm) {
        // Auto-generate full name for individual tenants
        if (frm.doc.tenant_type === 'Individual') {
            generate_full_name(frm);
        }
    },
    
    last_name: function(frm) {
        // Auto-generate full name for individual tenants
        if (frm.doc.tenant_type === 'Individual') {
            generate_full_name(frm);
        }
    },
    
    annual_income: function(frm) {
        // Auto-calculate monthly income
        if (frm.doc.annual_income) {
            frm.set_value('monthly_income', frm.doc.annual_income / 12);
        }
    },
    
    background_check_status: function(frm) {
        // Update tab badges when background check status changes
        update_tenant_tab_badges(frm);
    }
});

function load_tenant_summary_dashboard(frm) {
    let tenant_name = frm.doc.tenant_type === 'Individual' ? 
        (frm.doc.full_name || `${frm.doc.first_name || ''} ${frm.doc.last_name || ''}`.trim()) :
        frm.doc.company_name;
    
    let contact_info = `${frm.doc.email || 'No email'} | ${frm.doc.phone || 'No phone'}`;
    
    let financial_info = '';
    if (frm.doc.tenant_type === 'Individual') {
        financial_info = `
            <strong>Annual Income:</strong> ${format_currency(frm.doc.annual_income || 0)}<br>
            <strong>Credit Score:</strong> ${frm.doc.credit_score || 'Not provided'}
        `;
    } else {
        financial_info = `
            <strong>Annual Revenue:</strong> ${format_currency(frm.doc.annual_revenue || 0)}<br>
            <strong>Credit Rating:</strong> ${frm.doc.credit_rating || 'Not provided'}
        `;
    }
    
    let background_check_color = get_background_check_color(frm.doc.background_check_status);
    
    let html = `
        <div class="tenant-summary-dashboard">
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Tenant Overview</div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-4">
                                    <h5 class="card-title">${tenant_name || 'Unnamed Tenant'}</h5>
                                    <p class="card-text">
                                        <strong>Type:</strong> ${frm.doc.tenant_type}<br>
                                        <strong>Contact:</strong> ${contact_info}
                                    </p>
                                </div>
                                <div class="col-md-4">
                                    <h6>Financial Information</h6>
                                    <p class="card-text">${financial_info}</p>
                                </div>
                                <div class="col-md-4">
                                    <h6>Background Check</h6>
                                    <p class="card-text">
                                        <span class="badge badge-${background_check_color}">
                                            ${frm.doc.background_check_status || 'Pending'}
                                        </span>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Current Address</div>
                        <div class="card-body">
                            <p class="card-text">
                                ${frm.doc.current_address || 'Not provided'}<br>
                                ${frm.doc.city || ''} ${frm.doc.state || ''} ${frm.doc.postal_code || ''}<br>
                                ${frm.doc.country || ''}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Emergency Contact</div>
                        <div class="card-body">
                            <p class="card-text">
                                <strong>${frm.doc.emergency_contact_name || 'Not provided'}</strong><br>
                                ${frm.doc.emergency_contact_relationship || ''}<br>
                                ${frm.doc.emergency_contact_phone || 'No phone'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // HTML field has been replaced with practical fields
    // Dashboard content now handled by standard form fields
}

function load_employment_verification(frm) {
    if (frm.doc.tenant_type !== 'Individual') return;
    
    let employment_status_color = get_employment_status_color(frm.doc.employment_status);
    let income_verification = verify_income_adequacy(frm.doc.annual_income);
    
    let html = `
        <div class="employment-verification-dashboard">
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Employment Status</div>
                        <div class="card-body">
                            <h6 class="card-title">
                                <span class="badge badge-${employment_status_color}">
                                    ${frm.doc.employment_status || 'Not specified'}
                                </span>
                            </h6>
                            <p class="card-text">
                                <strong>Employer:</strong> ${frm.doc.employer || 'Not provided'}<br>
                                <strong>Occupation:</strong> ${frm.doc.occupation || 'Not provided'}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Income Verification</div>
                        <div class="card-body">
                            <h6 class="card-title">${format_currency(frm.doc.annual_income || 0)}</h6>
                            <p class="card-text">
                                <strong>Monthly:</strong> ${format_currency(frm.doc.monthly_income || 0)}<br>
                                <span class="badge badge-${income_verification.color}">
                                    ${income_verification.status}
                                </span>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Credit Assessment</div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h5 class="card-title">${frm.doc.credit_score || 'Not provided'}</h5>
                                    <p class="card-text">Credit Score</p>
                                </div>
                                <div class="col-md-6">
                                    <div class="progress" style="height: 25px;">
                                        <div class="progress-bar ${get_credit_score_color(frm.doc.credit_score)}" 
                                             role="progressbar" 
                                             style="width: ${get_credit_score_percentage(frm.doc.credit_score)}%" 
                                             aria-valuenow="${frm.doc.credit_score || 0}" 
                                             aria-valuemin="300" aria-valuemax="850">
                                            ${get_credit_score_rating(frm.doc.credit_score)}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // HTML field has been replaced with practical fields
    // Dashboard content now handled by standard form fields
}

function load_business_summary(frm) {
    if (frm.doc.tenant_type !== 'Corporate') return;
    
    let credit_rating_color = get_credit_rating_color(frm.doc.credit_rating);
    
    let html = `
        <div class="business-summary-dashboard">
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Business Information</div>
                        <div class="card-body">
                            <h6 class="card-title">${frm.doc.company_name || 'Company Name Not Provided'}</h6>
                            <p class="card-text">
                                <strong>Business Type:</strong> ${frm.doc.business_type || 'Not specified'}<br>
                                <strong>Contact Person:</strong> ${frm.doc.contact_person || 'Not specified'}<br>
                                <strong>Business License:</strong> ${frm.doc.business_license || 'Not provided'}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Financial Information</div>
                        <div class="card-body">
                            <h6 class="card-title">${format_currency(frm.doc.annual_revenue || 0)}</h6>
                            <p class="card-text">
                                Annual Revenue<br>
                                <strong>Tax ID:</strong> ${frm.doc.tax_id || 'Not provided'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Credit Rating</div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h5 class="card-title">
                                        <span class="badge badge-${credit_rating_color} badge-lg">
                                            ${frm.doc.credit_rating || 'Not Rated'}
                                        </span>
                                    </h5>
                                    <p class="card-text">Corporate Credit Rating</p>
                                </div>
                                <div class="col-md-6">
                                    <p class="card-text">
                                        ${get_credit_rating_description(frm.doc.credit_rating)}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // HTML field has been replaced with practical fields
    // Dashboard content now handled by standard form fields
}

function load_address_map(frm) {
    let current_address = `${frm.doc.current_address || ''}, ${frm.doc.city || ''}, ${frm.doc.country || ''}`;
    let previous_address = `${frm.doc.previous_address || ''}, ${frm.doc.previous_city || ''}, ${frm.doc.previous_country || ''}`;
    
    let html = `
        <div class="address-map-dashboard">
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Current Address</div>
                        <div class="card-body">
                            <p class="card-text">${current_address}</p>
                            <div class="alert alert-info">
                                <i class="fa fa-map-marker"></i> 
                                Map integration for current address can be added here.
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Previous Address</div>
                        <div class="card-body">
                            <p class="card-text">${previous_address || 'Not provided'}</p>
                            <div class="alert alert-secondary">
                                <i class="fa fa-history"></i> 
                                Previous address for reference and verification.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // HTML field has been replaced with practical fields
    // Dashboard content now handled by standard form fields
}

function load_references_dashboard(frm) {
    let background_check_color = get_background_check_color(frm.doc.background_check_status);
    
    let html = `
        <div class="references-dashboard">
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Background Check Status</div>
                        <div class="card-body">
                            <h5 class="card-title">
                                <span class="badge badge-${background_check_color}">
                                    ${frm.doc.background_check_status || 'Pending'}
                                </span>
                            </h5>
                            <p class="card-text">
                                ${get_background_check_description(frm.doc.background_check_status)}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Documents Provided</div>
                        <div class="card-body">
                            <p class="card-text">
                                ${frm.doc.documents_provided || 'No documents listed'}
                            </p>
                            <button type="button" class="btn btn-primary btn-sm" onclick="manage_tenant_documents('${frm.doc.name}')">
                                <i class="fa fa-file"></i> Manage Documents
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Emergency Contact Information</div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <p class="card-text">
                                        <strong>Name:</strong> ${frm.doc.emergency_contact_name || 'Not provided'}<br>
                                        <strong>Relationship:</strong> ${frm.doc.emergency_contact_relationship || 'Not specified'}<br>
                                        <strong>Phone:</strong> ${frm.doc.emergency_contact_phone || 'Not provided'}
                                    </p>
                                </div>
                                <div class="col-md-6">
                                    <p class="card-text">
                                        <strong>Email:</strong> ${frm.doc.emergency_contact_email || 'Not provided'}<br>
                                        <strong>Address:</strong> ${frm.doc.emergency_contact_address || 'Not provided'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // HTML field has been replaced with practical fields
    // Dashboard content now handled by standard form fields
}

function update_tenant_tab_badges(frm) {
    setTimeout(() => {
        // Personal Information tab
        let personal_tab = $('a[data-fieldname="tab_break_personal"]');
        if (personal_tab.length) {
            let tenant_type_badge = frm.doc.tenant_type === 'Individual' ? 
                '<span class="badge badge-primary">Individual</span>' : 
                '<span class="badge badge-info">Corporate</span>';
            personal_tab.html(`Personal Information ${tenant_type_badge}`);
        }
        
        // Employment & Financial tab
        let employment_tab = $('a[data-fieldname="tab_break_employment"]');
        if (employment_tab.length && frm.doc.tenant_type === 'Individual') {
            let has_income = frm.doc.annual_income > 0;
            let badge_class = has_income ? 'badge-success' : 'badge-warning';
            let badge_text = has_income ? 'Verified' : 'Pending';
            employment_tab.html(`Employment & Financial <span class="badge ${badge_class}">${badge_text}</span>`);
        }
        
        // Business Information tab
        let business_tab = $('a[data-fieldname="tab_break_business"]');
        if (business_tab.length && frm.doc.tenant_type === 'Corporate') {
            let has_business_info = frm.doc.business_license && frm.doc.tax_id;
            let badge_class = has_business_info ? 'badge-success' : 'badge-warning';
            let badge_text = has_business_info ? 'Complete' : 'Incomplete';
            business_tab.html(`Business Information <span class="badge ${badge_class}">${badge_text}</span>`);
        }
        
        // Emergency & References tab
        let emergency_tab = $('a[data-fieldname="tab_break_emergency"]');
        if (emergency_tab.length) {
            let background_check_color = get_background_check_color(frm.doc.background_check_status);
            emergency_tab.html(`Emergency & References <span class="badge badge-${background_check_color}">${frm.doc.background_check_status || 'Pending'}</span>`);
        }
    }, 100);
}

function setup_conditional_fields(frm) {
    // Show/hide tabs based on tenant type
    if (frm.doc.tenant_type === 'Individual') {
        frm.toggle_display('tab_break_business', false);
        frm.toggle_display('tab_break_employment', true);
    } else {
        frm.toggle_display('tab_break_employment', false);
        frm.toggle_display('tab_break_business', true);
    }
}

function add_tenant_management_buttons(frm) {
    if (frm.doc.name) {
        // View Contracts Button
        frm.add_custom_button(__('View Contracts'), function() {
            frappe.route_options = {"tenant": frm.doc.name};
            frappe.set_route("List", "Rental Contract");
        }, __('Tenant'));
        
        // Background Check Button
        frm.add_custom_button(__('Run Background Check'), function() {
            run_background_check(frm);
        }, __('Actions'));
        
        // Tenant Report Button
        frm.add_custom_button(__('Tenant Report'), function() {
            show_tenant_report(frm);
        }, __('Reports'));
        
        // Credit Check Button
        if (frm.doc.tenant_type === 'Individual') {
            frm.add_custom_button(__('Credit Check'), function() {
                run_credit_check(frm);
            }, __('Actions'));
        }
    }
}

function generate_full_name(frm) {
    if (frm.doc.first_name || frm.doc.last_name) {
        let full_name = `${frm.doc.first_name || ''} ${frm.doc.last_name || ''}`.trim();
        frm.set_value('full_name', full_name);
    }
}

function initialize_tenant_tab_content(frm) {
    setTimeout(() => {
        if (frm.doc.name) {
            load_tenant_summary_dashboard(frm);
            load_employment_verification(frm);
            load_business_summary(frm);
            load_address_map(frm);
            load_references_dashboard(frm);
        }
        setup_conditional_fields(frm);
    }, 500);
}

// Utility functions
function get_background_check_color(status) {
    switch(status) {
        case 'Passed': return 'success';
        case 'Failed': return 'danger';
        case 'In Progress': return 'warning';
        default: return 'secondary';
    }
}

function get_employment_status_color(status) {
    switch(status) {
        case 'Employed': return 'success';
        case 'Self-Employed': return 'info';
        case 'Unemployed': return 'danger';
        case 'Retired': return 'secondary';
        case 'Student': return 'warning';
        default: return 'light';
    }
}

function verify_income_adequacy(annual_income) {
    // Assuming minimum income requirement (this can be configurable)
    let minimum_annual_income = 50000; // Example threshold
    
    if (!annual_income) {
        return {status: 'Not Provided', color: 'secondary'};
    } else if (annual_income >= minimum_annual_income) {
        return {status: 'Adequate', color: 'success'};
    } else {
        return {status: 'Below Threshold', color: 'warning'};
    }
}

function get_credit_score_color(score) {
    if (!score) return 'bg-secondary';
    if (score >= 750) return 'bg-success';
    if (score >= 650) return 'bg-info';
    if (score >= 550) return 'bg-warning';
    return 'bg-danger';
}

function get_credit_score_percentage(score) {
    if (!score) return 0;
    return ((score - 300) / (850 - 300)) * 100;
}

function get_credit_score_rating(score) {
    if (!score) return 'No Score';
    if (score >= 750) return 'Excellent';
    if (score >= 650) return 'Good';
    if (score >= 550) return 'Fair';
    return 'Poor';
}

function get_credit_rating_color(rating) {
    if (!rating) return 'secondary';
    if (rating.startsWith('A')) return 'success';
    if (rating.startsWith('B')) return 'info';
    if (rating.startsWith('C')) return 'warning';
    return 'danger';
}

function get_credit_rating_description(rating) {
    switch(rating) {
        case 'A+': case 'A': case 'A-': return 'Excellent credit rating with low risk';
        case 'B+': case 'B': case 'B-': return 'Good credit rating with moderate risk';
        case 'C+': case 'C': case 'C-': return 'Fair credit rating with higher risk';
        case 'D': return 'Poor credit rating with high risk';
        default: return 'Credit rating not available';
    }
}

function get_background_check_description(status) {
    switch(status) {
        case 'Passed': return 'Background check completed successfully with no issues found.';
        case 'Failed': return 'Background check revealed issues that require attention.';
        case 'In Progress': return 'Background check is currently being processed.';
        default: return 'Background check has not been initiated yet.';
    }
}

// Global functions
window.manage_tenant_documents = function(tenant_name) {
    frappe.msgprint('Document management functionality can be implemented here.');
};

function run_background_check(frm) {
    frappe.confirm(
        __('Run background check for this tenant?'),
        function() {
            frm.set_value('background_check_status', 'In Progress');
            frm.save();
            frappe.msgprint(__('Background check initiated. Status updated to "In Progress".'));
        }
    );
}

function run_credit_check(frm) {
    frappe.msgprint('Credit check functionality can be implemented here.');
}

function show_tenant_report(frm) {
    frappe.msgprint('Tenant report functionality can be implemented here.');
}

function format_currency(value) {
    return frappe.format(value, {fieldtype: 'Currency'});
}

// CSS for enhanced styling
frappe.ready(function() {
    $('head').append(`
        <style>
            .tenant-summary-dashboard .card,
            .employment-verification-dashboard .card,
            .business-summary-dashboard .card,
            .address-map-dashboard .card,
            .references-dashboard .card {
                margin-bottom: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border: none;
            }
            
            .badge-lg {
                font-size: 1.1em;
                padding: 0.5em 0.75em;
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

