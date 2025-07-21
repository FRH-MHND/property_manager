# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, getdate, nowdate, add_days
from datetime import datetime, timedelta

class PaymentValidationError(Exception):
    """Custom exception for payment validation errors"""
    pass

def validate_payment_entry_for_rental(payment_entry):
    """
    Comprehensive validation for Payment Entry related to rental payments
    """
    validation_results = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "rental_context": None
    }
    
    try:
        # Check if payment is for a customer (tenant)
        if payment_entry.party_type != "Customer":
            validation_results["warnings"].append("Payment is not for a customer - rental linking may not apply")
            return validation_results
            
        # Find rental context
        rental_context = find_rental_context_for_payment(payment_entry)
        if not rental_context:
            validation_results["warnings"].append("No rental context found for this payment")
            return validation_results
            
        validation_results["rental_context"] = rental_context
        
        # Validate payment amount
        amount_validation = validate_payment_amount(payment_entry, rental_context)
        if not amount_validation["is_valid"]:
            validation_results["errors"].extend(amount_validation["errors"])
            validation_results["is_valid"] = False
            
        # Validate payment date
        date_validation = validate_payment_date(payment_entry, rental_context)
        if not date_validation["is_valid"]:
            validation_results["warnings"].extend(date_validation["warnings"])
            
        # Validate for duplicate payments
        duplicate_validation = validate_duplicate_payments(payment_entry, rental_context)
        if not duplicate_validation["is_valid"]:
            validation_results["errors"].extend(duplicate_validation["errors"])
            validation_results["is_valid"] = False
            
        # Validate payment schedule availability
        schedule_validation = validate_payment_schedule_availability(payment_entry, rental_context)
        if not schedule_validation["is_valid"]:
            validation_results["errors"].extend(schedule_validation["errors"])
            validation_results["is_valid"] = False
            
    except Exception as e:
        validation_results["is_valid"] = False
        validation_results["errors"].append(f"Validation error: {str(e)}")
        frappe.log_error(f"Payment validation error: {str(e)}")
        
    return validation_results

def find_rental_context_for_payment(payment_entry):
    """
    Find rental context (tenant, contracts, schedules) for a payment entry
    """
    try:
        customer = payment_entry.party
        
        # Find tenant by customer
        tenant = find_tenant_by_customer(customer)
        if not tenant:
            return None
            
        # Find active rental contracts for tenant
        contracts = frappe.get_all(
            "Rental Contract",
            filters={
                "tenant": tenant,
                "contract_status": ["in", ["Active", "Draft"]],
                "docstatus": ["in", [0, 1]]
            },
            fields=["name", "rental_unit", "property", "monthly_rent", "start_date", "end_date"]
        )
        
        if not contracts:
            return None
            
        # Find payment schedules for these contracts
        payment_schedules = []
        for contract in contracts:
            schedules = frappe.get_all(
                "Rental Payment Schedule",
                filters={
                    "rental_contract": contract.name,
                    "schedule_status": ["in", ["Active", "Overdue"]],
                    "docstatus": 1
                },
                fields=["name", "rental_contract", "outstanding_amount", "total_rent_amount"]
            )
            payment_schedules.extend(schedules)
            
        return {
            "tenant": tenant,
            "contracts": contracts,
            "payment_schedules": payment_schedules,
            "customer": customer
        }
        
    except Exception as e:
        frappe.log_error(f"Error finding rental context: {str(e)}")
        return None

def find_tenant_by_customer(customer):
    """
    Find tenant associated with a customer with multiple matching strategies
    """
    try:
        # Strategy 1: Direct customer field match
        tenant = frappe.db.get_value("Tenant", {"customer": customer}, "name")
        if tenant:
            return tenant
            
        # Strategy 2: Customer name pattern match (TENANT-XXX format)
        if customer.startswith("TENANT-"):
            tenant_id = customer.replace("TENANT-", "")
            tenant = frappe.db.get_value("Tenant", tenant_id, "name")
            if tenant:
                return tenant
                
        # Strategy 3: Email match
        customer_doc = frappe.get_doc("Customer", customer)
        if customer_doc.email_id:
            tenant = frappe.db.get_value("Tenant", {"email": customer_doc.email_id}, "name")
            if tenant:
                return tenant
                
        # Strategy 4: Phone match
        if customer_doc.mobile_no:
            tenant = frappe.db.get_value("Tenant", {"phone": customer_doc.mobile_no}, "name")
            if tenant:
                return tenant
                
        # Strategy 5: Name similarity match
        customer_name = customer_doc.customer_name
        tenants = frappe.get_all("Tenant", fields=["name", "tenant_name", "first_name", "last_name"])
        
        for tenant_doc in tenants:
            # Check full name match
            tenant_full_name = ""
            if tenant_doc.get("first_name") and tenant_doc.get("last_name"):
                tenant_full_name = f"{tenant_doc.first_name} {tenant_doc.last_name}"
            elif tenant_doc.get("tenant_name"):
                tenant_full_name = tenant_doc.tenant_name
                
            if tenant_full_name and customer_name.lower() in tenant_full_name.lower():
                return tenant_doc.name
                
        return None
        
    except Exception as e:
        frappe.log_error(f"Error finding tenant by customer: {str(e)}")
        return None

