// Copyright (c) 2025, Farah and contributors
// For license information, please see license.txt

frappe.ui.form.on('Rental Payment Schedule', {
    refresh: function(frm) {
        // Add custom buttons for payment management
        if (frm.doc.docstatus === 1) {
            add_payment_management_buttons(frm);
        }
        
        // Add payment status indicators
        add_payment_status_indicators(frm);
        
        // Add dashboard cards
        add_payment_dashboard_cards(frm);
        
        // Set up real-time updates
        setup_realtime_updates(frm);
    },
    
    onload: function(frm) {
        // Set up custom filters and formatting
        setup_payment_schedule_formatting(frm);
    }
});

frappe.ui.form.on('Payment Schedule', {
    payment_status: function(frm, cdt, cdn) {
        // Update row styling based on payment status
        update_payment_row_styling(frm, cdt, cdn);
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

function add_payment_status_indicators(frm) {
    // Add status indicators to the form
    let status_html = '';
    
    if (frm.doc.schedule_status === 'Overdue') {
        status_html = '<div class="alert alert-danger">⚠️ This payment schedule has overdue payments</div>';
    } else if (frm.doc.schedule_status === 'Completed') {
        status_html = '<div class="alert alert-success">✅ All payments completed</div>';
    } else if (frm.doc.schedule_status === 'Active') {
        status_html = '<div class="alert alert-info">📅 Payment schedule is active</div>';
    }
    
    if (status_html) {
        frm.dashboard.add_section(status_html);
    }
}

function add_payment_dashboard_cards(frm) {
    // Add dashboard cards with key metrics
    frappe.call({
        method: 'property_manager.utils.reporting.get_payment_schedule_dashboard',
        args: {
            rental_payment_schedule: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.schedules && r.message.schedules.length > 0) {
                let schedule_data = r.message.schedules[0];
                add_dashboard_cards(frm, schedule_data);
            }
        }
    });
}

function add_dashboard_cards(frm, schedule_data) {
    let cards_html = `
        <div class="row">
            <div class="col-sm-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">${format_currency(schedule_data.financial_summary.total_amount)}</h5>
                        <p class="card-text">Total Amount</p>
                    </div>
                </div>
            </div>
            <div class="col-sm-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">${format_currency(schedule_data.financial_summary.paid_amount)}</h5>
                        <p class="card-text">Paid Amount</p>
                    </div>
                </div>
            </div>
            <div class="col-sm-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">${format_currency(schedule_data.financial_summary.outstanding_amount)}</h5>
                        <p class="card-text">Outstanding</p>
                    </div>
                </div>
            </div>
            <div class="col-sm-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">${schedule_data.financial_summary.payment_completion_rate.toFixed(1)}%</h5>
                        <p class="card-text">Completion Rate</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-sm-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-success">${schedule_data.payment_history.length}</h5>
                        <p class="card-text">Completed Payments</p>
                    </div>
                </div>
            </div>
            <div class="col-sm-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-warning">${schedule_data.overdue_payments.length}</h5>
                        <p class="card-text">Overdue Payments</p>
                    </div>
                </div>
            </div>
            <div class="col-sm-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title text-info">${schedule_data.upcoming_payments.length}</h5>
                        <p class="card-text">Upcoming Payments</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    frm.dashboard.add_section(cards_html, __('Payment Overview'));
}

function setup_payment_schedule_formatting(frm) {
    // Custom formatting for payment schedule grid
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
    
    // Format payment amounts
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
            return `<span style="color: red; font-weight: bold;">${frappe.datetime.str_to_user(value)} (${days_overdue} days overdue)</span>`;
        }
        
        return frappe.datetime.str_to_user(value);
    };
}

function setup_realtime_updates(frm) {
    // Set up real-time updates for payment status changes
    frappe.realtime.on('payment_schedule_updated', function(data) {
        if (data.rental_payment_schedule === frm.doc.name) {
            frm.reload_doc();
        }
    });
}

function show_payment_dashboard(frm) {
    frappe.call({
        method: 'property_manager.utils.reporting.get_payment_schedule_dashboard',
        args: {
            rental_payment_schedule: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let dashboard_data = r.message;
                show_dashboard_dialog(dashboard_data);
            }
        }
    });
}

function show_dashboard_dialog(dashboard_data) {
    let dialog = new frappe.ui.Dialog({
        title: __('Payment Dashboard'),
        size: 'extra-large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'dashboard_html'
            }
        ]
    });
    
    let html = generate_dashboard_html(dashboard_data);
    dialog.fields_dict.dashboard_html.$wrapper.html(html);
    dialog.show();
}

function generate_dashboard_html(data) {
    let schedule_data = data.schedules[0];
    
    let html = `
        <div class="payment-dashboard">
            <div class="row">
                <div class="col-md-6">
                    <h4>Financial Summary</h4>
                    <table class="table table-bordered">
                        <tr><td>Total Amount</td><td>${format_currency(schedule_data.financial_summary.total_amount)}</td></tr>
                        <tr><td>Paid Amount</td><td>${format_currency(schedule_data.financial_summary.paid_amount)}</td></tr>
                        <tr><td>Outstanding</td><td>${format_currency(schedule_data.financial_summary.outstanding_amount)}</td></tr>
                        <tr><td>Completion Rate</td><td>${schedule_data.financial_summary.payment_completion_rate.toFixed(1)}%</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h4>Payment Status</h4>
                    <table class="table table-bordered">
                        <tr><td>Completed</td><td>${schedule_data.payment_history.length}</td></tr>
                        <tr><td>Overdue</td><td>${schedule_data.overdue_payments.length}</td></tr>
                        <tr><td>Upcoming</td><td>${schedule_data.upcoming_payments.length}</td></tr>
                        <tr><td>Total Payments</td><td>${schedule_data.payment_details.length}</td></tr>
                    </table>
                </div>
            </div>
    `;
    
    if (schedule_data.overdue_payments.length > 0) {
        html += `
            <div class="row mt-4">
                <div class="col-md-12">
                    <h4>Overdue Payments</h4>
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Due Date</th>
                                <th>Amount</th>
                                <th>Outstanding</th>
                                <th>Days Overdue</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        schedule_data.overdue_payments.forEach(payment => {
            html += `
                <tr>
                    <td>${frappe.datetime.str_to_user(payment.due_date)}</td>
                    <td>${format_currency(payment.payment_amount)}</td>
                    <td>${format_currency(payment.outstanding)}</td>
                    <td>${payment.days_overdue} days</td>
                </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

function show_payment_linking_dialog(frm) {
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
            },
            {
                fieldtype: 'Select',
                fieldname: 'payment_schedule_row',
                label: __('Payment Schedule Row'),
                reqd: 1
            }
        ],
        primary_action: function(values) {
            frappe.call({
                method: 'property_manager.utils.payment_entry.manual_link_payment_entry',
                args: {
                    payment_entry: values.payment_entry,
                    rental_payment_schedule: frm.doc.name,
                    payment_schedule_row: values.payment_schedule_row
                },
                callback: function(r) {
                    if (r.message) {
                        frm.reload_doc();
                        dialog.hide();
                    }
                }
            });
        },
        primary_action_label: __('Link Payment')
    });
    
    // Populate payment schedule options
    let options = [];
    frm.doc.payment_schedules.forEach(row => {
        if (parseFloat(row.outstanding) > 0) {
            options.push({
                label: `${frappe.datetime.str_to_user(row.due_date)} - ${format_currency(row.outstanding)}`,
                value: row.name
            });
        }
    });
    
    dialog.fields_dict.payment_schedule_row.df.options = options.map(opt => opt.label).join('\n');
    dialog.show();
}

function show_payment_summary_dialog(frm) {
    frappe.call({
        method: 'property_manager.utils.payment_entry.get_payment_schedule_status',
        args: {
            rental_payment_schedule: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let summary = r.message;
                show_summary_dialog(summary);
            }
        }
    });
}

function show_summary_dialog(summary) {
    let dialog = new frappe.ui.Dialog({
        title: __('Payment Summary'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'summary_html'
            }
        ]
    });
    
    let html = `
        <div class="payment-summary">
            <div class="row">
                <div class="col-md-6">
                    <h4>Overview</h4>
                    <table class="table table-bordered">
                        <tr><td>Total Schedules</td><td>${summary.total_schedules}</td></tr>
                        <tr><td>Paid Schedules</td><td>${summary.paid_schedules}</td></tr>
                        <tr><td>Partially Paid</td><td>${summary.partially_paid_schedules}</td></tr>
                        <tr><td>Pending</td><td>${summary.pending_schedules}</td></tr>
                        <tr><td>Overdue</td><td>${summary.overdue_schedules}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h4>Financial</h4>
                    <table class="table table-bordered">
                        <tr><td>Total Amount</td><td>${format_currency(summary.total_amount)}</td></tr>
                        <tr><td>Paid Amount</td><td>${format_currency(summary.paid_amount)}</td></tr>
                        <tr><td>Outstanding</td><td>${format_currency(summary.outstanding_amount)}</td></tr>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    dialog.fields_dict.summary_html.$wrapper.html(html);
    dialog.show();
}

function show_export_dialog(frm) {
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
            },
            {
                fieldtype: 'Date',
                fieldname: 'from_date',
                label: __('From Date')
            },
            {
                fieldtype: 'Date',
                fieldname: 'to_date',
                label: __('To Date')
            }
        ],
        primary_action: function(values) {
            frappe.call({
                method: 'property_manager.utils.reporting.export_payment_data',
                args: {
                    format_type: values.format.toLowerCase(),
                    filters: {
                        rental_payment_schedule: frm.doc.name,
                        from_date: values.from_date,
                        to_date: values.to_date
                    }
                },
                callback: function(r) {
                    if (r.message && !r.message.error) {
                        // Handle export download
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

function show_overdue_analysis(frm) {
    frappe.call({
        method: 'property_manager.utils.reporting.generate_overdue_analysis',
        args: {
            schedules: [frm.doc.name]
        },
        callback: function(r) {
            if (r.message) {
                let analysis = r.message;
                show_overdue_dialog(analysis);
            }
        }
    });
}

function show_overdue_dialog(analysis) {
    let dialog = new frappe.ui.Dialog({
        title: __('Overdue Analysis'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'analysis_html'
            }
        ]
    });
    
    let html = `
        <div class="overdue-analysis">
            <div class="row">
                <div class="col-md-12">
                    <h4>Overdue Summary</h4>
                    <p><strong>Total Overdue Amount:</strong> ${format_currency(analysis.total_overdue_amount)}</p>
                    <p><strong>Number of Overdue Payments:</strong> ${analysis.overdue_count}</p>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <h4>Aging Analysis</h4>
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Age Bucket</th>
                                <th>Count</th>
                                <th>Amount</th>
                            </tr>
                        </thead>
                        <tbody>
    `;
    
    Object.keys(analysis.aging_buckets).forEach(bucket => {
        let data = analysis.aging_buckets[bucket];
        html += `
            <tr>
                <td>${bucket.replace('_', '-')}</td>
                <td>${data.count}</td>
                <td>${format_currency(data.amount)}</td>
            </tr>
        `;
    });
    
    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    dialog.fields_dict.analysis_html.$wrapper.html(html);
    dialog.show();
}

function send_payment_reminders(frm) {
    frappe.confirm(
        __('Send payment reminders for overdue payments?'),
        function() {
            frappe.call({
                method: 'property_manager.utils.notifications.send_payment_reminders',
                args: {
                    rental_payment_schedule: frm.doc.name
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

// Utility functions
function format_currency(value) {
    return frappe.format(value, {fieldtype: 'Currency'});
}

// CSS for payment status styling
frappe.ready(function() {
    $('head').append(`
        <style>
            .payment-paid { background-color: #d4edda !important; }
            .payment-overdue { background-color: #f8d7da !important; }
            .payment-partial { background-color: #fff3cd !important; }
            .payment-pending { background-color: #d1ecf1 !important; }
            
            .payment-dashboard .card {
                margin-bottom: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .payment-dashboard .card-title {
                font-size: 1.5em;
                font-weight: bold;
            }
            
            .overdue-analysis table th {
                background-color: #f8f9fa;
            }
        </style>
    `);
});

