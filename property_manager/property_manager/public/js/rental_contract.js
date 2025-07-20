frappe.ui.form.on('Rental Contract', {
    refresh: function(frm) {
        // Add custom buttons
        if (frm.doc.docstatus === 1 && frm.doc.contract_status === 'Active') {
            frm.add_custom_button(__('Generate Rent Schedules'), function() {
                frappe.call({
                    method: 'property_manager.property_manager.doctype.rental_contract.rental_contract.generate_rent_schedules',
                    args: {
                        contract: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint(__('Rent schedules generated successfully'));
                            frm.reload_doc();
                        }
                    }
                });
            });
            
            frm.add_custom_button(__('View Rent Schedules'), function() {
                frappe.route_options = {
                    'rental_contract': frm.doc.name
                };
                frappe.set_route('List', 'Rent Schedule');
            });
        }
        
        // Add terminate contract button
        if (frm.doc.docstatus === 1 && frm.doc.contract_status === 'Active') {
            frm.add_custom_button(__('Terminate Contract'), function() {
                frappe.confirm(
                    'Are you sure you want to terminate this contract?',
                    function() {
                        frappe.call({
                            method: 'frappe.client.set_value',
                            args: {
                                doctype: 'Rental Contract',
                                name: frm.doc.name,
                                fieldname: 'contract_status',
                                value: 'Terminated'
                            },
                            callback: function(r) {
                                frm.reload_doc();
                                frappe.msgprint(__('Contract terminated successfully'));
                            }
                        });
                    }
                );
            }, __('Actions'));
        }
    },
    
    rental_unit: function(frm) {
        // Auto-fill rent amount from unit's base rent
        if (frm.doc.rental_unit) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Rental Unit',
                    filters: {'name': frm.doc.rental_unit},
                    fieldname: ['base_rent', 'security_deposit', 'late_fee_amount']
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('rent_amount', r.message.base_rent);
                        frm.set_value('security_deposit_amount', r.message.security_deposit);
                        frm.set_value('late_fee_amount', r.message.late_fee_amount);
                    }
                }
            });
        }
    },
    
    start_date: function(frm) {
        // Auto-calculate end date based on typical lease terms
        if (frm.doc.start_date && !frm.doc.end_date) {
            let end_date = frappe.datetime.add_months(frm.doc.start_date, 12);
            frm.set_value('end_date', end_date);
        }
    },
    
    payment_frequency: function(frm) {
        // Update payment due day based on frequency
        if (frm.doc.payment_frequency === 'Weekly') {
            frm.set_value('payment_due_day', null);
            frm.set_df_property('payment_due_day', 'hidden', 1);
        } else {
            frm.set_df_property('payment_due_day', 'hidden', 0);
            if (!frm.doc.payment_due_day) {
                frm.set_value('payment_due_day', 1);
            }
        }
    }
});

