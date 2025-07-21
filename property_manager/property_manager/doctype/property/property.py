# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Property(Document):
	def validate(self):
		self.validate_emails()
		self.validate_financial_data()
		
	def validate_emails(self):
		"""Validate email addresses"""
		if self.manager_email and "@" not in self.manager_email:
			frappe.throw("Please enter a valid manager email address")
		if self.owner_email and "@" not in self.owner_email:
			frappe.throw("Please enter a valid owner email address")
			
	def validate_financial_data(self):
		"""Validate financial information"""
		if self.purchase_price and self.purchase_price < 0:
			frappe.throw("Purchase price cannot be negative")
		if self.current_market_value and self.current_market_value < 0:
			frappe.throw("Current market value cannot be negative")
			
	def on_update(self):
		"""Update calculated fields when property is updated"""
		self.update_unit_counts()
		
	def update_unit_counts(self):
		"""Update total units, available units, occupied units, and occupancy rate"""
		# Get total units count
		total_units = frappe.db.count("Rental Unit", {"property": self.name})
		
		# Get available units count
		available_units = frappe.db.count("Rental Unit", {
			"property": self.name, 
			"unit_status": "Available"
		})
		
		# Get occupied units count
		occupied_units = frappe.db.count("Rental Unit", {
			"property": self.name, 
			"unit_status": "Occupied"
		})
		
		# Calculate occupancy rate
		occupancy_rate = 0
		if total_units > 0:
			occupancy_rate = (occupied_units / total_units) * 100
			
		# Update the fields
		frappe.db.set_value("Property", self.name, {
			"total_units": total_units,
			"available_units": available_units,
			"occupied_units": occupied_units,
			"occupancy_rate": occupancy_rate
		})
		
	def get_available_units(self):
		"""Get list of available rental units for this property"""
		return frappe.get_all("Rental Unit", 
			filters={"property": self.name, "unit_status": "Available"},
			fields=["name", "unit_number", "unit_type", "monthly_rent", "furnished_status"]
		)
		
	def get_occupied_units(self):
		"""Get list of occupied rental units for this property"""
		return frappe.get_all("Rental Unit", 
			filters={"property": self.name, "unit_status": "Occupied"},
			fields=["name", "unit_number", "unit_type", "monthly_rent", "furnished_status"]
		)
		
	def get_active_contracts(self):
		"""Get all active rental contracts for this property"""
		return frappe.get_all("Rental Contract",
			filters={"property": self.name, "contract_status": "Active"},
			fields=["name", "tenant", "rental_unit", "start_date", "end_date", "monthly_rent"]
		)
		
	def get_monthly_rental_income(self):
		"""Calculate total monthly rental income from all occupied units"""
		occupied_units = self.get_occupied_units()
		total_income = sum(unit.monthly_rent or 0 for unit in occupied_units)
		return total_income
		
	def get_annual_rental_income(self):
		"""Calculate total annual rental income"""
		return self.get_monthly_rental_income() * 12
		
	def get_property_performance_summary(self):
		"""Get comprehensive property performance data"""
		return {
			"total_units": self.total_units,
			"available_units": self.available_units,
			"occupied_units": self.occupied_units,
			"occupancy_rate": self.occupancy_rate,
			"monthly_income": self.get_monthly_rental_income(),
			"annual_income": self.get_annual_rental_income(),
			"active_contracts": len(self.get_active_contracts())
		}
