# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta

class RentSchedule(Document):
	def validate(self):
		self.calculate_total_amount_due()
		self.validate_payment_amount()
		
	def calculate_total_amount_due(self):
		"""Calculate total amount due including late fees"""
		self.total_amount_due = self.rent_amount
		
		# Add late fee if payment is overdue
		if self.status == "Overdue" and self.late_fee_amount:
			self.total_amount_due += self.late_fee_amount
			
	def validate_payment_amount(self):
		"""Validate payment amount doesn't exceed total due"""
		if self.amount_paid and self.total_amount_due:
			if self.amount_paid > self.total_amount_due:
				frappe.throw("Payment amount cannot exceed total amount due")
				
	def before_save(self):
		# Update status based on payment
		if self.amount_paid:
			if self.amount_paid >= self.total_amount_due:
				self.status = "Paid"
				if not self.payment_date:
					self.payment_date = datetime.now().date()
			elif self.amount_paid > 0:
				self.status = "Partially Paid"
				
	def on_update(self):
		# Create sales invoice when payment is made
		if self.status == "Paid" and not self.invoice_reference:
			self.create_sales_invoice()
			
	def create_sales_invoice(self):
		"""Create sales invoice when rent is paid"""
		try:
			# Get tenant details
			tenant_doc = frappe.get_doc("Tenant", self.tenant)
			
			# Create customer if doesn't exist
			customer_name = self.get_or_create_customer(tenant_doc)
			
			# Create sales invoice
			invoice = frappe.get_doc({
				"doctype": "Sales Invoice",
				"customer": customer_name,
				"posting_date": self.payment_date or datetime.now().date(),
				"due_date": self.due_date,
				"items": [{
					"item_code": self.get_or_create_rent_item(),
					"qty": 1,
					"rate": self.amount_paid,
					"description": f"Rent payment for {self.rental_unit} - Due: {self.due_date}"
				}],
				"taxes_and_charges": "",
				"remarks": f"Rent payment for contract {self.rental_contract}"
			})
			
			invoice.insert()
			invoice.submit()
			
			# Update rent schedule with invoice reference
			self.invoice_reference = invoice.name
			self.save()
			
			frappe.msgprint(f"Sales Invoice {invoice.name} created successfully")
			
		except Exception as e:
			frappe.log_error(f"Error creating sales invoice for rent schedule {self.name}: {str(e)}")
			
	def get_or_create_customer(self, tenant_doc):
		"""Get or create customer for tenant"""
		customer_name = f"TENANT-{tenant_doc.name}"
		
		if not frappe.db.exists("Customer", customer_name):
			customer = frappe.get_doc({
				"doctype": "Customer",
				"customer_name": tenant_doc.tenant_name,
				"customer_type": "Individual",
				"customer_group": "Individual",
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
		
	def mark_as_overdue(self):
		"""Mark rent schedule as overdue"""
		if self.status == "Pending":
			self.status = "Overdue"
			self.calculate_total_amount_due()
			self.save()
			
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
def generate_monthly_schedules():
	"""Scheduled task to generate upcoming monthly rent schedules"""
	# This can be used to generate schedules for long-term contracts
	pass
	
def create_sales_invoice_on_payment(doc, method):
	"""Hook function to create sales invoice when payment is updated"""
	if doc.doctype == "Rent Schedule" and method == "on_update":
		if doc.status == "Paid" and not doc.invoice_reference:
			doc.create_sales_invoice()

