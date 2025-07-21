# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, getdate, nowdate, add_days
from datetime import datetime, timedelta
import json

def link_to_payment_schedule(doc, method):
    """
    Link Payment Entry to corresponding Payment Schedule rows
    Called when Payment Entry is submitted
    """
    try:
        if not doc.party_type == "Customer":
            return
            
        # Find matching rental payment schedules
        matching_schedules = find_matching_payment_schedules(doc)
        
        if not matching_schedules:
            # Log for debugging but don't block the payment
            frappe.log_error(
                f"No matching payment schedules found for Payment Entry {doc.name}",
                "Payment Schedule Linking"
            )
            return
            
        # Process each matching schedule
        for schedule_info in matching_schedules:
            process_payment_schedule_link(doc, schedule_info)
            
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(
            f"Error linking Payment Entry {doc.name} to Payment Schedule: {str(e)}",
            "Payment Schedule Linking Error"
        )
        # Don't throw error to avoid blocking payment submission
        
def unlink_from_payment_schedule(doc, method):
    """
    Unlink Payment Entry from Payment Schedule rows
    Called when Payment Entry is cancelled
    """
    try:
        # Find all Payment Schedule rows linked to this Payment Entry
        linked_schedules = frappe.db.sql("""
            SELECT 
                ps.name as schedule_name,
                ps.parent as payment_schedule_parent,
                ps.parenttype,
                ps.payment_amount,
                ps.paid_amount,
                ps.outstanding
            FROM `tabPayment Schedule` ps
            WHERE ps.payment_entry = %s
        """, (doc.name,), as_dict=True)
        
        for schedule in linked_schedules:
            # Get the parent document
            parent_doc = frappe.get_doc(schedule.parenttype, schedule.payment_schedule_parent)
            
            # Find the specific child row
            for child_row in parent_doc.payment_schedules:
                if child_row.name == schedule.schedule_name:
                    # Revert payment information
                    child_row.payment_entry = None
                    child_row.payment_status = "Pending"
                    child_row.payment_date = None
                    child_row.payment_reference = None
                    child_row.payment_mode = None
                    
                    # Recalculate amounts
                    payment_amount = flt(doc.paid_amount) if hasattr(doc, 'paid_amount') else flt(doc.base_paid_amount)
                    child_row.paid_amount = flt(child_row.paid_amount) - payment_amount
                    child_row.outstanding = flt(child_row.payment_amount) - flt(child_row.paid_amount)
                    
                    # Ensure paid_amount doesn't go negative
                    if child_row.paid_amount < 0:
                        child_row.paid_amount = 0
                        child_row.outstanding = child_row.payment_amount
                    
                    break
            
            # Save the parent document
            parent_doc.save()
            
            # Update parent totals if it's a Rental Payment Schedule
            if schedule.parenttype == "Rental Payment Schedule":
                update_rental_payment_schedule_totals(parent_doc)
                
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(
            f"Error unlinking Payment Entry {doc.name} from Payment Schedule: {str(e)}",
            "Payment Schedule Unlinking Error"
        )

def find_matching_payment_schedules(payment_entry):
    """
    Find Payment Schedule rows that match the Payment Entry
    Returns list of matching schedule information
    """
    matching_schedules = []
    
    try:
        # Get customer information
        customer = payment_entry.party
        payment_amount = flt(payment_entry.paid_amount) or flt(payment_entry.base_paid_amount)
        payment_date = getdate(payment_entry.posting_date)
        
        # Find tenant associated with this customer
        tenant = find_tenant_by_customer(customer)
        if not tenant:
            return matching_schedules
            
        # Find active rental payment schedules for this tenant
        rental_schedules = frappe.get_all(
            "Rental Payment Schedule",
            filters={
                "tenant": tenant,
                "schedule_status": ["in", ["Active", "Overdue"]],
                "docstatus": 1
            },
            fields=["name", "rental_contract", "tenant", "property", "rental_unit"]
        )
        
        for rental_schedule in rental_schedules:
            # Get the full document to access child table
            schedule_doc = frappe.get_doc("Rental Payment Schedule", rental_schedule.name)
            
            # Check each payment schedule row
            for payment_schedule in schedule_doc.payment_schedules:
                if is_payment_schedule_match(payment_schedule, payment_entry, payment_amount, payment_date):
                    matching_schedules.append({
                        "rental_payment_schedule": rental_schedule.name,
                        "payment_schedule_row": payment_schedule.name,
                        "payment_schedule_doc": payment_schedule,
                        "rental_contract": rental_schedule.rental_contract,
                        "tenant": rental_schedule.tenant,
                        "property": rental_schedule.property,
                        "rental_unit": rental_schedule.rental_unit
                    })
                    
    except Exception as e:
        frappe.log_error(f"Error finding matching payment schedules: {str(e)}")
        
    return matching_schedules

