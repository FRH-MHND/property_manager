# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from frappe.utils import getdate

class RentalContract(Document):
	def validate(self):
		self.validate_dates()
		self.validate_rent_amount()
		self.validate_unit_availability()
		self.calculate_amounts()
		self.populate_property()
		
	def validate_dates(self):
		"""Validate contract dates"""
		if self.start_date and self.end_date:
			start_date = getdate(self.start_date)
			end_date = getdate(self.end_date)
			
			if start_date >= end_date:
				frappe.throw("End date must be after start date")
				
			# Validate contract duration is reasonable
			duration = (end_date - start_date).days
			if duration < 7:
				frappe.throw("Contract duration must be at least 7 days")
			
	def validate_rent_amount(self):
		"""Validate rent amount"""
		if self.monthly_rent and self.monthly_rent <= 0:
			frappe.throw("Monthly rent amount must be greater than 0")
			
	def validate_unit_availability(self):
		"""Check if unit is available for the contract period"""
		if self.rental_unit and self.start_date and self.end_date:
			# Skip validation for draft contracts
			if self.contract_status == "Draft":
				return
				
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
			""", (self.rental_unit, self.name or "", self.start_date, self.start_date, 
				  self.end_date, self.end_date, self.start_date, self.end_date))
			
			if overlapping_contracts:
				frappe.throw(f"Unit {self.rental_unit} is not available for the selected period")
				
	def calculate_amounts(self):
		"""Calculate rent amount per payment frequency and total contract value"""
		if not self.monthly_rent:
			return
			
		# Calculate rent amount per payment frequency
		if self.payment_frequency == "Monthly":
			self.rent_amount_per_frequency = self.monthly_rent
		elif self.payment_frequency == "Weekly":
			# Average weeks per month (52 weeks / 12 months = 4.33)
			WEEKS_PER_MONTH = 4.33
			self.rent_amount_per_frequency = self.monthly_rent / WEEKS_PER_MONTH
		elif self.payment_frequency == "Bi-weekly":
			# Average bi-weeks per month (26 bi-weeks / 12 months = 2.17)
			BIWEEKS_PER_MONTH = 2.17
			self.rent_amount_per_frequency = self.monthly_rent / BIWEEKS_PER_MONTH
		elif self.payment_frequency == "Quarterly":
			self.rent_amount_per_frequency = self.monthly_rent * 3
		elif self.payment_frequency == "Annually":
			self.rent_amount_per_frequency = self.monthly_rent * 12
		else:
			self.rent_amount_per_frequency = self.monthly_rent
			
		# Calculate total contract value
		if self.start_date and self.end_date:
			try:
				start_date = getdate(self.start_date)
				end_date = getdate(self.end_date)
				
				# Calculate duration in months
				duration_months = ((end_date.year - start_date.year) * 12 + 
								  (end_date.month - start_date.month) + 
								  (end_date.day - start_date.day) / 30)
				self.total_contract_value = self.monthly_rent * abs(duration_months)
			except:
				# If date calculation fails, use a simple approximation
				self.total_contract_value = self.monthly_rent * 12
		
	def populate_property(self):
		"""Populate property from rental unit"""
		if self.rental_unit and not self.property:
			self.property = frappe.db.get_value("Rental Unit", self.rental_unit, "property")
			
	def before_insert(self):
		"""Set creation information"""
		self.created_by = frappe.session.user
		self.creation_date = datetime.now()
		
	def on_submit(self):
		"""Actions when contract is submitted"""
		# Mark unit as occupied
		if self.rental_unit:
			try:
				unit_doc = frappe.get_doc("Rental Unit", self.rental_unit)
				unit_doc.mark_as_occupied(self)
			except frappe.DoesNotExistError:
				frappe.log_error(f"Rental Unit {self.rental_unit} not found", "Contract Submission Error")
			except Exception as e:
				frappe.log_error(f"Error updating rental unit: {str(e)}", "Contract Submission Error")
			
		# Set contract as active
		self.contract_status = "Active"
		self.approval_date = datetime.now()
		self.approved_by = frappe.session.user
		self.save()
		
		# Generate rent schedules
		self.generate_rent_schedules()
		
		# Update property unit counts
		if self.property:
			try:
				property_doc = frappe.get_doc("Property", self.property)
				property_doc.update_unit_counts()
			except:
				# If property update fails, continue
				pass
		
	def on_cancel(self):
		"""Actions when contract is cancelled"""
		# Mark unit as available
		if self.rental_unit:
			try:
				unit_doc = frappe.get_doc("Rental Unit", self.rental_unit)
				unit_doc.mark_as_available()
			except:
				pass
			
		# Cancel all pending rent schedules
		try:
			rent_schedules = frappe.get_all("Rent Schedule", 
				filters={"rental_contract": self.name, "status": ["in", ["Pending", "Overdue"]]})
			for schedule in rent_schedules:
				schedule_doc = frappe.get_doc("Rent Schedule", schedule.name)
				schedule_doc.cancel()
		except:
			pass
			
		# Update property unit counts
		if self.property:
			try:
				property_doc = frappe.get_doc("Property", self.property)
				property_doc.update_unit_counts()
			except:
				pass
			
	def generate_rent_schedules(self):
		"""Generate rent payment schedules based on payment frequency"""
		try:
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
		except Exception as e:
			frappe.log_error(f"Error generating rent schedules: {str(e)}")
			
	def generate_monthly_schedules(self):
		"""Generate monthly rent schedules"""
		if not self.start_date or not self.end_date:
			return
			
		start_date = getdate(self.start_date)
		end_date = getdate(self.end_date)
		current_date = start_date
		
		while current_date <= end_date:
			# Set due date to the specified day of month
			try:
				payment_day = int(self.payment_due_day or 1)
				due_date = current_date.replace(day=min(payment_day, 28))
			except (ValueError, TypeError):
				due_date = current_date.replace(day=1)
				
			if due_date < current_date:
				due_date = due_date + relativedelta(months=1)
				
			if due_date <= end_date:
				self.create_rent_schedule(due_date, self.monthly_rent)
				
			current_date = current_date + relativedelta(months=1)
			
	def generate_weekly_schedules(self):
		"""Generate weekly rent schedules"""
		if not self.start_date or not self.end_date:
			return
			
		start_date = getdate(self.start_date)
		end_date = getdate(self.end_date)
		current_date = start_date
		
		while current_date <= end_date:
			self.create_rent_schedule(current_date, self.rent_amount_per_frequency or self.monthly_rent)
			current_date = current_date + timedelta(weeks=1)
			
	def generate_biweekly_schedules(self):
		"""Generate bi-weekly rent schedules"""
		if not self.start_date or not self.end_date:
			return
			
		start_date = getdate(self.start_date)
		end_date = getdate(self.end_date)
		current_date = start_date
		
		# For bi-weekly, use 1st and 15th of month
		while current_date <= end_date:
			# First payment on 1st
			due_date_1 = current_date.replace(day=1)
			if due_date_1 >= current_date and due_date_1 <= end_date:
				self.create_rent_schedule(due_date_1, self.rent_amount_per_frequency or (self.monthly_rent / 2))
				
			# Second payment on 15th
			try:
				due_date_15 = current_date.replace(day=15)
				if due_date_15 >= current_date and due_date_15 <= end_date:
					self.create_rent_schedule(due_date_15, self.rent_amount_per_frequency or (self.monthly_rent / 2))
			except:
				pass
				
			current_date = current_date + relativedelta(months=1)
			
	def generate_quarterly_schedules(self):
		"""Generate quarterly rent schedules"""
		if not self.start_date or not self.end_date:
			return
			
		start_date = getdate(self.start_date)
		end_date = getdate(self.end_date)
		current_date = start_date
		
		while current_date <= end_date:
			try:
				payment_day = int(self.payment_due_day or 1)
				due_date = current_date.replace(day=min(payment_day, 28))
			except (ValueError, TypeError):
				due_date = current_date.replace(day=1)
				
			if due_date < current_date:
				due_date = due_date + relativedelta(months=3)
				
			if due_date <= end_date:
				self.create_rent_schedule(due_date, self.rent_amount_per_frequency or (self.monthly_rent * 3))
				
			current_date = current_date + relativedelta(months=3)
			
	def generate_annual_schedules(self):
		"""Generate annual rent schedules"""
		if not self.start_date or not self.end_date:
			return
			
		start_date = getdate(self.start_date)
		end_date = getdate(self.end_date)
		current_date = start_date
		
		while current_date <= end_date:
			try:
				payment_day = int(self.payment_due_day or 1)
				due_date = current_date.replace(day=min(payment_day, 28))
			except (ValueError, TypeError):
				due_date = current_date.replace(day=1)
				
			if due_date < current_date:
				due_date = due_date + relativedelta(years=1)
				
			if due_date <= end_date:
				self.create_rent_schedule(due_date, self.rent_amount_per_frequency or (self.monthly_rent * 12))
				
			current_date = current_date + relativedelta(years=1)
			
	def create_rent_schedule(self, due_date, amount):
		"""Create a rent schedule entry"""
		try:
			rent_schedule = frappe.get_doc({
				"doctype": "Rent Schedule",
				"rental_contract": self.name,
				"tenant": self.tenant,
				"property": self.property,
				"rental_unit": self.rental_unit,
				"due_date": due_date,
				"rent_amount": amount,
				"late_fee_amount": self.late_fee_amount or 0,
				"grace_period_days": self.grace_period_days or 5,
				"status": "Pending"
			})
			rent_schedule.insert()
		except Exception as e:
			frappe.log_error(f"Error creating rent schedule: {str(e)}")
		
	def get_outstanding_amount(self):
		"""Get total outstanding amount for this contract"""
		try:
			outstanding_schedules = frappe.get_all("Rent Schedule",
				filters={
					"rental_contract": self.name,
					"status": ["in", ["Pending", "Overdue", "Partially Paid"]]
				},
				fields=["rent_amount", "late_fee_amount", "amount_paid"]
			)
			
			total_outstanding = 0
			for schedule in outstanding_schedules:
				amount_due = (schedule.rent_amount or 0) + (schedule.late_fee_amount or 0)
				amount_paid = schedule.amount_paid or 0
				total_outstanding += (amount_due - amount_paid)
				
			return total_outstanding
		except:
			return 0
