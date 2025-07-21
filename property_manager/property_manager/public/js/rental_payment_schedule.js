// Enhanced JavaScript for Tabbed Rental Payment Schedule
// Copyright (c) 2025, Farah and contributors

frappe.ui.form.on('Rental Payment Schedule', {
    refresh: function(frm) {
        // Add custom buttons for payment management
        if (frm.doc.docstatus === 1) {
            add_payment_management_buttons(frm);
        }
        
        // Load financial summary dashboard
        load_financial_summary_dashboard(frm);
        
        // Load payment actions dashboard
        load_payment_actions_dashboard(frm);
        
        // Add payment status indicators
        add_payment_status_indicators(frm);
        
        // Set up real-time updates
        setup_realtime_updates(frm);
        
        // Update tab badges
        update_tab_badges(frm);
    },
    
    onload: function(frm) {
        // Set up custom filters and formatting
        setup_payment_schedule_formatting(frm);
        
        // Initialize tab content
        initialize_tab_content(frm);
    },
    
    schedule_status: function(frm) {
        // Update tab badges when status changes
        update_tab_badges(frm);
    }
});

frappe.ui.form.on('Payment Schedule', {
    payment_status: function(frm, cdt, cdn) {
        // Update row styling based on payment status
        update_payment_row_styling(frm, cdt, cdn);
        
        // Refresh financial summary
        setTimeout(() => {
            load_financial_summary_dashboard(frm);
            update_tab_badges(frm);
        }, 500);
    },
    
    payment_entry: function(frm, cdt, cdn) {
        // Handle payment entry changes
        handle_payment_entry_change(frm, cdt, cdn);
    }
});

function add_payment_management_buttons(frm) {
    // Payment Dashboard Button
    frm.add_custom_button(__('Payment Dashboard'), function() {
        show_payment_dashboard(frm);
    }, __('Reports'));
    
    // Link Payment Entry Button
    frm.add_custom_button(__('Link Payment Entry'), function() {
        show_payment_linking_dialog(frm);
    }, __('Actions'));
    
    // Payment Summary Button
    frm.add_custom_button(__('Payment Summary'), function() {
        show_payment_summary_dialog(frm);
    }, __('Reports'));
    
    // Export Payments Button
    frm.add_custom_button(__('Export Payments'), function() {
        show_export_dialog(frm);
    }, __('Reports'));
    
    // Overdue Analysis Button
    if (frm.doc.schedule_status === 'Overdue') {
        frm.add_custom_button(__('Overdue Analysis'), function() {
            show_overdue_analysis(frm);
        }, __('Reports'));
    }
    
    // Payment Reminders Button
    frm.add_custom_button(__('Send Reminders'), function() {
        send_payment_reminders(frm);
    }, __('Actions'));
}

function load_financial_summary_dashboard(frm) {
    if (!frm.doc.name) return;
    
    frappe.call({
        method: 'property_manager.utils.reporting.get_payment_schedule_dashboard',
        args: {
            rental_payment_schedule: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.schedules && r.message.schedules.length > 0) {
                let schedule_data = r.message.schedules[0];
                render_financial_summary(frm, schedule_data);
            }
        }
    });
}

