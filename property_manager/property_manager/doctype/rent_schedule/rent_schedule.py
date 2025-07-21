# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta

class RentSchedule(Document):
	def validate(self):
		self.calculate_amounts()
		self.validate_payment_amount()
		self.calculate_overdue_days()
		
	def calculate_amounts(self):
		"""Calculate total amount due and balance"""
		self.total_amount_due = self.rent_amount or 0
		
		# Add late fee if applicable
		if self.status == "Overdue" and self.late_fee_amount and not self.waived_late_fee:
			self.total_amount_due += (self.late_fee_amount - (self.waived_late_fee or 0))
			
		# Calculate balance amount
		self.balance_amount = self.total_amount_due - (self.amount_paid or 0)
		if self.balance_amount < 0:
			self.balance_amount = 0
			
	def validate_payment_amount(self):
		"""Validate payment amount doesn't exceed total due"""
		if self.amount_paid and self.total_amount_due:
			if self.amount_paid > self.total_amount_due:
				frappe.throw("Payment amount cannot exceed total amount due")
				
	def calculate_overdue_days(self):
		"""Calculate days overdue"""
		if self.due_date:
			today = datetime.now().date()
			grace_end_date = self.due_date + timedelta(days=self.grace_period_days or 5)
			
			if today > grace_end_date:
				self.overdue_days = (today - grace_end_date).days
			else:
				self.overdue_days = 0
				
	def before_save(self):
		"""Update status and apply late fees before saving"""
		self.update_payment_status()
		self.apply_late_fees_if_overdue()
		
	def update_payment_status(self):
		"""Update status based on payment amount"""
		if self.amount_paid:
			if self.balance_amount <= 0:
				self.status = "Paid"
				if not self.payment_date:
					self.payment_date = datetime.now().date()
			elif self.amount_paid > 0:
				self.status = "Partially Paid"
		elif self.status == "Paid":
			# Reset status if payment was removed
			if self.overdue_days > 0:
				self.status = "Overdue"
			else:
				self.status = "Pending"
				
	def apply_late_fees_if_overdue(self):
		"""Apply late fees if payment is overdue"""
		if self.overdue_days > 0 and self.status in ["Overdue", "Partially Paid"]:
			if self.late_fee_amount and not self.late_fee_applied_date:
				self.late_fee_applied_date = datetime.now().date()
				
	def on_update(self):
		"""Create sales invoice when payment is made"""
		if self.status == "Paid" and not self.invoice_reference:
			self.create_sales_invoice()
			
	def create_sales_invoice(self):
		"""Create sales invoice when rent is paid"""
		try:
			# Get tenant details
			tenant_doc = frappe.get_doc("Tenant", self.tenant)
			
			# Create customer if doesn't exist
			customer_name = self.get_or_create_customer(tenant_doc)
			
			# Prepare invoice items
			items = []
			
			# Add rent item
			items.append({
				"item_code": self.get_or_create_rent_item(),
				"qty": 1,
				"rate": self.rent_amount,
				"description": f"Rent payment for {self.rental_unit} - Due: {self.due_date}"
			})
			
			# Add late fee item if applicable
			if self.late_fee_amount and (self.late_fee_amount - (self.waived_late_fee or 0)) > 0:
				late_fee_net = self.late_fee_amount - (self.waived_late_fee or 0)
				items.append({
					"item_code": self.get_or_create_late_fee_item(),
					"qty": 1,
					"rate": late_fee_net,
					"description": f"Late fee for {self.rental_unit} - Due: {self.due_date}"
				})
			
			# Create sales invoice
			invoice = frappe.get_doc({
				"doctype": "Sales Invoice",
				"customer": customer_name,
				"posting_date": self.payment_date or datetime.now().date(),
				"due_date": self.due_date,
				"items": items,
				"taxes_and_charges": "",
				"remarks": f"Rent payment for contract {self.rental_contract}"
			})
			
			invoice.insert()
			invoice.submit()
			
			# Update rent schedule with invoice reference
			self.invoice_reference = invoice.name
			self.invoice_status = "Submitted"
			self.invoice_date = invoice.posting_date
			self.save()
			
			frappe.msgprint(f"Sales Invoice {invoice.name} created successfully")
			
		except Exception as e:
			frappe.log_error(f"Error creating sales invoice for rent schedule {self.name}: {str(e)}")
			frappe.throw(f"Error creating sales invoice: {str(e)}")
			
	def get_or_create_customer(self, tenant_doc):
		"""Get or create customer for tenant"""
		if tenant_doc.tenant_type == "Corporate":
			customer_name = tenant_doc.company_name or f"TENANT-{tenant_doc.name}"
			display_name = tenant_doc.company_name
		else:
			customer_name = f"TENANT-{tenant_doc.name}"
			display_name = tenant_doc.get_display_name()
		
		if not frappe.db.exists("Customer", customer_name):
			customer = frappe.get_doc({
				"doctype": "Customer",
				"customer_name": display_name,
				"customer_type": "Individual" if tenant_doc.tenant_type == "Individual" else "Company",
				"customer_group": "Individual" if tenant_doc.tenant_type == "Individual" else "Commercial",
				"territory": "All Territories",
				"email_id": tenant_doc.email,
				"mobile_no": tenant_doc.phone
			})
			customer.insert()
			return customer.name
			
		return customer_name
		
	def get_or_create_rent_item(self):
		"""Get or create rent service item"""
		item_code = "RENT-SERVICE"
		
		if not frappe.db.exists("Item", item_code):
			item = frappe.get_doc({
				"doctype": "Item",
				"item_code": item_code,
				"item_name": "Rent Service",
				"item_group": "Services",
				"stock_uom": "Nos",
				"is_stock_item": 0,
				"is_sales_item": 1,
				"is_service_item": 1,
				"description": "Rental property service"
			})
			item.insert()
			
		return item_code
		
	def get_or_create_late_fee_item(self):
		"""Get or create late fee service item"""
		item_code = "LATE-FEE-SERVICE"
		
		if not frappe.db.exists("Item", item_code):
			item = frappe.get_doc({
				"doctype": "Item",
				"item_code": item_code,
				"item_name": "Late Fee",
				"item_group": "Services",
				"stock_uom": "Nos",
				"is_stock_item": 0,
				"is_sales_item": 1,
				"is_service_item": 1,
				"description": "Late payment fee"
			})
			item.insert()
			
		return item_code
		
	def mark_as_overdue(self):
		"""Mark rent schedule as overdue"""
		if self.status == "Pending":
			self.status = "Overdue"
			self.calculate_amounts()
			self.save()
			
	def waive_late_fee(self, waiver_amount, reason):
		"""Waive late fee partially or fully"""
		if waiver_amount > self.late_fee_amount:
			frappe.throw("Waiver amount cannot exceed late fee amount")
			
		self.waived_late_fee = waiver_amount
		self.waiver_reason = reason
		self.calculate_amounts()
		self.save()
		
	def send_payment_reminder(self):
		"""Send payment reminder to tenant"""
		try:
			tenant_doc = frappe.get_doc("Tenant", self.tenant)
			
			# Prepare email content
			subject = f"Payment Reminder - Rent Due for {self.rental_unit}"
			
			message = f"""
			Dear {tenant_doc.get_display_name()},
			
			This is a reminder that your rent payment for {self.rental_unit} is due.
			
			Due Date: {self.due_date}
			Rent Amount: {frappe.format_value(self.rent_amount, 'Currency')}
			"""
			
			if self.status == "Overdue":
				message += f"""
				Late Fee: {frappe.format_value(self.late_fee_amount, 'Currency')}
				Total Amount Due: {frappe.format_value(self.total_amount_due, 'Currency')}
				Days Overdue: {self.overdue_days}
				"""
			
			message += f"""
			
			Please make your payment as soon as possible.
			
			Thank you,
			Property Management Team
			"""
			
			# Send email
			frappe.sendmail(
				recipients=[tenant_doc.email],
				subject=subject,
				message=message
			)
			
			# Update reminder tracking
			self.reminder_count = (self.reminder_count or 0) + 1
			self.last_reminder_date = datetime.now().date()
			if not self.reminder_sent_date:
				self.reminder_sent_date = datetime.now().date()
			self.save()
			
			frappe.msgprint(f"Payment reminder sent to {tenant_doc.email}")
			
		except Exception as e:
			frappe.log_error(f"Error sending payment reminder for {self.name}: {str(e)}")
			frappe.throw(f"Error sending reminder: {str(e)}")
			
	def get_payment_summary(self):
		"""Get comprehensive payment summary"""
		return {
			"schedule_info": {
				"due_date": self.due_date,
				"rent_amount": self.rent_amount,
				"late_fee_amount": self.late_fee_amount,
				"waived_late_fee": self.waived_late_fee,
				"total_amount_due": self.total_amount_due,
				"status": self.status
			},
			"payment_info": {
				"amount_paid": self.amount_paid,
				"balance_amount": self.balance_amount,
				"payment_date": self.payment_date,
				"payment_method": self.payment_method,
				"payment_reference": self.payment_reference
			},
			"overdue_info": {
				"overdue_days": self.overdue_days,
				"grace_period_days": self.grace_period_days,
				"late_fee_applied_date": self.late_fee_applied_date
			},
			"reminder_info": {
				"reminder_count": self.reminder_count,
				"last_reminder_date": self.last_reminder_date
			},
			"invoice_info": {
				"invoice_reference": self.invoice_reference,
				"invoice_status": self.invoice_status,
				"invoice_date": self.invoice_date
			}
		}

