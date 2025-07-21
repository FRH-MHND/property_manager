# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from frappe.utils import getdate, flt

class RentalPaymentSchedule(Document):
	def validate(self):
		self.populate_contract_details()
		self.calculate_totals()
		self.validate_payment_schedules()
		
	def populate_contract_details(self):
		"""Populate details from rental contract"""
		if self.rental_contract:
			contract = frappe.get_doc("Rental Contract", self.rental_contract)
			self.tenant = contract.tenant
			self.property = contract.property
			self.rental_unit = contract.rental_unit
			self.start_date = contract.start_date
			self.end_date = contract.end_date
			self.payment_frequency = contract.payment_frequency
			
	def calculate_totals(self):
		"""Calculate total amounts from payment schedules"""
		if not self.payment_schedules:
			return
			
		total_amount = 0
		paid_amount = 0
		
		for schedule in self.payment_schedules:
			total_amount += flt(schedule.payment_amount)
			paid_amount += flt(schedule.paid_amount)
			
		self.total_rent_amount = total_amount
		self.paid_amount = paid_amount
		self.outstanding_amount = total_amount - paid_amount
		self.payments_count = len(self.payment_schedules)
		
		# Update status based on payments
		self.update_schedule_status()
		
	def validate_payment_schedules(self):
		"""Validate payment schedule entries"""
		if not self.payment_schedules:
			frappe.throw("At least one payment schedule is required")
			
		# Check for duplicate due dates
		due_dates = []
		for schedule in self.payment_schedules:
			if schedule.due_date in due_dates:
				frappe.throw(f"Duplicate due date found: {schedule.due_date}")
			due_dates.append(schedule.due_date)
			
		# Validate payment amounts
		for schedule in self.payment_schedules:
			if flt(schedule.payment_amount) <= 0:
				frappe.throw("Payment amount must be greater than 0")
				
	def update_schedule_status(self):
		"""Update schedule status based on payment progress"""
		if self.outstanding_amount <= 0:
			self.schedule_status = "Completed"
		elif self.paid_amount > 0:
			# Check if any payments are overdue
			today = datetime.now().date()
			overdue_payments = [s for s in self.payment_schedules 
							   if getdate(s.due_date) < today and flt(s.outstanding) > 0]
			if overdue_payments:
				self.schedule_status = "Overdue"
			else:
				self.schedule_status = "Active"
		elif self.schedule_status == "Draft":
			self.schedule_status = "Active"
			
	def before_insert(self):
		"""Set creation information"""
		self.created_by = frappe.session.user
		self.created_date = datetime.now()
		
	def before_save(self):
		"""Update last modified timestamp"""
		self.last_updated = datetime.now()
		
	def on_submit(self):
		"""Actions when payment schedule is submitted"""
		self.schedule_status = "Active"
		self.save()
		
		# Update rental contract with payment schedule reference
		if self.rental_contract:
			contract = frappe.get_doc("Rental Contract", self.rental_contract)
			contract.payment_schedule_reference = self.name
			contract.save()
			
	def on_cancel(self):
		"""Actions when payment schedule is cancelled"""
		self.schedule_status = "Cancelled"
		self.save()
		
		# Remove reference from rental contract
		if self.rental_contract:
			contract = frappe.get_doc("Rental Contract", self.rental_contract)
			contract.payment_schedule_reference = None
			contract.save()
			
	def generate_payment_schedule(self):
		"""Generate payment schedule based on contract terms"""
		if not self.rental_contract:
			frappe.throw("Rental Contract is required to generate payment schedule")
			
		contract = frappe.get_doc("Rental Contract", self.rental_contract)
		
		# Clear existing schedules
		self.payment_schedules = []
		
		# Generate based on payment frequency
		if contract.payment_frequency == "Monthly":
			self.generate_monthly_payments(contract)
		elif contract.payment_frequency == "Weekly":
			self.generate_weekly_payments(contract)
		elif contract.payment_frequency == "Bi-weekly":
			self.generate_biweekly_payments(contract)
		elif contract.payment_frequency == "Quarterly":
			self.generate_quarterly_payments(contract)
		elif contract.payment_frequency == "Annually":
			self.generate_annual_payments(contract)
			
		self.calculate_totals()
		
	def generate_monthly_payments(self, contract):
		"""Generate monthly payment schedule"""
		start_date = getdate(contract.start_date)
		end_date = getdate(contract.end_date)
		current_date = start_date
		
		while current_date <= end_date:
			# Set due date to the specified day of month
			try:
				payment_day = int(contract.payment_due_day or 1)
				due_date = current_date.replace(day=min(payment_day, 28))
			except (ValueError, TypeError):
				due_date = current_date.replace(day=1)
				
			if due_date < current_date:
				due_date = due_date + relativedelta(months=1)
				
			if due_date <= end_date:
				self.add_payment_schedule_item(due_date, contract.monthly_rent)
				
			current_date = current_date + relativedelta(months=1)
			
	def generate_weekly_payments(self, contract):
		"""Generate weekly payment schedule"""
		start_date = getdate(contract.start_date)
		end_date = getdate(contract.end_date)
		current_date = start_date
		weekly_amount = flt(contract.monthly_rent) / 4.33  # Average weeks per month
		
		while current_date <= end_date:
			self.add_payment_schedule_item(current_date, weekly_amount)
			current_date = current_date + timedelta(weeks=1)
			
	def generate_biweekly_payments(self, contract):
		"""Generate bi-weekly payment schedule"""
		start_date = getdate(contract.start_date)
		end_date = getdate(contract.end_date)
		current_date = start_date
		biweekly_amount = flt(contract.monthly_rent) / 2.17  # Average bi-weeks per month
		
		while current_date <= end_date:
			# First payment on 1st
			due_date_1 = current_date.replace(day=1)
			if due_date_1 >= current_date and due_date_1 <= end_date:
				self.add_payment_schedule_item(due_date_1, biweekly_amount)
				
			# Second payment on 15th
			try:
				due_date_15 = current_date.replace(day=15)
				if due_date_15 >= current_date and due_date_15 <= end_date:
					self.add_payment_schedule_item(due_date_15, biweekly_amount)
			except:
				pass
				
			current_date = current_date + relativedelta(months=1)
			
	def generate_quarterly_payments(self, contract):
		"""Generate quarterly payment schedule"""
		start_date = getdate(contract.start_date)
		end_date = getdate(contract.end_date)
		current_date = start_date
		quarterly_amount = flt(contract.monthly_rent) * 3
		
		while current_date <= end_date:
			try:
				payment_day = int(contract.payment_due_day or 1)
				due_date = current_date.replace(day=min(payment_day, 28))
			except (ValueError, TypeError):
				due_date = current_date.replace(day=1)
				
			if due_date < current_date:
				due_date = due_date + relativedelta(months=3)
				
			if due_date <= end_date:
				self.add_payment_schedule_item(due_date, quarterly_amount)
				
			current_date = current_date + relativedelta(months=3)
			
	def generate_annual_payments(self, contract):
		"""Generate annual payment schedule"""
		start_date = getdate(contract.start_date)
		end_date = getdate(contract.end_date)
		current_date = start_date
		annual_amount = flt(contract.monthly_rent) * 12
		
		while current_date <= end_date:
			try:
				payment_day = int(contract.payment_due_day or 1)
				due_date = current_date.replace(day=min(payment_day, 28))
			except (ValueError, TypeError):
				due_date = current_date.replace(day=1)
				
			if due_date < current_date:
				due_date = due_date + relativedelta(years=1)
				
			if due_date <= end_date:
				self.add_payment_schedule_item(due_date, annual_amount)
				
			current_date = current_date + relativedelta(years=1)
			
	def add_payment_schedule_item(self, due_date, amount):
		"""Add a payment schedule item"""
		self.append("payment_schedules", {
			"due_date": due_date,
			"payment_amount": amount,
			"outstanding": amount,
			"paid_amount": 0,
			"discounted_amount": 0
		})
		
	def record_payment(self, due_date, paid_amount, payment_date=None):
		"""Record payment for a specific due date"""
		if not payment_date:
			payment_date = datetime.now().date()
			
		for schedule in self.payment_schedules:
			if getdate(schedule.due_date) == getdate(due_date):
				schedule.paid_amount = flt(schedule.paid_amount) + flt(paid_amount)
				schedule.outstanding = flt(schedule.payment_amount) - flt(schedule.paid_amount)
				
				if schedule.outstanding <= 0:
					schedule.outstanding = 0
					
				break
		else:
			frappe.throw(f"No payment schedule found for due date: {due_date}")
			
		self.calculate_totals()
		self.save()
		
		# Create sales invoice if needed
		self.create_sales_invoice_for_payment(due_date, paid_amount, payment_date)
		
	def create_sales_invoice_for_payment(self, due_date, paid_amount, payment_date):
		"""Create sales invoice for the payment"""
		try:
			# Get tenant details
			tenant_doc = frappe.get_doc("Tenant", self.tenant)
			
			# Create customer if doesn't exist
			customer_name = self.get_or_create_customer(tenant_doc)
			
			# Create sales invoice
			invoice = frappe.get_doc({
				"doctype": "Sales Invoice",
				"customer": customer_name,
				"posting_date": payment_date,
				"due_date": due_date,
				"items": [{
					"item_code": self.get_or_create_rent_item(),
					"qty": 1,
					"rate": paid_amount,
					"description": f"Rent payment for {self.rental_unit} - Due: {due_date}"
				}],
				"taxes_and_charges": "",
				"remarks": f"Rent payment for contract {self.rental_contract}"
			})
			
			invoice.insert()
			invoice.submit()
			
			# Update payment schedule with invoice reference
			for schedule in self.payment_schedules:
				if getdate(schedule.due_date) == getdate(due_date):
					schedule.invoice = invoice.name
					break
					
			self.save()
			
			frappe.msgprint(f"Sales Invoice {invoice.name} created successfully")
			
		except Exception as e:
			frappe.log_error(f"Error creating sales invoice: {str(e)}")
			
	def get_or_create_customer(self, tenant_doc):
		"""Get or create customer for tenant"""
		if hasattr(tenant_doc, 'tenant_type') and tenant_doc.tenant_type == "Corporate":
			customer_name = tenant_doc.company_name or f"TENANT-{tenant_doc.name}"
			display_name = tenant_doc.company_name
		else:
			customer_name = f"TENANT-{tenant_doc.name}"
			if hasattr(tenant_doc, 'first_name') and hasattr(tenant_doc, 'last_name'):
				display_name = f"{tenant_doc.first_name} {tenant_doc.last_name}"
			else:
				display_name = tenant_doc.tenant_name or tenant_doc.name
		
		if not frappe.db.exists("Customer", customer_name):
			customer = frappe.get_doc({
				"doctype": "Customer",
				"customer_name": display_name,
				"customer_type": "Individual" if not hasattr(tenant_doc, 'tenant_type') or tenant_doc.tenant_type == "Individual" else "Company",
				"customer_group": "Individual" if not hasattr(tenant_doc, 'tenant_type') or tenant_doc.tenant_type == "Individual" else "Commercial",
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
		
	def get_payment_summary(self):
		"""Get comprehensive payment summary"""
		overdue_payments = []
		upcoming_payments = []
		completed_payments = []
		
		today = datetime.now().date()
		
		for schedule in self.payment_schedules:
			due_date = getdate(schedule.due_date)
			outstanding = flt(schedule.outstanding)
			
			if outstanding <= 0:
				completed_payments.append(schedule)
			elif due_date < today:
				overdue_payments.append(schedule)
			else:
				upcoming_payments.append(schedule)
				
		return {
			"total_payments": len(self.payment_schedules),
			"completed_payments": len(completed_payments),
			"overdue_payments": len(overdue_payments),
			"upcoming_payments": len(upcoming_payments),
			"total_amount": self.total_rent_amount,
			"paid_amount": self.paid_amount,
			"outstanding_amount": self.outstanding_amount,
			"overdue_amount": sum(flt(s.outstanding) for s in overdue_payments),
			"next_payment_date": min([getdate(s.due_date) for s in upcoming_payments]) if upcoming_payments else None,
			"next_payment_amount": next((flt(s.payment_amount) for s in upcoming_payments 
										if getdate(s.due_date) == min([getdate(s.due_date) for s in upcoming_payments])), 0) if upcoming_payments else 0
		}

@frappe.whitelist()
def create_payment_schedule_from_contract(rental_contract):
	"""Create payment schedule from rental contract"""
	# Check if payment schedule already exists
	existing = frappe.db.exists("Rental Payment Schedule", {"rental_contract": rental_contract})
	if existing:
		frappe.throw(f"Payment schedule already exists for contract {rental_contract}")
		
	# Create new payment schedule
	payment_schedule = frappe.get_doc({
		"doctype": "Rental Payment Schedule",
		"rental_contract": rental_contract
	})
	
	payment_schedule.generate_payment_schedule()
	payment_schedule.insert()
	payment_schedule.submit()
	
	return payment_schedule.name

@frappe.whitelist()
def record_rental_payment(payment_schedule_name, due_date, paid_amount, payment_date=None):
	"""Record payment for rental payment schedule"""
	payment_schedule = frappe.get_doc("Rental Payment Schedule", payment_schedule_name)
	payment_schedule.record_payment(due_date, paid_amount, payment_date)
	
	return payment_schedule.get_payment_summary()