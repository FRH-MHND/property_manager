frappe.ui.form.on('Rent Schedule', {
    refresh: function(frm) {
        // Add custom buttons
        if (frm.doc.status === 'Pending' || frm.doc.status === 'Overdue') {
            frm.add_custom_button(__('Mark as Paid'), function() {
                let payment_dialog = new frappe.ui.Dialog({
                    title: __('Record Payment'),
                    fields: [
                        {
                            fieldtype: 'Currency',
                            fieldname: 'amount_paid',
                            label: __('Amount Paid'),
                            reqd: 1,
                            default: frm.doc.total_amount_due || frm.doc.rent_amount
                        },
                        {
                            fieldtype: 'Date',
                            fieldname: 'payment_date',
                            label: __('Payment Date'),
                            reqd: 1,
                            default: frappe.datetime.get_today()
                        },
                        {
                            fieldtype: 'Select',
                            fieldname: 'payment_method',
                            label: __('Payment Method'),
                            options: 'Cash\nCheck\nBank Transfer\nCredit Card\nOnline Payment\nOther',
                            default: 'Cash'
                        },
                        {
                            fieldtype: 'Small Text',
                            fieldname: 'notes',
                            label: __('Notes')
                        }
                    ],
                    primary_action_label: __('Record Payment'),
                    primary_action: function(values) {
                        frm.set_value('amount_paid', values.amount_paid);
                        frm.set_value('payment_date', values.payment_date);
                        frm.set_value('payment_method', values.payment_method);
                        if (values.notes) {
                            frm.set_value('notes', values.notes);
                        }
                        frm.save();
                        payment_dialog.hide();
                    }
                });
                payment_dialog.show();
            });
        }
        
        // Add view invoice button
        if (frm.doc.invoice_reference) {
            frm.add_custom_button(__('View Invoice'), function() {
                frappe.set_route('Form', 'Sales Invoice', frm.doc.invoice_reference);
            });
        }
        
        // Add send reminder button
        if (frm.doc.status === 'Overdue') {
            frm.add_custom_button(__('Send Reminder'), function() {
                frappe.call({
                    method: 'property_manager.property_manager.doctype.rent_schedule.rent_schedule.send_payment_reminder',
                    args: {
                        rent_schedule: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint(__('Payment reminder sent successfully'));
                        }
                    }
                });
            }, __('Actions'));
        }
    },
    
    amount_paid: function(frm) {
        // Auto-update status based on payment amount
        if (frm.doc.amount_paid) {
            let total_due = frm.doc.total_amount_due || frm.doc.rent_amount;
            if (frm.doc.amount_paid >= total_due) {
                frm.set_value('status', 'Paid');
                if (!frm.doc.payment_date) {
                    frm.set_value('payment_date', frappe.datetime.get_today());
                }
            } else if (frm.doc.amount_paid > 0) {
                frm.set_value('status', 'Partially Paid');
            }
        }
    },
    
    status: function(frm) {
        // Calculate total amount due when status changes
        if (frm.doc.status === 'Overdue') {
            let total_due = frm.doc.rent_amount;
            if (frm.doc.late_fee_amount) {
                total_due += frm.doc.late_fee_amount;
            }
            frm.set_value('total_amount_due', total_due);
        } else {
            frm.set_value('total_amount_due', frm.doc.rent_amount);
        }
    }
});