@frappe.whitelist()
def mark_overdue_rents():
	"""Scheduled task to mark overdue rent payments"""
	today = datetime.now().date()
	
	# Get all pending rent schedules past due date + grace period
	pending_schedules = frappe.get_all("Rent Schedule",
		filters={
			"status": "Pending",
			"due_date": ["<", today]
		},
		fields=["name", "due_date", "grace_period_days"]
	)
	
	for schedule in pending_schedules:
		grace_end_date = schedule.due_date + timedelta(days=schedule.grace_period_days or 5)
		if today > grace_end_date:
			schedule_doc = frappe.get_doc("Rent Schedule", schedule.name)
			schedule_doc.mark_as_overdue()
			
@frappe.whitelist()
def send_payment_reminders():
	"""Scheduled task to send payment reminders"""
	today = datetime.now().date()
	
	# Get overdue schedules that haven't been reminded recently
	overdue_schedules = frappe.get_all("Rent Schedule",
		filters={
			"status": ["in", ["Overdue", "Partially Paid"]],
			"last_reminder_date": ["<", today - timedelta(days=7)]  # Last reminder was more than 7 days ago
		},
		fields=["name"]
	)
	
	for schedule in overdue_schedules:
		try:
			schedule_doc = frappe.get_doc("Rent Schedule", schedule.name)
			schedule_doc.send_payment_reminder()
		except Exception as e:
			frappe.log_error(f"Error sending reminder for {schedule.name}: {str(e)}")
			
@frappe.whitelist()
def record_payment(rent_schedule_name, amount_paid, payment_date=None, payment_method=None, payment_reference=None):
	"""Record payment for rent schedule"""
	schedule_doc = frappe.get_doc("Rent Schedule", rent_schedule_name)
	
	schedule_doc.amount_paid = (schedule_doc.amount_paid or 0) + float(amount_paid)
	schedule_doc.payment_date = payment_date or datetime.now().date()
	schedule_doc.payment_method = payment_method
	schedule_doc.payment_reference = payment_reference
	
	schedule_doc.save()
	
	return schedule_doc.get_payment_summary()
