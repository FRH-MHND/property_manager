// Enhanced JavaScript for Tabbed Rental Contract Doctype
// Copyright (c) 2025, Farah and contributors

frappe.ui.form.on('Rental Contract', {
    refresh: function(frm) {
        // Load contract summary dashboard
        load_contract_summary_dashboard(frm);
        
        // Load financial analysis
        load_contract_financial_analysis(frm);
        
        // Load payment dashboard
        load_contract_payment_dashboard(frm);
        
        // Load contract lifecycle
        load_contract_lifecycle_dashboard(frm);
        
        // Load contract documents
        load_contract_documents_dashboard(frm);
        
        // Update tab badges
        update_rental_contract_tab_badges(frm);
        
        // Add custom buttons
        add_rental_contract_management_buttons(frm);
    },
    
    onload: function(frm) {
        // Initialize tab content
        initialize_rental_contract_tab_content(frm);
    },
    
    contract_status: function(frm) {
        // Update tab badges when status changes
        update_rental_contract_tab_badges(frm);
    },
    
    monthly_rent: function(frm) {
        // Recalculate amounts when rent changes
        calculate_contract_amounts(frm);
    },
    
    payment_frequency: function(frm) {
        // Recalculate amounts when frequency changes
        calculate_contract_amounts(frm);
    },
    
    start_date: function(frm) {
        // Recalculate amounts when dates change
        calculate_contract_amounts(frm);
    },
    
    end_date: function(frm) {
        // Recalculate amounts when dates change
        calculate_contract_amounts(frm);
    },
    
    rental_unit: function(frm) {
        // Auto-populate property when unit is selected
        if (frm.doc.rental_unit) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Rental Unit',
                    filters: {name: frm.doc.rental_unit},
                    fieldname: ['property', 'monthly_rent', 'security_deposit']
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('property', r.message.property);
                        if (!frm.doc.monthly_rent) {
                            frm.set_value('monthly_rent', r.message.monthly_rent);
                        }
                        if (!frm.doc.security_deposit_amount) {
                            frm.set_value('security_deposit_amount', r.message.security_deposit);
                        }
                    }
                }
            });
        }
    }
});

