# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class RentalUnit(Document):
	def validate(self):
		self.validate_rent_amount()
		self.validate_unit_number_unique()
		
	def validate_rent_amount(self):
		if self.base_rent <= 0:
			frappe.throw("Base rent amount must be greater than 0")
			
	def validate_unit_number_unique(self):
		# Check if unit number is unique within the property
		existing = frappe.db.exists("Rental Unit", {
			"property": self.property,
			"unit_number": self.unit_number,
			"name": ["!=", self.name]
		})
		if existing:
			frappe.throw(f"Unit number {self.unit_number} already exists in {self.property}")
			
	def on_update(self):
		# Update property's total units count
		if self.property:
			property_doc = frappe.get_doc("Property", self.property)
			property_doc.on_update()
			
	def get_current_tenant(self):
		"""Get current tenant for this unit"""
		active_contract = frappe.db.get_value("Rental Contract", {
			"rental_unit": self.name,
			"contract_status": "Active"
		}, "tenant")
		
		if active_contract:
			return frappe.get_doc("Tenant", active_contract)
		return None
		
	def get_rental_history(self):
		"""Get rental history for this unit"""
		return frappe.get_all("Rental Contract",
			filters={"rental_unit": self.name},
			fields=["name", "tenant", "start_date", "end_date", "rent_amount", "contract_status"],
			order_by="start_date desc"
		)
		
	def mark_as_occupied(self):
		"""Mark unit as occupied"""
		self.status = "Occupied"
		self.save()
		
	def mark_as_available(self):
		"""Mark unit as available"""
		self.status = "Available"
		self.save()

