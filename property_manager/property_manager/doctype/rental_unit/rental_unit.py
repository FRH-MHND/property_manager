# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class RentalUnit(Document):
	def validate(self):
		self.validate_rent_amount()
		self.validate_unit_number_unique()
		self.validate_maintenance_dates()
		
	def validate_rent_amount(self):
		"""Validate rent amount is positive"""
		if self.monthly_rent <= 0:
			frappe.throw("Monthly rent amount must be greater than 0")
			
	def validate_unit_number_unique(self):
		"""Check if unit number is unique within the property"""
		existing = frappe.db.exists("Rental Unit", {
			"property": self.property,
			"unit_number": self.unit_number,
			"name": ["!=", self.name]
		})
		if existing:
			frappe.throw(f"Unit number {self.unit_number} already exists in {self.property}")
			
	def validate_maintenance_dates(self):
		"""Validate maintenance date logic"""
		if self.last_maintenance_date and self.next_maintenance_date:
			if self.next_maintenance_date <= self.last_maintenance_date:
				frappe.throw("Next maintenance date must be after last maintenance date")
				
	def on_update(self):
		"""Update property's unit counts when unit is updated"""
		if self.property:
			property_doc = frappe.get_doc("Property", self.property)
			property_doc.update_unit_counts()
			
	def update_lease_info(self, contract_doc=None):
		"""Update current lease information from active contract"""
		if contract_doc:
			# Update from provided contract
			self.current_tenant = contract_doc.tenant
			self.lease_start_date = contract_doc.start_date
			self.lease_end_date = contract_doc.end_date
		else:
			# Find active contract
			active_contract = frappe.db.get_value("Rental Contract", {
				"rental_unit": self.name,
				"contract_status": "Active"
			}, ["tenant", "start_date", "end_date"], as_dict=True)
			
			if active_contract:
				self.current_tenant = active_contract.tenant
				self.lease_start_date = active_contract.start_date
				self.lease_end_date = active_contract.end_date
			else:
				# Clear lease info if no active contract
				self.current_tenant = None
				self.lease_start_date = None
				self.lease_end_date = None
				
		self.save()
		
	def get_current_tenant(self):
		"""Get current tenant for this unit"""
		if self.current_tenant:
			return frappe.get_doc("Tenant", self.current_tenant)
		return None
		
	def get_active_contract(self):
		"""Get active rental contract for this unit"""
		return frappe.db.get_value("Rental Contract", {
			"rental_unit": self.name,
			"contract_status": "Active"
		}, ["name", "tenant", "start_date", "end_date", "monthly_rent"], as_dict=True)
		
	def get_rental_history(self):
		"""Get rental history for this unit"""
		return frappe.get_all("Rental Contract",
			filters={"rental_unit": self.name},
			fields=["name", "tenant", "start_date", "end_date", "monthly_rent", "contract_status"],
			order_by="start_date desc"
		)
		
	def mark_as_occupied(self, contract_doc=None):
		"""Mark unit as occupied and update lease info"""
		self.unit_status = "Occupied"
		if contract_doc:
			self.update_lease_info(contract_doc)
		else:
			self.save()
		
	def mark_as_available(self):
		"""Mark unit as available and clear lease info"""
		self.unit_status = "Available"
		self.current_tenant = None
		self.lease_start_date = None
		self.lease_end_date = None
		self.save()
		
	def mark_for_maintenance(self, maintenance_date=None):
		"""Mark unit for maintenance"""
		self.unit_status = "Maintenance"
		self.maintenance_status = "Scheduled"
		if maintenance_date:
			self.next_maintenance_date = maintenance_date
		self.save()
		
	def complete_maintenance(self, completion_date=None):
		"""Mark maintenance as completed"""
		if completion_date:
			self.last_maintenance_date = completion_date
		self.maintenance_status = "Completed"
		
		# Return to previous status (Available or Occupied)
		if self.current_tenant:
			self.unit_status = "Occupied"
		else:
			self.unit_status = "Available"
			
		self.save()
		
	def get_unit_summary(self):
		"""Get comprehensive unit summary"""
		active_contract = self.get_active_contract()
		rental_history = self.get_rental_history()
		
		return {
			"unit_info": {
				"property": self.property,
				"unit_number": self.unit_number,
				"unit_type": self.unit_type,
				"square_footage": self.square_footage,
				"bedrooms": self.bedrooms,
				"bathrooms": self.bathrooms
			},
			"rental_info": {
				"monthly_rent": self.monthly_rent,
				"security_deposit": self.security_deposit,
				"furnished_status": self.furnished_status,
				"unit_status": self.unit_status
			},
			"current_lease": active_contract,
			"rental_history_count": len(rental_history),
			"maintenance_status": self.maintenance_status,
			"amenities": self.amenities
		}
		
	def is_available_for_period(self, start_date, end_date):
		"""Check if unit is available for a specific period"""
		if self.unit_status not in ["Available", "Occupied"]:
			return False, f"Unit is currently {self.unit_status}"
			
		# Check for overlapping contracts
		overlapping_contracts = frappe.db.sql("""
			SELECT name FROM `tabRental Contract`
			WHERE rental_unit = %s
			AND contract_status = 'Active'
			AND (
				(start_date <= %s AND end_date >= %s) OR
				(start_date <= %s AND end_date >= %s) OR
				(start_date >= %s AND end_date <= %s)
			)
		""", (self.name, start_date, start_date, end_date, end_date, start_date, end_date))
		
		if overlapping_contracts:
			return False, "Unit is already rented for this period"
			
		return True, "Unit is available"
		
	def calculate_prorated_rent(self, start_date, end_date):
		"""Calculate prorated rent for partial month"""
		from datetime import datetime
		from calendar import monthrange
		
		if not isinstance(start_date, datetime):
			start_date = datetime.strptime(str(start_date), "%Y-%m-%d")
		if not isinstance(end_date, datetime):
			end_date = datetime.strptime(str(end_date), "%Y-%m-%d")
			
		# Get days in the month
		days_in_month = monthrange(start_date.year, start_date.month)[1]
		
		# Calculate days to charge
		if start_date.month == end_date.month:
			days_to_charge = (end_date - start_date).days + 1
		else:
			# Handle cross-month scenarios
			days_to_charge = days_in_month - start_date.day + 1
			
		# Calculate prorated amount
		daily_rate = self.monthly_rent / days_in_month
		prorated_amount = daily_rate * days_to_charge
		
		return prorated_amount