def validate_payment_amount(payment_entry, rental_context):
    """
    Validate payment amount against rental schedules
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    try:
        payment_amount = flt(payment_entry.paid_amount) or flt(payment_entry.base_paid_amount)
        
        if payment_amount <= 0:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Payment amount must be greater than zero")
            return validation_result
            
        # Check against total outstanding amount across all schedules
        total_outstanding = sum(flt(schedule["outstanding_amount"]) for schedule in rental_context["payment_schedules"])
        
        if payment_amount > total_outstanding + 1:  # Allow small rounding differences
            validation_result["warnings"].append(
                f"Payment amount {payment_amount} exceeds total outstanding amount {total_outstanding}. "
                "This may result in overpayment or credit."
            )
            
        # Check if payment amount matches any specific schedule amount
        matching_schedule_found = False
        for schedule in rental_context["payment_schedules"]:
            schedule_doc = frappe.get_doc("Rental Payment Schedule", schedule["name"])
            for payment_schedule in schedule_doc.payment_schedules:
                outstanding = flt(payment_schedule.outstanding)
                if abs(payment_amount - outstanding) <= 0.01:  # Exact match
                    matching_schedule_found = True
                    break
            if matching_schedule_found:
                break
                
        if not matching_schedule_found and len(rental_context["payment_schedules"]) > 1:
            validation_result["warnings"].append(
                "Payment amount does not exactly match any single scheduled payment. "
                "Payment will be allocated to the best matching schedule."
            )
            
    except Exception as e:
        validation_result["is_valid"] = False
        validation_result["errors"].append(f"Amount validation error: {str(e)}")
        
    return validation_result

def validate_payment_date(payment_entry, rental_context):
    """
    Validate payment date against due dates and contract periods
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    try:
        payment_date = getdate(payment_entry.posting_date)
        today = getdate(nowdate())
        
        # Check if payment date is in the future
        if payment_date > today:
            validation_result["warnings"].append(
                f"Payment date {payment_date} is in the future. "
                "Ensure this is intentional for advance payments."
            )
            
        # Check against contract periods
        for contract in rental_context["contracts"]:
            contract_start = getdate(contract["start_date"])
            contract_end = getdate(contract["end_date"])
            
            if payment_date < contract_start:
                validation_result["warnings"].append(
                    f"Payment date {payment_date} is before contract start date {contract_start} "
                    f"for contract {contract['name']}"
                )
            elif payment_date > contract_end:
                validation_result["warnings"].append(
                    f"Payment date {payment_date} is after contract end date {contract_end} "
                    f"for contract {contract['name']}"
                )
                
        # Check against payment schedule due dates
        closest_due_date = None
        min_date_diff = float('inf')
        
        for schedule in rental_context["payment_schedules"]:
            schedule_doc = frappe.get_doc("Rental Payment Schedule", schedule["name"])
            for payment_schedule in schedule_doc.payment_schedules:
                if flt(payment_schedule.outstanding) > 0:
                    due_date = getdate(payment_schedule.due_date)
                    date_diff = abs((payment_date - due_date).days)
                    if date_diff < min_date_diff:
                        min_date_diff = date_diff
                        closest_due_date = due_date
                        
        if closest_due_date and min_date_diff > 60:  # More than 60 days difference
            validation_result["warnings"].append(
                f"Payment date {payment_date} is {min_date_diff} days away from "
                f"the closest due date {closest_due_date}. Verify payment allocation."
            )
            
    except Exception as e:
        validation_result["errors"].append(f"Date validation error: {str(e)}")
        
    return validation_result

