# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Property(Document):
	def validate(self):
		self.validate_owner_email()
		
	def validate_owner_email(self):
		if self.owner_email and "@" not in self.owner_email:
			frappe.throw("Please enter a valid email address")
			
	def on_update(self):
		# Update total units count based on rental units
		total_units = frappe.db.count("Rental Unit", {"property": self.name})
		if total_units != self.total_units:
			frappe.db.set_value("Property", self.name, "total_units", total_units)
			
	def get_available_units(self):
		"""Get list of available rental units for this property"""
		return frappe.get_all("Rental Unit", 
			filters={"property": self.name, "status": "Available"},
			fields=["name", "unit_number", "unit_type", "base_rent", "furnished_status"]
		)
		
	def get_occupied_units(self):
		"""Get list of occupied rental units for this property"""
		return frappe.get_all("Rental Unit", 
			filters={"property": self.name, "status": "Occupied"},
			fields=["name", "unit_number", "unit_type", "base_rent", "furnished_status"]
		)