function render_financial_summary(frm, schedule_data) {
    let financial_summary = schedule_data.financial_summary;
    let payment_details = schedule_data.payment_details;
    
    // Calculate additional metrics
    let total_payments = payment_details.length;
    let completed_payments = payment_details.filter(p => p.payment_status === 'Paid').length;
    let overdue_payments = schedule_data.overdue_payments.length;
    let upcoming_payments = schedule_data.upcoming_payments.length;
    
    let html = `
        <div class="financial-summary-dashboard">
            <div class="row">
                <div class="col-md-3">
                    <div class="card text-center bg-primary text-white">
                        <div class="card-body">
                            <h4 class="card-title">${format_currency(financial_summary.total_amount)}</h4>
                            <p class="card-text">Total Amount</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center bg-success text-white">
                        <div class="card-body">
                            <h4 class="card-title">${format_currency(financial_summary.paid_amount)}</h4>
                            <p class="card-text">Paid Amount</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center bg-warning text-white">
                        <div class="card-body">
                            <h4 class="card-title">${format_currency(financial_summary.outstanding_amount)}</h4>
                            <p class="card-text">Outstanding</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center bg-info text-white">
                        <div class="card-body">
                            <h4 class="card-title">${financial_summary.payment_completion_rate.toFixed(1)}%</h4>
                            <p class="card-text">Completion Rate</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title text-success">${completed_payments}</h5>
                            <p class="card-text">Completed</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title text-danger">${overdue_payments}</h5>
                            <p class="card-text">Overdue</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title text-info">${upcoming_payments}</h5>
                            <p class="card-text">Upcoming</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title text-primary">${total_payments}</h5>
                            <p class="card-text">Total Payments</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="progress" style="height: 25px;">
                        <div class="progress-bar bg-success" role="progressbar" 
                             style="width: ${financial_summary.payment_completion_rate}%" 
                             aria-valuenow="${financial_summary.payment_completion_rate}" 
                             aria-valuemin="0" aria-valuemax="100">
                            ${financial_summary.payment_completion_rate.toFixed(1)}% Complete
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.financial_summary_html.$wrapper.html(html);
}

function load_payment_actions_dashboard(frm) {
    if (!frm.doc.name) return;
    
    let html = `
        <div class="payment-actions-dashboard">
            <div class="row">
                <div class="col-md-12">
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-primary" onclick="link_payment_entry('${frm.doc.name}')">
                            <i class="fa fa-link"></i> Link Payment Entry
                        </button>
                        <button type="button" class="btn btn-info" onclick="view_payment_history('${frm.doc.name}')">
                            <i class="fa fa-history"></i> Payment History
                        </button>
                        <button type="button" class="btn btn-warning" onclick="send_payment_reminder('${frm.doc.name}')">
                            <i class="fa fa-bell"></i> Send Reminder
                        </button>
                        <button type="button" class="btn btn-success" onclick="export_payment_data('${frm.doc.name}')">
                            <i class="fa fa-download"></i> Export Data
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-12">
                    <div class="alert alert-info">
                        <strong>Quick Actions:</strong>
                        <ul class="mb-0">
                            <li>Use "Link Payment Entry" to manually connect payments to schedules</li>
                            <li>View complete payment history with "Payment History"</li>
                            <li>Send automated reminders for overdue payments</li>
                            <li>Export payment data for external analysis</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.fields_dict.payment_actions_html.$wrapper.html(html);
}

function add_payment_status_indicators(frm) {
    // Add status indicators to the form header
    let status_html = '';
    
    if (frm.doc.schedule_status === 'Overdue') {
        status_html = '<div class="alert alert-danger"><i class="fa fa-exclamation-triangle"></i> This payment schedule has overdue payments</div>';
    } else if (frm.doc.schedule_status === 'Completed') {
        status_html = '<div class="alert alert-success"><i class="fa fa-check-circle"></i> All payments completed successfully</div>';
    } else if (frm.doc.schedule_status === 'Active') {
        status_html = '<div class="alert alert-info"><i class="fa fa-calendar"></i> Payment schedule is active</div>';
    }
    
    if (status_html) {
        frm.dashboard.add_section(status_html);
    }
}

function update_tab_badges(frm) {
    if (!frm.doc.payment_schedules) return;
    
    // Calculate payment statistics
    let total_payments = frm.doc.payment_schedules.length;
    let overdue_count = 0;
    let completed_count = 0;
    
    frm.doc.payment_schedules.forEach(payment => {
        if (payment.payment_status === 'Paid') {
            completed_count++;
        } else if (payment.payment_status === 'Overdue') {
            overdue_count++;
        }
    });
    
    // Update tab labels with badges
    setTimeout(() => {
        // Financial Summary tab
        let financial_tab = $('a[data-fieldname="tab_break_financial"]');
        if (financial_tab.length) {
            let completion_rate = frm.doc.total_rent_amount > 0 ? 
                (frm.doc.paid_amount / frm.doc.total_rent_amount * 100).toFixed(0) : 0;
            financial_tab.html(`Financial Summary <span class="badge badge-info">${completion_rate}%</span>`);
        }
        
        // Payment Schedule tab
        let payments_tab = $('a[data-fieldname="tab_break_payments"]');
        if (payments_tab.length) {
            let badge_class = overdue_count > 0 ? 'badge-danger' : 'badge-success';
            payments_tab.html(`Payment Schedule <span class="badge ${badge_class}">${completed_count}/${total_payments}</span>`);
        }
        
        // Contract Details tab
        let contract_tab = $('a[data-fieldname="tab_break_contract"]');
        if (contract_tab.length) {
            let status_badge = '';
            switch(frm.doc.schedule_status) {
                case 'Active':
                    status_badge = '<span class="badge badge-success">Active</span>';
                    break;
                case 'Overdue':
                    status_badge = '<span class="badge badge-danger">Overdue</span>';
                    break;
                case 'Completed':
                    status_badge = '<span class="badge badge-info">Completed</span>';
                    break;
                default:
                    status_badge = '<span class="badge badge-secondary">Draft</span>';
            }
            contract_tab.html(`Contract Details ${status_badge}`);
        }
    }, 100);
}

