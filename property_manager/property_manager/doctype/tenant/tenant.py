# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import re

class Tenant(Document):
	def validate(self):
		self.validate_required_fields()
		self.validate_email()
		self.validate_phone()
		self.validate_credit_score()
		self.calculate_monthly_income()
		self.set_full_name()
		
	def validate_required_fields(self):
		"""Validate required fields based on tenant type"""
		if self.tenant_type == "Individual":
			if not self.first_name:
				frappe.throw("First Name is required for Individual tenants")
			if not self.last_name:
				frappe.throw("Last Name is required for Individual tenants")
		elif self.tenant_type == "Corporate":
			if not self.company_name:
				frappe.throw("Company Name is required for Corporate tenants")
			if not self.contact_person:
				frappe.throw("Contact Person is required for Corporate tenants")
		
	def validate_email(self):
		"""Validate email addresses"""
		if self.email and "@" not in self.email:
			frappe.throw("Please enter a valid email address")
		if self.emergency_contact_email and "@" not in self.emergency_contact_email:
			frappe.throw("Please enter a valid emergency contact email address")
			
	def validate_phone(self):
		"""Validate phone numbers"""
		if self.phone:
			# Remove all non-digit characters for validation
			phone_digits = re.sub(r'\D', '', self.phone)
			if len(phone_digits) < 10:
				frappe.throw("Please enter a valid phone number")
				
		if self.emergency_contact_phone:
			emergency_phone_digits = re.sub(r'\D', '', self.emergency_contact_phone)
			if len(emergency_phone_digits) < 10:
				frappe.throw("Please enter a valid emergency contact phone number")
				
	def validate_credit_score(self):
		"""Validate credit score range for individual tenants"""
		if self.tenant_type == "Individual" and self.credit_score:
			if self.credit_score < 300 or self.credit_score > 850:
				frappe.throw("Credit score must be between 300 and 850")
				
	def calculate_monthly_income(self):
		"""Calculate monthly income from annual income for individual tenants"""
		if self.tenant_type == "Individual" and self.annual_income:
			self.monthly_income = self.annual_income / 12
			
	def set_full_name(self):
		"""Set full name for individual tenants"""
		if self.tenant_type == "Individual" and self.first_name and self.last_name:
			self.full_name = f"{self.first_name} {self.last_name}"
			
	def get_display_name(self):
		"""Get display name based on tenant type"""
		if self.tenant_type == "Individual":
			return self.full_name or f"{self.first_name} {self.last_name}"
		else:
			return self.company_name
			
	def get_active_contracts(self):
		"""Get all active rental contracts for this tenant"""
		return frappe.get_all("Rental Contract",
			filters={"tenant": self.name, "contract_status": "Active"},
			fields=["name", "property", "rental_unit", "start_date", "end_date", "monthly_rent", "payment_frequency"]
		)
		
	def get_rental_history(self):
		"""Get complete rental history for this tenant"""
		return frappe.get_all("Rental Contract",
			filters={"tenant": self.name},
			fields=["name", "property", "rental_unit", "start_date", "end_date", "monthly_rent", "contract_status"],
			order_by="start_date desc"
		)
		
	def get_outstanding_payments(self):
		"""Get outstanding rent payments for this tenant"""
		active_contracts = [contract.name for contract in self.get_active_contracts()]
		if not active_contracts:
			return []
			
		return frappe.get_all("Rent Schedule",
			filters={
				"rental_contract": ["in", active_contracts],
				"status": ["in", ["Pending", "Overdue"]]
			},
			fields=["name", "rental_contract", "due_date", "rent_amount", "status", "late_fee"],
			order_by="due_date"
		)
		
	def get_payment_history(self):
		"""Get payment history for this tenant"""
		contracts = [contract.name for contract in self.get_rental_history()]
		if not contracts:
			return []
			
		return frappe.get_all("Rent Schedule",
			filters={
				"rental_contract": ["in", contracts],
				"status": "Paid"
			},
			fields=["name", "rental_contract", "due_date", "rent_amount", "payment_date", "invoice_reference"],
			order_by="payment_date desc"
		)
		
	def get_total_outstanding_amount(self):
		"""Calculate total outstanding amount for this tenant"""
		outstanding_payments = self.get_outstanding_payments()
		total_amount = sum((payment.rent_amount or 0) + (payment.late_fee or 0) for payment in outstanding_payments)
		return total_amount
		
	def get_tenant_summary(self):
		"""Get comprehensive tenant summary"""
		active_contracts = self.get_active_contracts()
		outstanding_payments = self.get_outstanding_payments()
		
		return {
			"tenant_name": self.get_display_name(),
			"tenant_type": self.tenant_type,
			"background_check_status": self.background_check_status,
			"active_contracts": len(active_contracts),
			"outstanding_payments": len(outstanding_payments),
			"total_outstanding": self.get_total_outstanding_amount(),
			"contact_info": {
				"email": self.email,
				"phone": self.phone
			}
		}
		
	def is_eligible_for_lease(self):
		"""Check if tenant is eligible for new lease"""
		# Basic eligibility criteria
		if self.background_check_status != "Passed":
			return False, "Background check not passed"
			
		# Check for outstanding payments
		outstanding_amount = self.get_total_outstanding_amount()
		if outstanding_amount > 0:
			return False, f"Outstanding payments: {outstanding_amount}"
			
		# Check income requirements for individual tenants
		if self.tenant_type == "Individual":
			if not self.annual_income or self.annual_income <= 0:
				return False, "Annual income not provided"
				
		return True, "Eligible for lease"
