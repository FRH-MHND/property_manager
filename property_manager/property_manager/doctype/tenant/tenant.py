# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import re

class Tenant(Document):
	def validate(self):
		self.validate_email()
		self.validate_phone()
		
	def validate_email(self):
		if self.email and "@" not in self.email:
			frappe.throw("Please enter a valid email address")
			
	def validate_phone(self):
		if self.phone:
			# Remove all non-digit characters for validation
			phone_digits = re.sub(r'\D', '', self.phone)
			if len(phone_digits) < 10:
				frappe.throw("Please enter a valid phone number")
				
	def get_active_contracts(self):
		"""Get all active rental contracts for this tenant"""
		return frappe.get_all("Rental Contract",
			filters={"tenant": self.name, "contract_status": "Active"},
			fields=["name", "rental_unit", "start_date", "end_date", "rent_amount", "payment_frequency"]
		)
		
	def get_rental_history(self):
		"""Get complete rental history for this tenant"""
		return frappe.get_all("Rental Contract",
			filters={"tenant": self.name},
			fields=["name", "rental_unit", "start_date", "end_date", "rent_amount", "contract_status"],
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
			fields=["name", "rental_contract", "due_date", "rent_amount", "status"],
			order_by="due_date"
		)
		
	def get_payment_history(self):
		"""Get payment history for this tenant"""
		active_contracts = [contract.name for contract in self.get_active_contracts()]
		if not active_contracts:
			return []
			
		return frappe.get_all("Rent Schedule",
			filters={
				"rental_contract": ["in", active_contracts],
				"status": "Paid"
			},
			fields=["name", "rental_contract", "due_date", "rent_amount", "payment_date", "invoice_reference"],
			order_by="payment_date desc"
		)