function load_contract_summary_dashboard(frm) {
    let contract_duration = calculate_contract_duration(frm.doc.start_date, frm.doc.end_date);
    let status_color = get_contract_status_color(frm.doc.contract_status);
    
    let html = `
        <div class="contract-summary-dashboard">
            <div class="row">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">Contract Status</div>
                        <div class="card-body text-center">
                            <h5 class="card-title">
                                <span class="badge badge-${status_color} badge-lg">
                                    ${frm.doc.contract_status || 'Draft'}
                                </span>
                            </h5>
                            <p class="card-text">${get_contract_status_description(frm.doc.contract_status)}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">Contract Duration</div>
                        <div class="card-body text-center">
                            <h5 class="card-title">${contract_duration.value}</h5>
                            <p class="card-text">
                                ${contract_duration.label}<br>
                                <small class="text-muted">${frm.doc.start_date || 'Not set'} to ${frm.doc.end_date || 'Not set'}</small>
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">Payment Frequency</div>
                        <div class="card-body text-center">
                            <h5 class="card-title">${frm.doc.payment_frequency || 'Not Set'}</h5>
                            <p class="card-text">
                                Due on day ${frm.doc.payment_due_day || 'Not specified'}<br>
                                <small class="text-muted">Grace period: ${frm.doc.grace_period_days || 0} days</small>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Tenant Information</div>
                        <div class="card-body">
                            <h6 class="card-title">${frm.doc.tenant || 'Not Selected'}</h6>
                            <p class="card-text">
                                <strong>Property:</strong> ${frm.doc.property || 'Not specified'}<br>
                                <strong>Unit:</strong> ${frm.doc.rental_unit || 'Not specified'}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Financial Summary</div>
                        <div class="card-body">
                            <h6 class="card-title">${format_currency(frm.doc.monthly_rent || 0)}</h6>
                            <p class="card-text">
                                Monthly Rent<br>
                                <strong>Total Value:</strong> ${format_currency(frm.doc.total_contract_value || 0)}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // HTML field contract_summary_html has been replaced with practical fields
    // Dashboard content now handled by standard form fields
}

function load_contract_financial_analysis(frm) {
    let monthly_rent = frm.doc.monthly_rent || 0;
    let total_value = frm.doc.total_contract_value || 0;
    let security_deposit = frm.doc.security_deposit_amount || 0;
    let rent_per_frequency = frm.doc.rent_amount_per_frequency || 0;
    
    // Calculate payment statistics
    let payment_stats = calculate_payment_statistics(frm);
    
    let html = `
        <div class="contract-financial-analysis">
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
                    <div class="card text-center bg-success text-white">
                        <div class="card-body">
                            <h5 class="card-title">${format_currency(rent_per_frequency)}</h5>
                            <p class="card-text">Per Payment</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center bg-info text-white">
                        <div class="card-body">
                            <h5 class="card-title">${format_currency(security_deposit)}</h5>
                            <p class="card-text">Security Deposit</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center bg-warning text-white">
                        <div class="card-body">
                            <h5 class="card-title">${format_currency(total_value)}</h5>
                            <p class="card-text">Total Value</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Payment Terms</div>
                        <div class="card-body">
                            <p class="card-text">
                                <strong>Frequency:</strong> ${frm.doc.payment_frequency || 'Not set'}<br>
                                <strong>Due Day:</strong> ${frm.doc.payment_due_day || 'Not set'}<br>
                                <strong>Late Fee:</strong> ${format_currency(frm.doc.late_fee_amount || 0)}<br>
                                <strong>Grace Period:</strong> ${frm.doc.grace_period_days || 0} days
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Deposit Information</div>
                        <div class="card-body">
                            <p class="card-text">
                                <strong>Required:</strong> ${format_currency(security_deposit)}<br>
                                <strong>Paid:</strong> ${format_currency(frm.doc.deposit_paid || 0)}<br>
                                <strong>Status:</strong> <span class="badge badge-${get_deposit_status_color(frm.doc.deposit_status)}">${frm.doc.deposit_status || 'Pending'}</span><br>
                                <strong>Date Paid:</strong> ${frm.doc.deposit_paid_date || 'Not paid'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Payment Statistics</div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <h6>Total Payments</h6>
                                    <h4 class="text-primary">${payment_stats.total_payments}</h4>
                                </div>
                                <div class="col-md-3">
                                    <h6>Annual Income</h6>
                                    <h4 class="text-success">${format_currency(payment_stats.annual_income)}</h4>
                                </div>
                                <div class="col-md-3">
                                    <h6>Quarterly Income</h6>
                                    <h4 class="text-info">${format_currency(payment_stats.quarterly_income)}</h4>
                                </div>
                                <div class="col-md-3">
                                    <h6>Weekly Income</h6>
                                    <h4 class="text-warning">${format_currency(payment_stats.weekly_income)}</h4>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // HTML field financial_analysis_html has been replaced with practical fields
    // Dashboard content now handled by standard form fields
}

function load_contract_payment_dashboard(frm) {
    let payment_schedule_status = frm.doc.payment_schedule_reference ? 'Created' : 'Not Created';
    let auto_create = frm.doc.auto_create_payment_schedule ? 'Enabled' : 'Disabled';
    
    let html = `
        <div class="contract-payment-dashboard">
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Payment Schedule</div>
                        <div class="card-body">
                            <h6 class="card-title">
                                <span class="badge badge-${payment_schedule_status === 'Created' ? 'success' : 'warning'}">
                                    ${payment_schedule_status}
                                </span>
                            </h6>
                            <p class="card-text">
                                <strong>Reference:</strong> ${frm.doc.payment_schedule_reference || 'Not created'}<br>
                                <strong>Auto Create:</strong> <span class="badge badge-${auto_create === 'Enabled' ? 'success' : 'secondary'}">${auto_create}</span>
                            </p>
                            ${frm.doc.payment_schedule_reference ? 
                                `<button type="button" class="btn btn-primary btn-sm" onclick="view_payment_schedule('${frm.doc.payment_schedule_reference}')">
                                    <i class="fa fa-eye"></i> View Schedule
                                </button>` : 
                                `<button type="button" class="btn btn-success btn-sm" onclick="create_payment_schedule('${frm.doc.name}')">
                                    <i class="fa fa-plus"></i> Create Schedule
                                </button>`
                            }
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Payment Actions</div>
                        <div class="card-body">
                            <button type="button" class="btn btn-info btn-sm" onclick="record_payment('${frm.doc.name}')">
                                <i class="fa fa-money"></i> Record Payment
                            </button>
                            <button type="button" class="btn btn-warning btn-sm ml-2" onclick="view_payment_history('${frm.doc.name}')">
                                <i class="fa fa-history"></i> Payment History
                            </button>
                            <br><br>
                            <button type="button" class="btn btn-secondary btn-sm" onclick="generate_invoice('${frm.doc.name}')">
                                <i class="fa fa-file-invoice"></i> Generate Invoice
                            </button>
                            <button type="button" class="btn btn-primary btn-sm ml-2" onclick="payment_reminder('${frm.doc.name}')">
                                <i class="fa fa-bell"></i> Send Reminder
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Payment Schedule Overview</div>
                        <div class="card-body">
                            <div class="alert alert-info">
                                <i class="fa fa-calendar"></i> 
                                Payment schedule details and progress tracking will be displayed here.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // HTML field payment_dashboard_html has been replaced with practical fields
    // Dashboard content now handled by standard form fields
}

function load_contract_lifecycle_dashboard(frm) {
    let lifecycle_status = get_contract_lifecycle_status(frm);
    let renewal_info = get_renewal_information(frm);
    
    let html = `
        <div class="contract-lifecycle-dashboard">
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Contract Lifecycle</div>
                        <div class="card-body">
                            <h6 class="card-title">
                                <span class="badge badge-${lifecycle_status.color}">
                                    ${lifecycle_status.status}
                                </span>
                            </h6>
                            <p class="card-text">
                                ${lifecycle_status.description}<br>
                                <strong>Days Remaining:</strong> ${lifecycle_status.days_remaining}
                            </p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Renewal Options</div>
                        <div class="card-body">
                            <h6 class="card-title">
                                <span class="badge badge-${frm.doc.auto_renewal ? 'success' : 'secondary'}">
                                    ${frm.doc.auto_renewal ? 'Auto Renewal Enabled' : 'Manual Renewal'}
                                </span>
                            </h6>
                            <p class="card-text">
                                <strong>Notice Required:</strong> ${frm.doc.renewal_notice_days || 30} days<br>
                                <strong>Termination Notice:</strong> ${frm.doc.termination_notice_days || 30} days
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Contract Actions</div>
                        <div class="card-body">
                            <button type="button" class="btn btn-success btn-sm" onclick="renew_contract('${frm.doc.name}')">
                                <i class="fa fa-refresh"></i> Renew Contract
                            </button>
                            <button type="button" class="btn btn-warning btn-sm ml-2" onclick="modify_contract('${frm.doc.name}')">
                                <i class="fa fa-edit"></i> Modify Terms
                            </button>
                            <button type="button" class="btn btn-danger btn-sm ml-2" onclick="terminate_contract('${frm.doc.name}')">
                                <i class="fa fa-times"></i> Terminate Contract
                            </button>
                            <br><br>
                            <button type="button" class="btn btn-info btn-sm" onclick="contract_history('${frm.doc.name}')">
                                <i class="fa fa-history"></i> Contract History
                            </button>
                            <button type="button" class="btn btn-secondary btn-sm ml-2" onclick="export_contract('${frm.doc.name}')">
                                <i class="fa fa-download"></i> Export Contract
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // HTML field contract_lifecycle_html has been replaced with practical fields
    // Dashboard content now handled by standard form fields
}

function load_contract_documents_dashboard(frm) {
    let html = `
        <div class="contract-documents-dashboard">
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">Contract Documents</div>
                        <div class="card-body">
                            <div class="alert alert-info">
                                <i class="fa fa-file-text"></i> 
                                Contract document management functionality can be implemented here.
                            </div>
                            <button type="button" class="btn btn-primary btn-sm" onclick="upload_contract_documents('${frm.doc.name}')">
                                <i class="fa fa-upload"></i> Upload Documents
                            </button>
                            <button type="button" class="btn btn-success btn-sm ml-2" onclick="generate_contract_pdf('${frm.doc.name}')">
                                <i class="fa fa-file-pdf"></i> Generate PDF
                            </button>
                            <button type="button" class="btn btn-info btn-sm ml-2" onclick="view_contract_documents('${frm.doc.name}')">
                                <i class="fa fa-folder"></i> View Documents
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // HTML field contract_documents_html has been replaced with practical fields
    // Dashboard content now handled by standard form fields
}

function update_rental_contract_tab_badges(frm) {
    setTimeout(() => {
        // Contract Details tab
        let contract_tab = $('a[data-fieldname="tab_break_contract"]');
        if (contract_tab.length) {
            let status_badge = `<span class="badge badge-${get_contract_status_color(frm.doc.contract_status)}">${frm.doc.contract_status || 'Draft'}</span>`;
            contract_tab.html(`Contract Details ${status_badge}`);
        }
        
        // Financial Terms tab
        let financial_tab = $('a[data-fieldname="tab_break_financial"]');
        if (financial_tab.length) {
            let has_rent = frm.doc.monthly_rent > 0;
            let badge_class = has_rent ? 'badge-success' : 'badge-warning';
            let badge_text = has_rent ? format_currency(frm.doc.monthly_rent) : 'No Rent';
            financial_tab.html(`Financial Terms <span class="badge ${badge_class}">${badge_text}</span>`);
        }
        
        // Payment Schedule tab
        let payment_tab = $('a[data-fieldname="tab_break_payment_schedule"]');
        if (payment_tab.length) {
            let has_schedule = frm.doc.payment_schedule_reference;
            let badge_class = has_schedule ? 'badge-success' : 'badge-warning';
            let badge_text = has_schedule ? 'Created' : 'Pending';
            payment_tab.html(`Payment Schedule <span class="badge ${badge_class}">${badge_text}</span>`);
        }
        
        // Contract Options tab
        let options_tab = $('a[data-fieldname="tab_break_contract_options"]');
        if (options_tab.length) {
            let auto_renewal = frm.doc.auto_renewal;
            let badge_class = auto_renewal ? 'badge-info' : 'badge-secondary';
            let badge_text = auto_renewal ? 'Auto Renewal' : 'Manual';
            options_tab.html(`Contract Options <span class="badge ${badge_class}">${badge_text}</span>`);
        }
    }, 100);
}

function add_rental_contract_management_buttons(frm) {
    if (frm.doc.name && frm.doc.docstatus === 1) {
        // Payment Schedule Button
        if (frm.doc.payment_schedule_reference) {
            frm.add_custom_button(__('View Payment Schedule'), function() {
                frappe.set_route('Form', 'Rental Payment Schedule', frm.doc.payment_schedule_reference);
            }, __('Contract'));
        } else {
            frm.add_custom_button(__('Create Payment Schedule'), function() {
                create_payment_schedule_from_contract(frm);
            }, __('Contract'));
        }
        
        // Contract Actions
        frm.add_custom_button(__('Renew Contract'), function() {
            renew_contract_action(frm);
        }, __('Actions'));
        
        frm.add_custom_button(__('Terminate Contract'), function() {
            terminate_contract_action(frm);
        }, __('Actions'));
        
        // Reports
        frm.add_custom_button(__('Contract Report'), function() {
            show_contract_report(frm);
        }, __('Reports'));
        
        frm.add_custom_button(__('Payment Report'), function() {
            show_payment_report(frm);
        }, __('Reports'));
    }
}

function calculate_contract_amounts(frm) {
    if (frm.doc.monthly_rent && frm.doc.payment_frequency) {
        let monthly_rent = frm.doc.monthly_rent;
        let rent_per_frequency = 0;
        
        switch(frm.doc.payment_frequency) {
            case 'Weekly':
                rent_per_frequency = monthly_rent * 12 / 52;
                break;
            case 'Bi-weekly':
                rent_per_frequency = monthly_rent * 12 / 26;
                break;
            case 'Monthly':
                rent_per_frequency = monthly_rent;
                break;
            case 'Quarterly':
                rent_per_frequency = monthly_rent * 3;
                break;
            case 'Annually':
                rent_per_frequency = monthly_rent * 12;
                break;
        }
        
        frm.set_value('rent_amount_per_frequency', rent_per_frequency);
    }
    
    if (frm.doc.monthly_rent && frm.doc.start_date && frm.doc.end_date) {
        let start_date = new Date(frm.doc.start_date);
        let end_date = new Date(frm.doc.end_date);
        let months = (end_date.getFullYear() - start_date.getFullYear()) * 12 + (end_date.getMonth() - start_date.getMonth());
        let total_value = frm.doc.monthly_rent * months;
        
        frm.set_value('total_contract_value', total_value);
    }
}

function initialize_rental_contract_tab_content(frm) {
    setTimeout(() => {
        if (frm.doc.name) {
            load_contract_summary_dashboard(frm);
            load_contract_financial_analysis(frm);
            load_contract_payment_dashboard(frm);
            load_contract_lifecycle_dashboard(frm);
            load_contract_documents_dashboard(frm);
        }
        calculate_contract_amounts(frm);
    }, 500);
}

// Utility functions
function get_contract_status_color(status) {
    switch(status) {
        case 'Active': return 'success';
        case 'Draft': return 'secondary';
        case 'Expired': return 'warning';
        case 'Terminated': return 'danger';
        case 'Renewed': return 'info';
        case 'Cancelled': return 'dark';
        default: return 'light';
    }
}

function get_contract_status_description(status) {
    switch(status) {
        case 'Active': return 'Contract is currently active and in effect';
        case 'Draft': return 'Contract is in draft status and not yet active';
        case 'Expired': return 'Contract has reached its end date';
        case 'Terminated': return 'Contract has been terminated early';
        case 'Renewed': return 'Contract has been renewed for another term';
        case 'Cancelled': return 'Contract has been cancelled';
        default: return 'Contract status not specified';
    }
}

function get_deposit_status_color(status) {
    switch(status) {
        case 'Paid': return 'success';
        case 'Partially Paid': return 'warning';
        case 'Pending': return 'secondary';
        case 'Refunded': return 'info';
        case 'Forfeited': return 'danger';
        default: return 'light';
    }
}

function calculate_contract_duration(start_date, end_date) {
    if (!start_date || !end_date) {
        return {value: 'N/A', label: 'Duration not calculated'};
    }
    
    let start = new Date(start_date);
    let end = new Date(end_date);
    let months = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth());
    
    if (months < 1) {
        let days = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
        return {value: days, label: `${days} Day${days !== 1 ? 's' : ''}`};
    } else if (months < 12) {
        return {value: months, label: `${months} Month${months !== 1 ? 's' : ''}`};
    } else {
        let years = Math.floor(months / 12);
        let remaining_months = months % 12;
        if (remaining_months === 0) {
            return {value: years, label: `${years} Year${years !== 1 ? 's' : ''}`};
        } else {
            return {value: `${years}y ${remaining_months}m`, label: 'Years and Months'};
        }
    }
}

function calculate_payment_statistics(frm) {
    let monthly_rent = frm.doc.monthly_rent || 0;
    
    return {
        total_payments: frm.doc.total_contract_value ? Math.ceil(frm.doc.total_contract_value / (frm.doc.rent_amount_per_frequency || monthly_rent)) : 0,
        annual_income: monthly_rent * 12,
        quarterly_income: monthly_rent * 3,
        weekly_income: monthly_rent * 12 / 52
    };
}

function get_contract_lifecycle_status(frm) {
    if (!frm.doc.end_date) {
        return {
            status: 'No End Date',
            color: 'secondary',
            description: 'Contract end date not specified',
            days_remaining: 'N/A'
        };
    }
    
    let end_date = new Date(frm.doc.end_date);
    let today = new Date();
    let days_remaining = Math.ceil((end_date - today) / (1000 * 60 * 60 * 24));
    
    if (days_remaining < 0) {
        return {
            status: 'Expired',
            color: 'danger',
            description: 'Contract has expired',
            days_remaining: Math.abs(days_remaining) + ' days ago'
        };
    } else if (days_remaining <= 30) {
        return {
            status: 'Expiring Soon',
            color: 'warning',
            description: 'Contract expires within 30 days',
            days_remaining: days_remaining
        };
    } else {
        return {
            status: 'Active',
            color: 'success',
            description: 'Contract is active and valid',
            days_remaining: days_remaining
        };
    }
}

function get_renewal_information(frm) {
    return {
        auto_renewal: frm.doc.auto_renewal,
        notice_days: frm.doc.renewal_notice_days || 30,
        termination_notice: frm.doc.termination_notice_days || 30
    };
}

// Global functions
window.view_payment_schedule = function(schedule_name) {
    frappe.set_route('Form', 'Rental Payment Schedule', schedule_name);
};

window.create_payment_schedule = function(contract_name) {
    frappe.msgprint('Payment schedule creation functionality can be implemented here.');
};

window.record_payment = function(contract_name) {
    frappe.msgprint('Payment recording functionality can be implemented here.');
};

window.view_payment_history = function(contract_name) {
    frappe.msgprint('Payment history functionality can be implemented here.');
};

window.generate_invoice = function(contract_name) {
    frappe.msgprint('Invoice generation functionality can be implemented here.');
};

window.payment_reminder = function(contract_name) {
    frappe.msgprint('Payment reminder functionality can be implemented here.');
};

window.renew_contract = function(contract_name) {
    frappe.msgprint('Contract renewal functionality can be implemented here.');
};

window.modify_contract = function(contract_name) {
    frappe.msgprint('Contract modification functionality can be implemented here.');
};

window.terminate_contract = function(contract_name) {
    frappe.msgprint('Contract termination functionality can be implemented here.');
};

window.contract_history = function(contract_name) {
    frappe.msgprint('Contract history functionality can be implemented here.');
};

window.export_contract = function(contract_name) {
    frappe.msgprint('Contract export functionality can be implemented here.');
};

window.upload_contract_documents = function(contract_name) {
    frappe.msgprint('Document upload functionality can be implemented here.');
};

window.generate_contract_pdf = function(contract_name) {
    frappe.msgprint('PDF generation functionality can be implemented here.');
};

window.view_contract_documents = function(contract_name) {
    frappe.msgprint('Document viewing functionality can be implemented here.');
};

function create_payment_schedule_from_contract(frm) {
    frappe.msgprint('Payment schedule creation from contract functionality can be implemented here.');
}

function renew_contract_action(frm) {
    frappe.msgprint('Contract renewal action functionality can be implemented here.');
}

function terminate_contract_action(frm) {
    frappe.msgprint('Contract termination action functionality can be implemented here.');
}

function show_contract_report(frm) {
    frappe.msgprint('Contract report functionality can be implemented here.');
}

function show_payment_report(frm) {
    frappe.msgprint('Payment report functionality can be implemented here.');
}

function format_currency(value) {
    return frappe.format(value, {fieldtype: 'Currency'});
}

// CSS for enhanced styling
frappe.ready(function() {
    $('head').append(`
        <style>
            .contract-summary-dashboard .card,
            .contract-financial-analysis .card,
            .contract-payment-dashboard .card,
            .contract-lifecycle-dashboard .card,
            .contract-documents-dashboard .card {
                margin-bottom: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border: none;
            }
            
            .contract-financial-analysis .card-title {
                font-size: 1.2em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .badge-lg {
                font-size: 1.1em;
                padding: 0.5em 0.75em;
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

