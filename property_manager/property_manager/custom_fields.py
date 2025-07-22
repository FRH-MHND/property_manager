# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def create_payment_schedule_custom_fields():
    """Create custom fields for Payment Schedule to support Payment Entry linking"""
    
    custom_fields = {
        "Payment Schedule": [
            {
                "fieldname": "payment_entry",
                "fieldtype": "Link",
                "options": "Payment Entry",
                "label": "Payment Entry",
                "read_only": 1,
                "insert_after": "paid_amount",
                "description": "Linked Payment Entry for this scheduled payment",
                "in_list_view": 0,
                "print_hide": 1,
                "report_hide": 0
            },
            {
                "fieldname": "payment_status",
                "fieldtype": "Select",
                "options": "Pending\nPaid\nPartially Paid\nOverdue\nCancelled",
                "label": "Payment Status",
                "default": "Pending",
                "read_only": 1,
                "insert_after": "payment_entry",
                "in_list_view": 1,
                "print_hide": 0,
                "report_hide": 0,
                "description": "Current status of this scheduled payment"
            },
            {
                "fieldname": "payment_date",
                "fieldtype": "Date",
                "label": "Payment Date",
                "read_only": 1,
                "insert_after": "payment_status",
                "description": "Date when payment was actually made",
                "in_list_view": 0,
                "print_hide": 0,
                "report_hide": 0
            },
            {
                "fieldname": "section_break_payment_details",
                "fieldtype": "Section Break",
                "label": "Payment Details",
                "insert_after": "payment_date",
                "collapsible": 1
            },
            {
                "fieldname": "payment_reference",
                "fieldtype": "Data",
                "label": "Payment Reference",
                "read_only": 1,
                "insert_after": "section_break_payment_details",
                "description": "Reference number from Payment Entry",
                "in_list_view": 0,
                "print_hide": 0
            },
            {
                "fieldname": "payment_mode",
                "fieldtype": "Link",
                "options": "Mode of Payment",
                "label": "Payment Mode",
                "read_only": 1,
                "insert_after": "payment_reference",
                "description": "Mode of payment used",
                "in_list_view": 0,
                "print_hide": 0
            },
            {
                "fieldname": "column_break_payment_info",
                "fieldtype": "Column Break",
                "insert_after": "payment_mode"
            },
            {
                "fieldname": "rental_contract_ref",
                "fieldtype": "Data",
                "label": "Rental Contract",
                "read_only": 1,
                "insert_after": "column_break_payment_info",
                "description": "Associated rental contract reference",
                "in_list_view": 0,
                "print_hide": 0
            },
            {
                "fieldname": "tenant_ref",
                "fieldtype": "Data",
                "label": "Tenant",
                "read_only": 1,
                "insert_after": "rental_contract_ref",
                "description": "Associated tenant reference",
                "in_list_view": 0,
                "print_hide": 0
            },
            {
                "fieldname": "property_unit_ref",
                "fieldtype": "Data",
                "label": "Property Unit",
                "read_only": 1,
                "insert_after": "tenant_ref",
                "description": "Associated property unit reference",
                "in_list_view": 0,
                "print_hide": 0
            }
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
    
def remove_payment_schedule_custom_fields():
    """Remove custom fields from Payment Schedule (for rollback)"""
    
    custom_field_names = [
        "Payment Schedule-payment_entry",
        "Payment Schedule-payment_status", 
        "Payment Schedule-payment_date",
        "Payment Schedule-section_break_payment_details",
        "Payment Schedule-payment_reference",
        "Payment Schedule-payment_mode",
        "Payment Schedule-column_break_payment_info",
        "Payment Schedule-rental_contract_ref",
        "Payment Schedule-tenant_ref",
        "Payment Schedule-property_unit_ref"
    ]
    
    for field_name in custom_field_names:
        if frappe.db.exists("Custom Field", field_name):
            frappe.delete_doc("Custom Field", field_name)
    
    frappe.db.commit()

def setup_payment_schedule_customizations():
    """Main function to set up all Payment Schedule customizations"""
    try:
        create_payment_schedule_custom_fields()
        frappe.msgprint("Payment Schedule custom fields created successfully")
        return True
    except Exception as e:
        frappe.log_error(f"Error creating Payment Schedule custom fields: {str(e)}")
        frappe.throw(f"Failed to create custom fields: {str(e)}")
        return False

# Execute on module load if called directly
if __name__ == "__main__":
    create_payment_schedule_custom_fields()