function setup_payment_schedule_formatting(frm) {
    // Custom formatting for payment schedule grid
    if (frm.fields_dict.payment_schedules && frm.fields_dict.payment_schedules.grid) {
        // Format payment status
        frm.fields_dict.payment_schedules.grid.get_field('payment_status').formatter = function(value, df, options, doc) {
            let color = 'gray';
            let icon = '⏳';
            
            switch(value) {
                case 'Paid':
                    color = 'green';
                    icon = '✅';
                    break;
                case 'Partially Paid':
                    color = 'orange';
                    icon = '🔄';
                    break;
                case 'Overdue':
                    color = 'red';
                    icon = '⚠️';
                    break;
                case 'Pending':
                    color = 'blue';
                    icon = '📅';
                    break;
            }
            
            return `<span style="color: ${color};">${icon} ${value}</span>`;
        };
        
        // Format outstanding amounts
        frm.fields_dict.payment_schedules.grid.get_field('outstanding').formatter = function(value, df, options, doc) {
            if (parseFloat(value) > 0) {
                return `<span style="color: red; font-weight: bold;">${format_currency(value)}</span>`;
            }
            return format_currency(value);
        };
        
        // Highlight overdue dates
        frm.fields_dict.payment_schedules.grid.get_field('due_date').formatter = function(value, df, options, doc) {
            let due_date = frappe.datetime.str_to_obj(value);
            let today = new Date();
            
            if (due_date < today && parseFloat(doc.outstanding) > 0) {
                let days_overdue = Math.floor((today - due_date) / (1000 * 60 * 60 * 24));
                return `<span style="color: red; font-weight: bold;">${frappe.datetime.str_to_user(value)} <br><small>(${days_overdue} days overdue)</small></span>`;
            }
            
            return frappe.datetime.str_to_user(value);
        };
    }
}

function initialize_tab_content(frm) {
    // Initialize content for each tab
    setTimeout(() => {
        if (frm.doc.name) {
            load_financial_summary_dashboard(frm);
            load_payment_actions_dashboard(frm);
        }
    }, 500);
}

function setup_realtime_updates(frm) {
    // Set up real-time updates for payment status changes
    frappe.realtime.on('payment_schedule_updated', function(data) {
        if (data.rental_payment_schedule === frm.doc.name) {
            frm.reload_doc();
        }
    });
}

// Global functions for payment actions
window.link_payment_entry = function(schedule_name) {
    show_payment_linking_dialog_global(schedule_name);
};

window.view_payment_history = function(schedule_name) {
    show_payment_history_dialog(schedule_name);
};

window.send_payment_reminder = function(schedule_name) {
    send_payment_reminders_global(schedule_name);
};

window.export_payment_data = function(schedule_name) {
    show_export_dialog_global(schedule_name);
};

function show_payment_linking_dialog_global(schedule_name) {
    let dialog = new frappe.ui.Dialog({
        title: __('Link Payment Entry'),
        fields: [
            {
                fieldtype: 'Link',
                fieldname: 'payment_entry',
                label: __('Payment Entry'),
                options: 'Payment Entry',
                reqd: 1,
                get_query: function() {
                    return {
                        filters: {
                            'party_type': 'Customer',
                            'docstatus': 1
                        }
                    };
                }
            }
        ],
        primary_action: function(values) {
            frappe.call({
                method: 'property_manager.utils.payment_entry.manual_link_payment_entry',
                args: {
                    payment_entry: values.payment_entry,
                    rental_payment_schedule: schedule_name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(__('Payment linked successfully'));
                        cur_frm.reload_doc();
                        dialog.hide();
                    }
                }
            });
        },
        primary_action_label: __('Link Payment')
    });
    
    dialog.show();
}

function show_payment_history_dialog(schedule_name) {
    frappe.call({
        method: 'property_manager.utils.reporting.get_payment_entry_linking_report',
        args: {
            rental_payment_schedule: schedule_name
        },
        callback: function(r) {
            if (r.message) {
                let history_data = r.message;
                show_history_dialog(history_data);
            }
        }
    });
}

function show_history_dialog(history_data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Payment History'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'history_html'
            }
        ]
    });
    
    let html = generate_payment_history_html(history_data);
    dialog.fields_dict.history_html.$wrapper.html(html);
    dialog.show();
}

