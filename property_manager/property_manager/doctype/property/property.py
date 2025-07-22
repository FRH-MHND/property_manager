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
		# Only run calculations if document is saved (has a name)
		if self.name and not self.name.startswith("new-"):
			self.update_unit_counts()
			self.calculate_financial_metrics()
		
	def update_unit_counts(self):
		"""Update total units, available units, occupied units, and occupancy rate"""
		# Skip if document doesn't have a proper name yet
		if not self.name or self.name.startswith("new-"):
			return
			
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
		
		# Calculate occupancy rate and vacancy rate
		occupancy_rate = 0
		vacancy_rate = 0
		if total_units > 0:
			occupancy_rate = (occupied_units / total_units) * 100
			vacancy_rate = (available_units / total_units) * 100
			
		# Update the fields
		frappe.db.set_value("Property", self.name, {
			"total_units": total_units,
			"available_units": available_units,
			"occupied_units": occupied_units,
			"occupancy_rate": occupancy_rate,
			"vacancy_rate": vacancy_rate
		})
		
	def calculate_financial_metrics(self):
		"""Calculate financial performance metrics"""
		# Skip if document doesn't have a proper name yet
		if not self.name or self.name.startswith("new-"):
			return
			
		# Get rental income data
		monthly_income = self.get_monthly_rental_income()
		potential_income = self.get_potential_monthly_income()
		annual_income = monthly_income * 12
		
		# Calculate average rent
		average_rent = 0
		total_units = self.total_units or 0
		if total_units > 0:
			total_rent = sum(frappe.db.get_value("Rental Unit", unit.name, "monthly_rent") or 0 
							for unit in frappe.get_all("Rental Unit", {"property": self.name}))
			average_rent = total_rent / total_units if total_units > 0 else 0
		
		# Calculate yield and cap rate
		property_value = self.current_market_value or self.purchase_price or 0
		yield_percentage = 0
		cap_rate = 0
		
		if property_value > 0:
			yield_percentage = (annual_income / property_value) * 100
			# Cap rate calculation (simplified - would need operating expenses for accurate calculation)
			cap_rate = yield_percentage  # Using yield as approximation
		
		# Update financial fields
		frappe.db.set_value("Property", self.name, {
			"monthly_rental_income": monthly_income,
			"potential_monthly_income": potential_income,
			"annual_rental_income": annual_income,
			"average_rent_per_unit": average_rent,
			"total_property_value": property_value,
			"yield_percentage": yield_percentage,
			"cap_rate": cap_rate
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
		"""Calculate current monthly rental income from all occupied units"""
		occupied_units = frappe.get_all("Rental Unit", 
			filters={"property": self.name, "unit_status": "Occupied"},
			fields=["monthly_rent"])
		total_income = sum(unit.monthly_rent or 0 for unit in occupied_units)
		return total_income
		
	def get_potential_monthly_income(self):
		"""Calculate potential monthly rental income from all units"""
		all_units = frappe.get_all("Rental Unit", 
			filters={"property": self.name},
			fields=["monthly_rent"])
		potential_income = sum(unit.monthly_rent or 0 for unit in all_units)
		return potential_income
		
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
