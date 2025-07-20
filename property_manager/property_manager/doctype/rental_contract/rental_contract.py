# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class RentalContract(Document):
	def validate(self):
		self.validate_dates()
		self.validate_rent_amount()
		self.validate_unit_availability()
		
	def validate_dates(self):
		if self.start_date >= self.end_date:
			frappe.throw("End date must be after start date")
			
	def validate_rent_amount(self):
		if self.rent_amount <= 0:
			frappe.throw("Rent amount must be greater than 0")
			
	def validate_unit_availability(self):
		# Check if unit is available for the contract period
		if self.rental_unit:
			overlapping_contracts = frappe.db.sql("""
				SELECT name FROM `tabRental Contract`
				WHERE rental_unit = %s
				AND contract_status = 'Active'
				AND name != %s
				AND (
					(start_date <= %s AND end_date >= %s) OR
					(start_date <= %s AND end_date >= %s) OR
					(start_date >= %s AND end_date <= %s)
				)
			""", (self.rental_unit, self.name, self.start_date, self.start_date, 
				  self.end_date, self.end_date, self.start_date, self.end_date))
			
			if overlapping_contracts:
				frappe.throw(f"Unit {self.rental_unit} is not available for the selected period")
				
	def before_insert(self):
		self.created_by = frappe.session.user
		self.creation_date = datetime.now()
		
	def on_submit(self):
		# Mark unit as occupied
		if self.rental_unit:
			unit_doc = frappe.get_doc("Rental Unit", self.rental_unit)
			unit_doc.mark_as_occupied()
			
		# Set contract as active
		self.contract_status = "Active"
		self.save()
		
		# Generate rent schedules
		self.generate_rent_schedules()
		
	def on_cancel(self):
		# Mark unit as available
		if self.rental_unit:
			unit_doc = frappe.get_doc("Rental Unit", self.rental_unit)
			unit_doc.mark_as_available()
			
		# Cancel all pending rent schedules
		rent_schedules = frappe.get_all("Rent Schedule", 
			filters={"rental_contract": self.name, "status": ["in", ["Pending", "Overdue"]]})
		for schedule in rent_schedules:
			schedule_doc = frappe.get_doc("Rent Schedule", schedule.name)
			schedule_doc.cancel()
			
	def generate_rent_schedules(self):
		"""Generate rent payment schedules based on payment frequency"""
		if self.payment_frequency == "Monthly":
			self.generate_monthly_schedules()
		elif self.payment_frequency == "Weekly":
			self.generate_weekly_schedules()
		elif self.payment_frequency == "Bi-weekly":
			self.generate_biweekly_schedules()
		elif self.payment_frequency == "Quarterly":
			self.generate_quarterly_schedules()
		elif self.payment_frequency == "Annually":
			self.generate_annual_schedules()
			
	def generate_monthly_schedules(self):
		"""Generate monthly rent schedules"""
		current_date = self.start_date
		while current_date <= self.end_date:
			# Set due date to the specified day of month
			due_date = current_date.replace(day=self.payment_due_day)
			if due_date < current_date:
				due_date = due_date + relativedelta(months=1)
				
			if due_date <= self.end_date:
				self.create_rent_schedule(due_date)
				
			current_date = current_date + relativedelta(months=1)
			
	def generate_weekly_schedules(self):
		"""Generate weekly rent schedules"""
		current_date = self.start_date
		weekly_amount = self.rent_amount / 4.33  # Average weeks per month
		
		while current_date <= self.end_date:
			self.create_rent_schedule(current_date, weekly_amount)
			current_date = current_date + timedelta(weeks=1)
			
	def generate_biweekly_schedules(self):
		"""Generate bi-weekly rent schedules"""
		current_date = self.start_date
		biweekly_amount = self.rent_amount / 2.17  # Average bi-weeks per month
		
		while current_date <= self.end_date:
			self.create_rent_schedule(current_date, biweekly_amount)
			current_date = current_date + timedelta(weeks=2)
			
	def generate_quarterly_schedules(self):
		"""Generate quarterly rent schedules"""
		current_date = self.start_date
		quarterly_amount = self.rent_amount * 3
		
		while current_date <= self.end_date:
			due_date = current_date.replace(day=self.payment_due_day)
			if due_date < current_date:
				due_date = due_date + relativedelta(months=3)
				
			if due_date <= self.end_date:
				self.create_rent_schedule(due_date, quarterly_amount)
				
			current_date = current_date + relativedelta(months=3)
			
	def generate_annual_schedules(self):
		"""Generate annual rent schedules"""
		current_date = self.start_date
		annual_amount = self.rent_amount * 12
		
		while current_date <= self.end_date:
			due_date = current_date.replace(day=self.payment_due_day)
			if due_date < current_date:
				due_date = due_date + relativedelta(years=1)
				
			if due_date <= self.end_date:
				self.create_rent_schedule(due_date, annual_amount)
				
			current_date = current_date + relativedelta(years=1)
			
	def create_rent_schedule(self, due_date, amount=None):
		"""Create a rent schedule entry"""
		if amount is None:
			amount = self.rent_amount
			
		rent_schedule = frappe.get_doc({
			"doctype": "Rent Schedule",
			"rental_contract": self.name,
			"tenant": self.tenant,
			"rental_unit": self.rental_unit,
			"due_date": due_date,
			"rent_amount": amount,
			"late_fee_amount": self.late_fee_amount or 0,
			"grace_period_days": self.grace_period_days or 5,
			"status": "Pending"
		})
		rent_schedule.insert()
		
def generate_rent_schedules(doc, method):
	"""Hook function to generate rent schedules on contract submission"""
	if doc.doctype == "Rental Contract" and method == "on_submit":
		doc.generate_rent_schedules()

