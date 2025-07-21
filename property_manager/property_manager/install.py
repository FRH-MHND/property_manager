# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from property_manager.custom_fields import setup_payment_schedule_customizations

def after_install():
    """
    Execute after Property Manager app installation
    """
    try:
        # Create custom fields for Payment Schedule
        setup_payment_schedule_customizations()
        
        # Create default roles and permissions
        create_property_manager_roles()
        
        # Set up default configurations
        setup_default_configurations()
        
        frappe.db.commit()
        print("Property Manager app installed successfully with Payment Entry integration")
        
    except Exception as e:
        frappe.log_error(f"Error during Property Manager installation: {str(e)}")
        print(f"Installation completed with errors: {str(e)}")

def create_property_manager_roles():
    """
    Create default roles for Property Manager
    """
    roles = [
        {
            "role_name": "Property Manager",
            "description": "Full access to property management features"
        },
        {
            "role_name": "Tenant",
            "description": "Limited access for tenants to view their information"
        },
        {
            "role_name": "Property Owner",
            "description": "Access to property information and reports"
        }
    ]
    
    for role_data in roles:
        if not frappe.db.exists("Role", role_data["role_name"]):
            role = frappe.get_doc({
                "doctype": "Role",
                "role_name": role_data["role_name"],
                "description": role_data["description"]
            })
            role.insert()

def setup_default_configurations():
    """
    Set up default configurations for Property Manager
    """
    # Create default payment terms if they don't exist
    payment_terms = [
        {"payment_term_name": "Monthly Rent", "description": "Monthly rental payment"},
        {"payment_term_name": "Security Deposit", "description": "Security deposit payment"},
        {"payment_term_name": "Late Fee", "description": "Late payment fee"}
    ]
    
    for term_data in payment_terms:
        if not frappe.db.exists("Payment Term", term_data["payment_term_name"]):
            term = frappe.get_doc({
                "doctype": "Payment Term",
                "payment_term_name": term_data["payment_term_name"],
                "description": term_data["description"]
            })
            term.insert()

def before_uninstall():
    """
    Execute before Property Manager app uninstallation
    """
    try:
        # Remove custom fields
        from property_manager.custom_fields import remove_payment_schedule_custom_fields
        remove_payment_schedule_custom_fields()
        
        frappe.db.commit()
        print("Property Manager app uninstalled successfully")
        
    except Exception as e:
        frappe.log_error(f"Error during Property Manager uninstallation: {str(e)}")
        print(f"Uninstallation completed with errors: {str(e)}")