def is_payment_schedule_match(payment_schedule, payment_entry, payment_amount, payment_date):
    """
    Determine if a payment schedule row matches the payment entry
    """
    try:
        # Skip if already fully paid
        if flt(payment_schedule.outstanding) <= 0:
            return False
            
        # Skip if already linked to another payment entry
        if payment_schedule.payment_entry and payment_schedule.payment_entry != payment_entry.name:
            return False
            
        # Check amount match (exact or partial)
        outstanding_amount = flt(payment_schedule.outstanding)
        if payment_amount > outstanding_amount + 0.01:  # Allow small rounding differences
            return False
            
        # Check date proximity (within 30 days of due date)
        due_date = getdate(payment_schedule.due_date)
        date_diff = abs((payment_date - due_date).days)
        if date_diff > 30:
            return False
            
        # Check for reference in payment entry remarks
        if payment_entry.remarks:
            remarks_lower = payment_entry.remarks.lower()
            if any(keyword in remarks_lower for keyword in ['rent', 'rental', 'property']):
                return True
                
        # If amount matches closely and date is reasonable, consider it a match
        amount_match_ratio = payment_amount / outstanding_amount if outstanding_amount > 0 else 0
        if 0.95 <= amount_match_ratio <= 1.05:  # Within 5% tolerance
            return True
            
        return False
        
    except Exception as e:
        frappe.log_error(f"Error checking payment schedule match: {str(e)}")
        return False

def process_payment_schedule_link(payment_entry, schedule_info):
    """
    Process the linking of Payment Entry to a specific Payment Schedule row
    """
    try:
        # Get the rental payment schedule document
        rental_schedule_doc = frappe.get_doc("Rental Payment Schedule", schedule_info["rental_payment_schedule"])
        
        # Find the specific payment schedule row
        payment_schedule_row = None
        for row in rental_schedule_doc.payment_schedules:
            if row.name == schedule_info["payment_schedule_row"]:
                payment_schedule_row = row
                break
                
        if not payment_schedule_row:
            return
            
        # Calculate payment allocation
        payment_amount = flt(payment_entry.paid_amount) or flt(payment_entry.base_paid_amount)
        outstanding_amount = flt(payment_schedule_row.outstanding)
        allocated_amount = min(payment_amount, outstanding_amount)
        
        # Update payment schedule row
        payment_schedule_row.payment_entry = payment_entry.name
        payment_schedule_row.paid_amount = flt(payment_schedule_row.paid_amount) + allocated_amount
        payment_schedule_row.outstanding = flt(payment_schedule_row.payment_amount) - flt(payment_schedule_row.paid_amount)
        payment_schedule_row.payment_date = payment_entry.posting_date
        payment_schedule_row.payment_reference = payment_entry.reference_no or payment_entry.name
        payment_schedule_row.payment_mode = payment_entry.mode_of_payment
        
        # Update rental context information
        payment_schedule_row.rental_contract_ref = schedule_info["rental_contract"]
        payment_schedule_row.tenant_ref = schedule_info["tenant"]
        payment_schedule_row.property_unit_ref = f"{schedule_info['property']} - {schedule_info['rental_unit']}"
        
        # Update payment status
        if flt(payment_schedule_row.outstanding) <= 0.01:  # Fully paid (allow small rounding)
            payment_schedule_row.payment_status = "Paid"
            payment_schedule_row.outstanding = 0
        elif flt(payment_schedule_row.paid_amount) > 0:
            payment_schedule_row.payment_status = "Partially Paid"
        else:
            payment_schedule_row.payment_status = "Pending"
            
        # Save the rental payment schedule
        rental_schedule_doc.save()
        
        # Update parent totals
        update_rental_payment_schedule_totals(rental_schedule_doc)
        
        # Log successful linking
        frappe.logger().info(f"Successfully linked Payment Entry {payment_entry.name} to Payment Schedule {payment_schedule_row.name}")
        
    except Exception as e:
        frappe.log_error(f"Error processing payment schedule link: {str(e)}")

def find_tenant_by_customer(customer):
    """
    Find tenant associated with a customer
    """
    try:
        # First try direct customer name match
        tenant = frappe.db.get_value("Tenant", {"customer": customer}, "name")
        if tenant:
            return tenant
            
        # Try customer name pattern match
        tenant_pattern = f"TENANT-{customer}"
        tenant = frappe.db.get_value("Tenant", {"name": ["like", f"%{tenant_pattern}%"]}, "name")
        if tenant:
            return tenant
            
        # Try email match
        customer_email = frappe.db.get_value("Customer", customer, "email_id")
        if customer_email:
            tenant = frappe.db.get_value("Tenant", {"email": customer_email}, "name")
            if tenant:
                return tenant
                
        # Try phone match
        customer_phone = frappe.db.get_value("Customer", customer, "mobile_no")
        if customer_phone:
            tenant = frappe.db.get_value("Tenant", {"phone": customer_phone}, "name")
            if tenant:
                return tenant
                
        return None
        
    except Exception as e:
        frappe.log_error(f"Error finding tenant by customer {customer}: {str(e)}")
        return None