function generate_payment_history_html(data) {
    let html = `
        <div class="payment-history">
            <h4>Payment Summary</h4>
            <table class="table table-bordered">
                <tr><td>Total Payments</td><td>${data.summary.total_payments}</td></tr>
                <tr><td>Linked Payments</td><td>${data.summary.linked_payments}</td></tr>
                <tr><td>Total Amount</td><td>${format_currency(data.summary.total_amount)}</td></tr>
                <tr><td>Linked Amount</td><td>${format_currency(data.summary.linked_amount)}</td></tr>
            </table>
            
            <h4>Payment Details</h4>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Payment Entry</th>
                        <th>Date</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Reference</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    data.payment_details.forEach(payment => {
        let status_badge = payment.is_linked ? 
            '<span class="badge badge-success">Linked</span>' : 
            '<span class="badge badge-warning">Unlinked</span>';
            
        html += `
            <tr>
                <td>${payment.payment_entry}</td>
                <td>${frappe.datetime.str_to_user(payment.date)}</td>
                <td>${format_currency(payment.amount)}</td>
                <td>${status_badge}</td>
                <td>${payment.reference || '-'}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    return html;
}

function send_payment_reminders_global(schedule_name) {
    frappe.confirm(
        __('Send payment reminders for overdue payments?'),
        function() {
            frappe.call({
                method: 'property_manager.utils.notifications.send_payment_reminders',
                args: {
                    rental_payment_schedule: schedule_name
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint(__('Payment reminders sent successfully'));
                    } else {
                        frappe.msgprint(__('Failed to send reminders: ') + (r.message.error || 'Unknown error'));
                    }
                }
            });
        }
    );
}

function show_export_dialog_global(schedule_name) {
    let dialog = new frappe.ui.Dialog({
        title: __('Export Payment Data'),
        fields: [
            {
                fieldtype: 'Select',
                fieldname: 'format',
                label: __('Format'),
                options: 'Excel\nCSV\nPDF',
                default: 'Excel',
                reqd: 1
            }
        ],
        primary_action: function(values) {
            frappe.call({
                method: 'property_manager.utils.reporting.export_payment_data',
                args: {
                    format_type: values.format.toLowerCase(),
                    filters: {
                        rental_payment_schedule: schedule_name
                    }
                },
                callback: function(r) {
                    if (r.message && !r.message.error) {
                        frappe.msgprint(__('Export completed successfully'));
                        dialog.hide();
                    } else {
                        frappe.msgprint(__('Export failed: ') + (r.message.error || 'Unknown error'));
                    }
                }
            });
        },
        primary_action_label: __('Export')
    });
    
    dialog.show();
}

// Utility functions
function format_currency(value) {
    return frappe.format(value, {fieldtype: 'Currency'});
}

function update_payment_row_styling(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let grid_row = frm.fields_dict.payment_schedules.grid.grid_rows_by_docname[cdn];
    
    if (grid_row) {
        let $row = grid_row.$wrapper;
        
        // Remove existing status classes
        $row.removeClass('payment-paid payment-overdue payment-partial payment-pending');
        
        // Add appropriate class based on status
        switch(row.payment_status) {
            case 'Paid':
                $row.addClass('payment-paid');
                break;
            case 'Overdue':
                $row.addClass('payment-overdue');
                break;
            case 'Partially Paid':
                $row.addClass('payment-partial');
                break;
            default:
                $row.addClass('payment-pending');
        }
    }
}

function handle_payment_entry_change(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    if (row.payment_entry) {
        // Fetch payment entry details
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Payment Entry',
                name: row.payment_entry
            },
            callback: function(r) {
                if (r.message) {
                    let payment_entry = r.message;
                    
                    // Update row with payment entry details
                    frappe.model.set_value(cdt, cdn, 'payment_date', payment_entry.posting_date);
                    frappe.model.set_value(cdt, cdn, 'payment_reference', payment_entry.reference_no);
                    frappe.model.set_value(cdt, cdn, 'payment_mode', payment_entry.mode_of_payment);
                    
                    frm.refresh_field('payment_schedules');
                }
            }
        });
    }
}

// CSS for enhanced styling
frappe.ready(function() {
    $('head').append(`
        <style>
            .payment-paid { background-color: #d4edda !important; }
            .payment-overdue { background-color: #f8d7da !important; }
            .payment-partial { background-color: #fff3cd !important; }
            .payment-pending { background-color: #d1ecf1 !important; }
            
            .financial-summary-dashboard .card {
                margin-bottom: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border: none;
            }
            
            .financial-summary-dashboard .card-title {
                font-size: 1.2em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .payment-actions-dashboard .btn-group {
                width: 100%;
            }
            
            .payment-actions-dashboard .btn {
                flex: 1;
                margin: 2px;
            }
            
            .tab-content .tab-pane {
                padding: 20px 0;
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
        </style>
    `);
});