def validate_duplicate_payments(payment_entry, rental_context):
    """
    Check for potential duplicate payments
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    try:
        payment_amount = flt(payment_entry.paid_amount) or flt(payment_entry.base_paid_amount)
        payment_date = getdate(payment_entry.posting_date)
        customer = payment_entry.party
        
        # Check for similar payments in the last 30 days
        similar_payments = frappe.db.sql("""
            SELECT name, paid_amount, posting_date, reference_no
            FROM `tabPayment Entry`
            WHERE party = %s
            AND party_type = 'Customer'
            AND docstatus = 1
            AND name != %s
            AND posting_date >= %s
            AND ABS(paid_amount - %s) <= 1
        """, (customer, payment_entry.name or "", add_days(payment_date, -30), payment_amount), as_dict=True)
        
        if similar_payments:
            validation_result["warnings"].append(
                f"Found {len(similar_payments)} similar payment(s) in the last 30 days. "
                "Please verify this is not a duplicate payment."
            )
            
        # Check for payments with same reference number
        if payment_entry.reference_no:
            duplicate_ref_payments = frappe.db.sql("""
                SELECT name, paid_amount, posting_date
                FROM `tabPayment Entry`
                WHERE party = %s
                AND party_type = 'Customer'
                AND docstatus = 1
                AND name != %s
                AND reference_no = %s
            """, (customer, payment_entry.name or "", payment_entry.reference_no), as_dict=True)
            
            if duplicate_ref_payments:
                validation_result["is_valid"] = False
                validation_result["errors"].append(
                    f"Payment with reference number '{payment_entry.reference_no}' already exists. "
                    "Duplicate reference numbers are not allowed."
                )
                
    except Exception as e:
        validation_result["errors"].append(f"Duplicate validation error: {str(e)}")
        
    return validation_result

def validate_payment_schedule_availability(payment_entry, rental_context):
    """
    Validate that there are available payment schedules to link to
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    try:
        available_schedules = 0
        total_outstanding = 0
        
        for schedule in rental_context["payment_schedules"]:
            schedule_doc = frappe.get_doc("Rental Payment Schedule", schedule["name"])
            for payment_schedule in schedule_doc.payment_schedules:
                outstanding = flt(payment_schedule.outstanding)
                if outstanding > 0:
                    available_schedules += 1
                    total_outstanding += outstanding
                    
        if available_schedules == 0:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                "No outstanding payment schedules found for this tenant. "
                "All scheduled payments may already be paid."
            )
        elif total_outstanding <= 0:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                "Total outstanding amount is zero. No payments are due."
            )
            
    except Exception as e:
        validation_result["errors"].append(f"Schedule availability validation error: {str(e)}")
        
    return validation_result

def validate_payment_cancellation(payment_entry):
    """
    Validate that a payment entry can be safely cancelled
    """
    validation_result = {
        "can_cancel": True,
        "errors": [],
        "warnings": [],
        "linked_schedules": []
    }
    
    try:
        # Find linked payment schedules
        linked_schedules = frappe.db.sql("""
            SELECT 
                ps.name as schedule_name,
                ps.parent as payment_schedule_parent,
                ps.parenttype,
                ps.payment_amount,
                ps.paid_amount,
                ps.outstanding,
                ps.payment_status
            FROM `tabPayment Schedule` ps
            WHERE ps.payment_entry = %s
        """, (payment_entry.name,), as_dict=True)
        
        validation_result["linked_schedules"] = linked_schedules
        
        if not linked_schedules:
            validation_result["warnings"].append(
                "No linked payment schedules found. Cancellation will not affect rental payments."
            )
            return validation_result
            
        # Check if cancellation would create negative balances
        for schedule in linked_schedules:
            if flt(schedule.paid_amount) < flt(payment_entry.paid_amount):
                validation_result["warnings"].append(
                    f"Cancelling this payment may result in negative paid amount "
                    f"for payment schedule {schedule.schedule_name}"
                )
                
        # Check if there are subsequent payments that depend on this one
        for schedule in linked_schedules:
            subsequent_payments = frappe.db.sql("""
                SELECT COUNT(*) as count
                FROM `tabPayment Schedule` ps
                INNER JOIN `tabPayment Entry` pe ON ps.payment_entry = pe.name
                WHERE ps.parent = %s
                AND ps.parenttype = %s
                AND pe.posting_date > %s
                AND pe.docstatus = 1
                AND pe.name != %s
            """, (schedule.payment_schedule_parent, schedule.parenttype, 
                  payment_entry.posting_date, payment_entry.name), as_dict=True)
            
            if subsequent_payments and subsequent_payments[0].count > 0:
                validation_result["warnings"].append(
                    f"There are subsequent payments after this one for payment schedule "
                    f"{schedule.payment_schedule_parent}. Consider the impact on payment sequence."
                )
                
    except Exception as e:
        validation_result["can_cancel"] = False
        validation_result["errors"].append(f"Cancellation validation error: {str(e)}")
        
    return validation_result

@frappe.whitelist()
def validate_payment_entry_rental_context(payment_entry_name):
    """
    API endpoint to validate payment entry rental context
    """
    try:
        payment_entry = frappe.get_doc("Payment Entry", payment_entry_name)
        validation_result = validate_payment_entry_for_rental(payment_entry)
        return validation_result
    except Exception as e:
        frappe.log_error(f"Error validating payment entry: {str(e)}")
        return {
            "is_valid": False,
            "errors": [f"Validation error: {str(e)}"],
            "warnings": [],
            "rental_context": None
        }

@frappe.whitelist()
def check_payment_cancellation_impact(payment_entry_name):
    """
    API endpoint to check impact of payment entry cancellation
    """
    try:
        payment_entry = frappe.get_doc("Payment Entry", payment_entry_name)
        validation_result = validate_payment_cancellation(payment_entry)
        return validation_result
    except Exception as e:
        frappe.log_error(f"Error checking cancellation impact: {str(e)}")
        return {
            "can_cancel": False,
            "errors": [f"Validation error: {str(e)}"],
            "warnings": [],
            "linked_schedules": []
        }