def update_rental_payment_schedule_totals(rental_schedule_doc):
    """
    Update totals in Rental Payment Schedule based on child payment schedules
    """
    try:
        total_amount = 0
        paid_amount = 0
        
        for schedule in rental_schedule_doc.payment_schedules:
            total_amount += flt(schedule.payment_amount)
            paid_amount += flt(schedule.paid_amount)
            
        rental_schedule_doc.total_rent_amount = total_amount
        rental_schedule_doc.paid_amount = paid_amount
        rental_schedule_doc.outstanding_amount = total_amount - paid_amount
        
        # Update overall status
        if rental_schedule_doc.outstanding_amount <= 0:
            rental_schedule_doc.schedule_status = "Completed"
        elif rental_schedule_doc.paid_amount > 0:
            # Check for overdue payments
            today = getdate(nowdate())
            overdue_payments = [s for s in rental_schedule_doc.payment_schedules 
                              if getdate(s.due_date) < today and flt(s.outstanding) > 0]
            if overdue_payments:
                rental_schedule_doc.schedule_status = "Overdue"
            else:
                rental_schedule_doc.schedule_status = "Active"
                
        rental_schedule_doc.save()
        
    except Exception as e:
        frappe.log_error(f"Error updating rental payment schedule totals: {str(e)}")

def validate_payment_amount(payment_entry, payment_schedule_row, allocated_amount):
    """
    Validate that payment amount doesn't exceed outstanding amount
    """
    outstanding = flt(payment_schedule_row.outstanding)
    if allocated_amount > outstanding + 0.01:  # Allow small rounding differences
        frappe.throw(
            f"Payment amount {allocated_amount} exceeds outstanding amount {outstanding} "
            f"for payment schedule due on {payment_schedule_row.due_date}"
        )

@frappe.whitelist()
def get_payment_schedule_status(rental_payment_schedule):
    """
    Get payment status summary for a rental payment schedule
    """
    try:
        doc = frappe.get_doc("Rental Payment Schedule", rental_payment_schedule)
        
        status_summary = {
            "total_schedules": len(doc.payment_schedules),
            "paid_schedules": 0,
            "partially_paid_schedules": 0,
            "pending_schedules": 0,
            "overdue_schedules": 0,
            "total_amount": doc.total_rent_amount,
            "paid_amount": doc.paid_amount,
            "outstanding_amount": doc.outstanding_amount,
            "schedule_details": []
        }
        
        today = getdate(nowdate())
        
        for schedule in doc.payment_schedules:
            if schedule.payment_status == "Paid":
                status_summary["paid_schedules"] += 1
            elif schedule.payment_status == "Partially Paid":
                status_summary["partially_paid_schedules"] += 1
            elif getdate(schedule.due_date) < today and flt(schedule.outstanding) > 0:
                status_summary["overdue_schedules"] += 1
            else:
                status_summary["pending_schedules"] += 1
                
            status_summary["schedule_details"].append({
                "due_date": schedule.due_date,
                "payment_amount": schedule.payment_amount,
                "paid_amount": schedule.paid_amount,
                "outstanding": schedule.outstanding,
                "payment_status": schedule.payment_status,
                "payment_entry": schedule.payment_entry,
                "payment_date": schedule.payment_date
            })
            
        return status_summary
        
    except Exception as e:
        frappe.log_error(f"Error getting payment schedule status: {str(e)}")
        return None

@frappe.whitelist()
def manual_link_payment_entry(payment_entry, rental_payment_schedule, payment_schedule_row):
    """
    Manually link a Payment Entry to a specific Payment Schedule row
    """
    try:
        # Validate inputs
        if not frappe.db.exists("Payment Entry", payment_entry):
            frappe.throw(f"Payment Entry {payment_entry} does not exist")
            
        if not frappe.db.exists("Rental Payment Schedule", rental_payment_schedule):
            frappe.throw(f"Rental Payment Schedule {rental_payment_schedule} does not exist")
            
        # Get documents
        payment_doc = frappe.get_doc("Payment Entry", payment_entry)
        schedule_doc = frappe.get_doc("Rental Payment Schedule", rental_payment_schedule)
        
        # Find the payment schedule row
        target_row = None
        for row in schedule_doc.payment_schedules:
            if row.name == payment_schedule_row:
                target_row = row
                break
                
        if not target_row:
            frappe.throw(f"Payment Schedule row {payment_schedule_row} not found")
            
        # Create schedule info for processing
        schedule_info = {
            "rental_payment_schedule": rental_payment_schedule,
            "payment_schedule_row": payment_schedule_row,
            "payment_schedule_doc": target_row,
            "rental_contract": schedule_doc.rental_contract,
            "tenant": schedule_doc.tenant,
            "property": schedule_doc.property,
            "rental_unit": schedule_doc.rental_unit
        }
        
        # Process the link
        process_payment_schedule_link(payment_doc, schedule_info)
        
        frappe.db.commit()
        frappe.msgprint(f"Successfully linked Payment Entry {payment_entry} to Payment Schedule")
        
        return True
        
    except Exception as e:
        frappe.log_error(f"Error manually linking payment entry: {str(e)}")
        frappe.throw(f"Failed to link payment entry: {str(e)}")
        return False
