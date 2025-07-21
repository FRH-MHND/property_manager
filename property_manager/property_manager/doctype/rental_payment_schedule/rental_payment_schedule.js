// Copyright (c) 2025, Farah and contributors
// For license information, please see license.txt

frappe.ui.form.on('Rental Payment Schedule', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Generate Schedule'), function() {
				frm.call('generate_payment_schedule').then(() => {
					frm.refresh();
				});
			});
		}
		
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Record Payment'), function() {
				show_payment_dialog(frm);
			});
			
			frm.add_custom_button(__('Payment Summary'), function() {
				show_payment_summary(frm);
			});
		}
		
		// Set color indicators
		if (frm.doc.schedule_status === 'Overdue') {
			frm.dashboard.set_headline_alert('<div class="row"><div class="col-xs-12"><span class="indicator red">Overdue Payments</span></div></div>');
		} else if (frm.doc.schedule_status === 'Completed') {
			frm.dashboard.set_headline_alert('<div class="row"><div class="col-xs-12"><span class="indicator green">All Payments Completed</span></div></div>');
		}
	},
	
	rental_contract: function(frm) {
		if (frm.doc.rental_contract) {
			// Auto-populate contract details
			frm.call('populate_contract_details').then(() => {
				frm.refresh_fields();
			});
		}
	}
});

frappe.ui.form.on('Payment Schedule', {
	paid_amount: function(frm, cdt, cdn) {
		// Recalculate totals when payment amount changes
		frm.call('calculate_totals').then(() => {
			frm.refresh_fields();
		});
	}
});

function show_payment_dialog(frm) {
	let dialog = new frappe.ui.Dialog({
		title: __('Record Payment'),
		fields: [
			{
				fieldtype: 'Select',
				fieldname: 'due_date',
				label: __('Due Date'),
				options: frm.doc.payment_schedules.map(s => s.due_date).join('\n'),
				reqd: 1
			},
			{
				fieldtype: 'Currency',
				fieldname: 'paid_amount',
				label: __('Paid Amount'),
				reqd: 1
			},
			{
				fieldtype: 'Date',
				fieldname: 'payment_date',
				label: __('Payment Date'),
				default: frappe.datetime.get_today()
			}
		],
		primary_action: function(values) {
			frappe.call({
				method: 'property_manager.property_manager.doctype.rental_payment_schedule.rental_payment_schedule.record_rental_payment',
				args: {
					payment_schedule_name: frm.doc.name,
					due_date: values.due_date,
					paid_amount: values.paid_amount,
					payment_date: values.payment_date
				},
				callback: function(r) {
					if (r.message) {
						frm.reload_doc();
						frappe.msgprint(__('Payment recorded successfully'));
					}
				}
			});
			dialog.hide();
		},
		primary_action_label: __('Record Payment')
	});
	
	dialog.show();
}

function show_payment_summary(frm) {
	frm.call('get_payment_summary').then(r => {
		if (r.message) {
			let summary = r.message;
			let html = `
				<div class="row">
					<div class="col-sm-6">
						<h5>Payment Overview</h5>
						<p><strong>Total Payments:</strong> ${summary.total_payments}</p>
						<p><strong>Completed:</strong> ${summary.completed_payments}</p>
						<p><strong>Overdue:</strong> ${summary.overdue_payments}</p>
						<p><strong>Upcoming:</strong> ${summary.upcoming_payments}</p>
					</div>
					<div class="col-sm-6">
						<h5>Financial Summary</h5>
						<p><strong>Total Amount:</strong> ${format_currency(summary.total_amount)}</p>
						<p><strong>Paid Amount:</strong> ${format_currency(summary.paid_amount)}</p>
						<p><strong>Outstanding:</strong> ${format_currency(summary.outstanding_amount)}</p>
						<p><strong>Overdue Amount:</strong> ${format_currency(summary.overdue_amount)}</p>
					</div>
				</div>
			`;
			
			if (summary.next_payment_date) {
				html += `
					<div class="row">
						<div class="col-sm-12">
							<h5>Next Payment</h5>
							<p><strong>Date:</strong> ${summary.next_payment_date}</p>
							<p><strong>Amount:</strong> ${format_currency(summary.next_payment_amount)}</p>
						</div>
					</div>
				`;
			}
			
			frappe.msgprint({
				title: __('Payment Summary'),
				message: html,
				wide: true
			});
		}
	});
}

function format_currency(amount) {
	return frappe.format(amount, {fieldtype: 'Currency'});
}