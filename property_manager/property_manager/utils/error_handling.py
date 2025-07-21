# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now_datetime, flt
import traceback
import json

class PaymentProcessingError(Exception):
    """Custom exception for payment processing errors"""
    def __init__(self, message, error_code=None, details=None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class PaymentLinkingError(PaymentProcessingError):
    """Specific error for payment linking issues"""
    pass

class PaymentValidationError(PaymentProcessingError):
    """Specific error for payment validation issues"""
    pass

def handle_payment_processing_error(error, payment_entry_name, operation="processing"):
    """
    Centralized error handling for payment processing operations
    """
    error_info = {
        "timestamp": now_datetime(),
        "payment_entry": payment_entry_name,
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc()
    }
    
    # Log detailed error information
    frappe.log_error(
        title=f"Payment {operation.title()} Error - {payment_entry_name}",
        message=json.dumps(error_info, indent=2, default=str)
    )
    
    # Create error log entry
    create_payment_error_log(error_info)
    
    # Determine if error should be raised or just logged
    if isinstance(error, (PaymentLinkingError, PaymentValidationError)):
        # These are business logic errors that should be raised
        raise error
    else:
        # System errors should be logged but not block payment processing
        frappe.logger().error(f"Payment processing error: {str(error)}")

def create_payment_error_log(error_info):
    """
    Create a log entry for payment processing errors
    """
    try:
        # Create a custom error log document if needed
        if not frappe.db.exists("DocType", "Payment Processing Error Log"):
            create_error_log_doctype()
            
        error_log = frappe.get_doc({
            "doctype": "Payment Processing Error Log",
            "payment_entry": error_info["payment_entry"],
            "operation": error_info["operation"],
            "error_type": error_info["error_type"],
            "error_message": error_info["error_message"],
            "error_details": json.dumps(error_info, indent=2, default=str),
            "timestamp": error_info["timestamp"],
            "status": "Open"
        })
        error_log.insert(ignore_permissions=True)
        
    except Exception as e:
        # If we can't create error log, just log to system
        frappe.logger().error(f"Failed to create payment error log: {str(e)}")

def create_error_log_doctype():
    """
    Create Payment Processing Error Log doctype if it doesn't exist
    """
    try:
        if frappe.db.exists("DocType", "Payment Processing Error Log"):
            return
            
        doctype = frappe.get_doc({
            "doctype": "DocType",
            "name": "Payment Processing Error Log",
            "module": "Property Manager",
            "custom": 1,
            "fields": [
                {
                    "fieldname": "payment_entry",
                    "fieldtype": "Link",
                    "options": "Payment Entry",
                    "label": "Payment Entry",
                    "reqd": 1
                },
                {
                    "fieldname": "operation",
                    "fieldtype": "Data",
                    "label": "Operation",
                    "reqd": 1
                },
                {
                    "fieldname": "error_type",
                    "fieldtype": "Data",
                    "label": "Error Type",
                    "reqd": 1
                },
                {
                    "fieldname": "error_message",
                    "fieldtype": "Text",
                    "label": "Error Message",
                    "reqd": 1
                },
                {
                    "fieldname": "error_details",
                    "fieldtype": "Long Text",
                    "label": "Error Details"
                },
                {
                    "fieldname": "timestamp",
                    "fieldtype": "Datetime",
                    "label": "Timestamp",
                    "reqd": 1
                },
                {
                    "fieldname": "status",
                    "fieldtype": "Select",
                    "options": "Open\nResolved\nIgnored",
                    "label": "Status",
                    "default": "Open"
                },
                {
                    "fieldname": "resolution_notes",
                    "fieldtype": "Text",
                    "label": "Resolution Notes"
                }
            ],
            "permissions": [
                {
                    "role": "System Manager",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1
                },
                {
                    "role": "Property Manager",
                    "read": 1,
                    "write": 1
                }
            ]
        })
        doctype.insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.logger().error(f"Failed to create Payment Processing Error Log doctype: {str(e)}")

def safe_payment_operation(operation_func, payment_entry, operation_name, *args, **kwargs):
    """
    Wrapper for safe execution of payment operations with error handling
    """
    try:
        return operation_func(payment_entry, *args, **kwargs)
    except PaymentProcessingError:
        # Re-raise business logic errors
        raise
    except Exception as e:
        # Handle system errors
        handle_payment_processing_error(e, payment_entry.name, operation_name)
        return None

def validate_payment_operation_preconditions(payment_entry, operation):
    """
    Validate preconditions before performing payment operations
    """
    if not payment_entry:
        raise PaymentValidationError("Payment Entry is required")
        
    if not payment_entry.name:
        raise PaymentValidationError("Payment Entry must be saved before processing")
        
    if operation == "link" and payment_entry.docstatus != 1:
        raise PaymentValidationError("Payment Entry must be submitted before linking")
        
    if operation == "unlink" and payment_entry.docstatus != 2:
        raise PaymentValidationError("Payment Entry must be cancelled before unlinking")

def recover_from_payment_error(payment_entry_name, error_type):
    """
    Attempt to recover from specific payment processing errors
    """
    recovery_result = {
        "success": False,
        "message": "",
        "actions_taken": []
    }
    
    try:
        payment_entry = frappe.get_doc("Payment Entry", payment_entry_name)
        
        if error_type == "linking_error":
            # Attempt to re-link payment
            recovery_result = recover_from_linking_error(payment_entry)
        elif error_type == "validation_error":
            # Attempt to fix validation issues
            recovery_result = recover_from_validation_error(payment_entry)
        elif error_type == "data_inconsistency":
            # Attempt to fix data inconsistencies
            recovery_result = recover_from_data_inconsistency(payment_entry)
        else:
            recovery_result["message"] = f"No recovery procedure available for error type: {error_type}"
            
    except Exception as e:
        recovery_result["message"] = f"Recovery attempt failed: {str(e)}"
        frappe.log_error(f"Payment error recovery failed: {str(e)}")
        
    return recovery_result

def recover_from_linking_error(payment_entry):
    """
    Recover from payment linking errors
    """
    recovery_result = {
        "success": False,
        "message": "",
        "actions_taken": []
    }
    
    try:
        # Clear any partial links
        frappe.db.sql("""
            UPDATE `tabPayment Schedule`
            SET payment_entry = NULL, payment_status = 'Pending', payment_date = NULL
            WHERE payment_entry = %s
        """, (payment_entry.name,))
        
        recovery_result["actions_taken"].append("Cleared partial payment links")
        
        # Attempt re-linking
        from property_manager.utils.payment_entry import link_to_payment_schedule
        link_to_payment_schedule(payment_entry, "on_submit")
        
        recovery_result["success"] = True
        recovery_result["message"] = "Successfully recovered from linking error"
        recovery_result["actions_taken"].append("Re-linked payment to schedule")
        
    except Exception as e:
        recovery_result["message"] = f"Linking recovery failed: {str(e)}"
        
    return recovery_result

def recover_from_validation_error(payment_entry):
    """
    Recover from payment validation errors
    """
    recovery_result = {
        "success": False,
        "message": "Validation errors require manual intervention",
        "actions_taken": []
    }
    
    # Validation errors typically require manual review
    # Log the issue for manual resolution
    recovery_result["actions_taken"].append("Logged validation error for manual review")
    
    return recovery_result

def recover_from_data_inconsistency(payment_entry):
    """
    Recover from data inconsistency errors
    """
    recovery_result = {
        "success": False,
        "message": "",
        "actions_taken": []
    }
    
    try:
        # Recalculate payment schedule totals
        linked_schedules = frappe.db.sql("""
            SELECT DISTINCT parent, parenttype
            FROM `tabPayment Schedule`
            WHERE payment_entry = %s
        """, (payment_entry.name,), as_dict=True)
        
        for schedule in linked_schedules:
            if schedule.parenttype == "Rental Payment Schedule":
                schedule_doc = frappe.get_doc("Rental Payment Schedule", schedule.parent)
                from property_manager.utils.payment_entry import update_rental_payment_schedule_totals
                update_rental_payment_schedule_totals(schedule_doc)
                recovery_result["actions_taken"].append(f"Recalculated totals for {schedule.parent}")
                
        recovery_result["success"] = True
        recovery_result["message"] = "Successfully recovered from data inconsistency"
        
    except Exception as e:
        recovery_result["message"] = f"Data inconsistency recovery failed: {str(e)}"
        
    return recovery_result

@frappe.whitelist()
def get_payment_error_logs(payment_entry=None, status=None, limit=50):
    """
    Get payment processing error logs
    """
    try:
        filters = {}
        if payment_entry:
            filters["payment_entry"] = payment_entry
        if status:
            filters["status"] = status
            
        error_logs = frappe.get_all(
            "Payment Processing Error Log",
            filters=filters,
            fields=["name", "payment_entry", "operation", "error_type", "error_message", "timestamp", "status"],
            order_by="timestamp desc",
            limit=limit
        )
        
        return error_logs
        
    except Exception as e:
        frappe.log_error(f"Error retrieving payment error logs: {str(e)}")
        return []

@frappe.whitelist()
def resolve_payment_error(error_log_name, resolution_notes=None):
    """
    Mark a payment error as resolved
    """
    try:
        error_log = frappe.get_doc("Payment Processing Error Log", error_log_name)
        error_log.status = "Resolved"
        if resolution_notes:
            error_log.resolution_notes = resolution_notes
        error_log.save()
        
        return {"success": True, "message": "Error marked as resolved"}
        
    except Exception as e:
        frappe.log_error(f"Error resolving payment error log: {str(e)}")
        return {"success": False, "message": f"Failed to resolve error: {str(e)}"}

@frappe.whitelist()
def retry_payment_operation(payment_entry_name, operation):
    """
    Retry a failed payment operation
    """
    try:
        payment_entry = frappe.get_doc("Payment Entry", payment_entry_name)
        
        if operation == "link":
            from property_manager.utils.payment_entry import link_to_payment_schedule
            link_to_payment_schedule(payment_entry, "on_submit")
        elif operation == "unlink":
            from property_manager.utils.payment_entry import unlink_from_payment_schedule
            unlink_from_payment_schedule(payment_entry, "on_cancel")
        else:
            return {"success": False, "message": f"Unknown operation: {operation}"}
            
        return {"success": True, "message": f"Successfully retried {operation} operation"}
        
    except Exception as e:
        frappe.log_error(f"Error retrying payment operation: {str(e)}")
        return {"success": False, "message": f"Retry failed: {str(e)}"}

