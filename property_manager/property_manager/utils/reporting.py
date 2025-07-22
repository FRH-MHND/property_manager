# Copyright (c) 2025, Farah and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, getdate, nowdate, add_days, add_months
from datetime import datetime, timedelta
import json

@frappe.whitelist()
def get_payment_schedule_dashboard(rental_payment_schedule=None, tenant=None, property_unit=None):
    """
    Get comprehensive payment schedule dashboard data
    """
    try:
        filters = {}
        if rental_payment_schedule:
            filters["name"] = rental_payment_schedule
        if tenant:
            filters["tenant"] = tenant
        if property_unit:
            filters["rental_unit"] = property_unit
            
        # Get rental payment schedules
        schedules = frappe.get_all(
            "Rental Payment Schedule",
            filters=filters,
            fields=["name", "tenant", "property", "rental_unit", "total_rent_amount", 
                   "paid_amount", "outstanding_amount", "schedule_status", "rental_contract"]
        )
        
        dashboard_data = {
            "summary": {
                "total_schedules": len(schedules),
                "total_amount": 0,
                "paid_amount": 0,
                "outstanding_amount": 0,
                "active_schedules": 0,
                "completed_schedules": 0,
                "overdue_schedules": 0
            },
            "schedules": [],
            "payment_trends": [],
            "overdue_analysis": []
        }
        
        for schedule in schedules:
            # Get detailed schedule information
            schedule_doc = frappe.get_doc("Rental Payment Schedule", schedule.name)
            schedule_details = analyze_payment_schedule(schedule_doc)
            
            dashboard_data["schedules"].append(schedule_details)
            
            # Update summary
            dashboard_data["summary"]["total_amount"] += flt(schedule.total_rent_amount)
            dashboard_data["summary"]["paid_amount"] += flt(schedule.paid_amount)
            dashboard_data["summary"]["outstanding_amount"] += flt(schedule.outstanding_amount)
            
            if schedule.schedule_status == "Active":
                dashboard_data["summary"]["active_schedules"] += 1
            elif schedule.schedule_status == "Completed":
                dashboard_data["summary"]["completed_schedules"] += 1
            elif schedule.schedule_status == "Overdue":
                dashboard_data["summary"]["overdue_schedules"] += 1
                
        # Generate payment trends
        dashboard_data["payment_trends"] = generate_payment_trends(schedules)
        
        # Generate overdue analysis
        dashboard_data["overdue_analysis"] = generate_overdue_analysis(schedules)
        
        return dashboard_data
        
    except Exception as e:
        frappe.log_error(f"Error generating payment schedule dashboard: {str(e)}")
        return None

def analyze_payment_schedule(schedule_doc):
    """
    Analyze individual payment schedule for detailed insights
    """
    analysis = {
        "schedule_info": {
            "name": schedule_doc.name,
            "tenant": schedule_doc.tenant,
            "property": schedule_doc.property,
            "rental_unit": schedule_doc.rental_unit,
            "rental_contract": schedule_doc.rental_contract,
            "status": schedule_doc.schedule_status
        },
        "financial_summary": {
            "total_amount": schedule_doc.total_rent_amount,
            "paid_amount": schedule_doc.paid_amount,
            "outstanding_amount": schedule_doc.outstanding_amount,
            "payment_completion_rate": 0
        },
        "payment_details": [],
        "overdue_payments": [],
        "upcoming_payments": [],
        "payment_history": []
    }
    
    if schedule_doc.total_rent_amount > 0:
        analysis["financial_summary"]["payment_completion_rate"] = (
            flt(schedule_doc.paid_amount) / flt(schedule_doc.total_rent_amount) * 100
        )
    
    today = getdate(nowdate())
    
    for payment_schedule in schedule_doc.payment_schedules:
        payment_detail = {
            "due_date": payment_schedule.due_date,
            "payment_amount": payment_schedule.payment_amount,
            "paid_amount": payment_schedule.paid_amount,
            "outstanding": payment_schedule.outstanding,
            "payment_status": payment_schedule.payment_status,
            "payment_entry": payment_schedule.payment_entry,
            "payment_date": payment_schedule.payment_date,
            "days_overdue": 0 if not payment_schedule.due_date else max(0, (today - getdate(payment_schedule.due_date)).days)
        }
        
        analysis["payment_details"].append(payment_detail)
        
        # Categorize payments
        if flt(payment_schedule.outstanding) > 0:
            if getdate(payment_schedule.due_date) < today:
                analysis["overdue_payments"].append(payment_detail)
            else:
                analysis["upcoming_payments"].append(payment_detail)
        else:
            analysis["payment_history"].append(payment_detail)
    
    return analysis

def generate_payment_trends(schedules):
    """
    Generate payment trend analysis
    """
    trends = {
        "monthly_collections": [],
        "payment_patterns": {},
        "completion_rates": []
    }
    
    try:
        # Get monthly collection data for the last 12 months
        end_date = getdate(nowdate())
        start_date = add_months(end_date, -12)
        
        monthly_data = frappe.db.sql("""
            SELECT 
                DATE_FORMAT(ps.payment_date, '%%Y-%%m') as month,
                SUM(ps.paid_amount) as total_collected,
                COUNT(ps.name) as payment_count
            FROM `tabPayment Schedule` ps
            INNER JOIN `tabRental Payment Schedule` rps ON ps.parent = rps.name
            WHERE ps.payment_date >= %s
            AND ps.payment_date <= %s
            AND ps.payment_status = 'Paid'
            GROUP BY DATE_FORMAT(ps.payment_date, '%%Y-%%m')
            ORDER BY month
        """, (start_date, end_date), as_dict=True)
        
        trends["monthly_collections"] = monthly_data
        
        # Analyze payment patterns (on-time vs late payments)
        payment_patterns = frappe.db.sql("""
            SELECT 
                CASE 
                    WHEN ps.payment_date <= ps.due_date THEN 'On Time'
                    WHEN ps.payment_date <= DATE_ADD(ps.due_date, INTERVAL 5 DAY) THEN 'Grace Period'
                    ELSE 'Late'
                END as payment_timing,
                COUNT(*) as count,
                AVG(DATEDIFF(ps.payment_date, ps.due_date)) as avg_delay_days
            FROM `tabPayment Schedule` ps
            WHERE ps.payment_status = 'Paid'
            AND ps.payment_date IS NOT NULL
            GROUP BY payment_timing
        """, as_dict=True)
        
        for pattern in payment_patterns:
            trends["payment_patterns"][pattern.payment_timing] = {
                "count": pattern.count,
                "avg_delay_days": flt(pattern.avg_delay_days)
            }
            
    except Exception as e:
        frappe.log_error(f"Error generating payment trends: {str(e)}")
        
    return trends

def generate_overdue_analysis(schedules):
    """
    Generate overdue payment analysis
    """
    analysis = {
        "total_overdue_amount": 0,
        "overdue_count": 0,
        "aging_buckets": {
            "1-30_days": {"count": 0, "amount": 0},
            "31-60_days": {"count": 0, "amount": 0},
            "61-90_days": {"count": 0, "amount": 0},
            "90+_days": {"count": 0, "amount": 0}
        },
        "tenant_wise_overdue": [],
        "property_wise_overdue": []
    }
    
    try:
        today = getdate(nowdate())
        
        # Get all overdue payments
        overdue_payments = frappe.db.sql("""
            SELECT 
                ps.due_date,
                ps.outstanding,
                ps.payment_amount,
                rps.tenant,
                rps.property,
                rps.rental_unit,
                DATEDIFF(%s, ps.due_date) as days_overdue
            FROM `tabPayment Schedule` ps
            INNER JOIN `tabRental Payment Schedule` rps ON ps.parent = rps.name
            WHERE ps.outstanding > 0
            AND ps.due_date < %s
            ORDER BY ps.due_date
        """, (today, today), as_dict=True)
        
        tenant_overdue = {}
        property_overdue = {}
        
        for payment in overdue_payments:
            outstanding = flt(payment.outstanding)
            days_overdue = payment.days_overdue
            
            analysis["total_overdue_amount"] += outstanding
            analysis["overdue_count"] += 1
            
            # Aging bucket analysis
            if days_overdue <= 30:
                analysis["aging_buckets"]["1-30_days"]["count"] += 1
                analysis["aging_buckets"]["1-30_days"]["amount"] += outstanding
            elif days_overdue <= 60:
                analysis["aging_buckets"]["31-60_days"]["count"] += 1
                analysis["aging_buckets"]["31-60_days"]["amount"] += outstanding
            elif days_overdue <= 90:
                analysis["aging_buckets"]["61-90_days"]["count"] += 1
                analysis["aging_buckets"]["61-90_days"]["amount"] += outstanding
            else:
                analysis["aging_buckets"]["90+_days"]["count"] += 1
                analysis["aging_buckets"]["90+_days"]["amount"] += outstanding
                
            # Tenant-wise analysis
            tenant = payment.tenant
            if tenant not in tenant_overdue:
                tenant_overdue[tenant] = {"count": 0, "amount": 0}
            tenant_overdue[tenant]["count"] += 1
            tenant_overdue[tenant]["amount"] += outstanding
            
            # Property-wise analysis
            property_key = f"{payment.property} - {payment.rental_unit}"
            if property_key not in property_overdue:
                property_overdue[property_key] = {"count": 0, "amount": 0}
            property_overdue[property_key]["count"] += 1
            property_overdue[property_key]["amount"] += outstanding
            
        # Convert to lists for easier consumption
        analysis["tenant_wise_overdue"] = [
            {"tenant": k, "count": v["count"], "amount": v["amount"]}
            for k, v in tenant_overdue.items()
        ]
        analysis["property_wise_overdue"] = [
            {"property_unit": k, "count": v["count"], "amount": v["amount"]}
            for k, v in property_overdue.items()
        ]
        
        # Sort by amount descending
        analysis["tenant_wise_overdue"].sort(key=lambda x: x["amount"], reverse=True)
        analysis["property_wise_overdue"].sort(key=lambda x: x["amount"], reverse=True)
        
    except Exception as e:
        frappe.log_error(f"Error generating overdue analysis: {str(e)}")
        
    return analysis

@frappe.whitelist()
def get_payment_entry_linking_report(from_date=None, to_date=None, tenant=None, property_unit=None):
    """
    Generate report on Payment Entry linking status
    """
    try:
        if not from_date:
            from_date = add_months(nowdate(), -3)
        if not to_date:
            to_date = nowdate()
            
        filters = {
            "posting_date": ["between", [from_date, to_date]],
            "party_type": "Customer",
            "docstatus": 1
        }
        
        if tenant:
            # Find customer for tenant
            customer = find_customer_for_tenant(tenant)
            if customer:
                filters["party"] = customer
                
        payment_entries = frappe.get_all(
            "Payment Entry",
            filters=filters,
            fields=["name", "party", "paid_amount", "posting_date", "reference_no", "mode_of_payment"]
        )
        
        report_data = {
            "summary": {
                "total_payments": len(payment_entries),
                "linked_payments": 0,
                "unlinked_payments": 0,
                "total_amount": 0,
                "linked_amount": 0,
                "unlinked_amount": 0
            },
            "payment_details": []
        }
        
        for payment in payment_entries:
            # Check if payment is linked to any payment schedule
            linked_schedules = frappe.db.sql("""
                SELECT 
                    ps.name as schedule_name,
                    ps.parent as payment_schedule_parent,
                    rps.tenant,
                    rps.property,
                    rps.rental_unit
                FROM `tabPayment Schedule` ps
                INNER JOIN `tabRental Payment Schedule` rps ON ps.parent = rps.name
                WHERE ps.payment_entry = %s
            """, (payment.name,), as_dict=True)
            
            payment_detail = {
                "payment_entry": payment.name,
                "customer": payment.party,
                "amount": payment.paid_amount,
                "date": payment.posting_date,
                "reference": payment.reference_no,
                "mode_of_payment": payment.mode_of_payment,
                "is_linked": len(linked_schedules) > 0,
                "linked_schedules": linked_schedules,
                "tenant": linked_schedules[0]["tenant"] if linked_schedules else None,
                "property_unit": f"{linked_schedules[0]['property']} - {linked_schedules[0]['rental_unit']}" if linked_schedules else None
            }
            
            report_data["payment_details"].append(payment_detail)
            report_data["summary"]["total_amount"] += flt(payment.paid_amount)
            
            if payment_detail["is_linked"]:
                report_data["summary"]["linked_payments"] += 1
                report_data["summary"]["linked_amount"] += flt(payment.paid_amount)
            else:
                report_data["summary"]["unlinked_payments"] += 1
                report_data["summary"]["unlinked_amount"] += flt(payment.paid_amount)
                
        return report_data
        
    except Exception as e:
        frappe.log_error(f"Error generating payment entry linking report: {str(e)}")
        return None

def find_customer_for_tenant(tenant):
    """
    Find customer associated with a tenant
    """
    try:
        # Try direct customer field
        customer = frappe.db.get_value("Tenant", tenant, "customer")
        if customer:
            return customer
            
        # Try pattern matching
        customer_pattern = f"TENANT-{tenant}"
        customer = frappe.db.get_value("Customer", {"name": ["like", f"%{customer_pattern}%"]}, "name")
        if customer:
            return customer
            
        # Try email matching
        tenant_doc = frappe.get_doc("Tenant", tenant)
        if tenant_doc.email:
            customer = frappe.db.get_value("Customer", {"email_id": tenant_doc.email}, "name")
            if customer:
                return customer
                
        return None
        
    except Exception as e:
        frappe.log_error(f"Error finding customer for tenant: {str(e)}")
        return None

@frappe.whitelist()
def get_rental_payment_summary(tenant=None, property_unit=None, from_date=None, to_date=None):
    """
    Get comprehensive rental payment summary
    """
    try:
        filters = {}
        if tenant:
            filters["tenant"] = tenant
        if property_unit:
            filters["rental_unit"] = property_unit
        if from_date and to_date:
            filters["start_date"] = ["<=", to_date]
            filters["end_date"] = [">=", from_date]
            
        schedules = frappe.get_all(
            "Rental Payment Schedule",
            filters=filters,
            fields=["name", "tenant", "property", "rental_unit", "total_rent_amount", 
                   "paid_amount", "outstanding_amount", "schedule_status"]
        )
        
        summary = {
            "financial_overview": {
                "total_scheduled": 0,
                "total_collected": 0,
                "total_outstanding": 0,
                "collection_rate": 0
            },
            "payment_status": {
                "on_time_payments": 0,
                "late_payments": 0,
                "overdue_payments": 0,
                "pending_payments": 0
            },
            "tenant_performance": [],
            "property_performance": []
        }
        
        tenant_data = {}
        property_data = {}
        
        for schedule in schedules:
            schedule_doc = frappe.get_doc("Rental Payment Schedule", schedule.name)
            
            # Financial overview
            summary["financial_overview"]["total_scheduled"] += flt(schedule.total_rent_amount)
            summary["financial_overview"]["total_collected"] += flt(schedule.paid_amount)
            summary["financial_overview"]["total_outstanding"] += flt(schedule.outstanding_amount)
            
            # Analyze individual payments
            today = getdate(nowdate())
            for payment in schedule_doc.payment_schedules:
                if payment.payment_status == "Paid":
                    if payment.payment_date and getdate(payment.payment_date) <= getdate(payment.due_date):
                        summary["payment_status"]["on_time_payments"] += 1
                    else:
                        summary["payment_status"]["late_payments"] += 1
                elif flt(payment.outstanding) > 0:
                    if getdate(payment.due_date) < today:
                        summary["payment_status"]["overdue_payments"] += 1
                    else:
                        summary["payment_status"]["pending_payments"] += 1
                        
            # Tenant performance
            tenant = schedule.tenant
            if tenant not in tenant_data:
                tenant_data[tenant] = {
                    "scheduled": 0, "collected": 0, "outstanding": 0,
                    "on_time": 0, "late": 0, "overdue": 0
                }
            tenant_data[tenant]["scheduled"] += flt(schedule.total_rent_amount)
            tenant_data[tenant]["collected"] += flt(schedule.paid_amount)
            tenant_data[tenant]["outstanding"] += flt(schedule.outstanding_amount)
            
            # Property performance
            property_key = f"{schedule.property} - {schedule.rental_unit}"
            if property_key not in property_data:
                property_data[property_key] = {
                    "scheduled": 0, "collected": 0, "outstanding": 0,
                    "occupancy_months": 0
                }
            property_data[property_key]["scheduled"] += flt(schedule.total_rent_amount)
            property_data[property_key]["collected"] += flt(schedule.paid_amount)
            property_data[property_key]["outstanding"] += flt(schedule.outstanding_amount)
            
        # Calculate collection rate
        if summary["financial_overview"]["total_scheduled"] > 0:
            summary["financial_overview"]["collection_rate"] = (
                summary["financial_overview"]["total_collected"] / 
                summary["financial_overview"]["total_scheduled"] * 100
            )
            
        # Convert to lists
        for tenant, data in tenant_data.items():
            data["tenant"] = tenant
            data["collection_rate"] = (data["collected"] / data["scheduled"] * 100) if data["scheduled"] > 0 else 0
            summary["tenant_performance"].append(data)
            
        for property_key, data in property_data.items():
            data["property_unit"] = property_key
            data["collection_rate"] = (data["collected"] / data["scheduled"] * 100) if data["scheduled"] > 0 else 0
            summary["property_performance"].append(data)
            
        # Sort by collection rate
        summary["tenant_performance"].sort(key=lambda x: x["collection_rate"], reverse=True)
        summary["property_performance"].sort(key=lambda x: x["collection_rate"], reverse=True)
        
        return summary
        
    except Exception as e:
        frappe.log_error(f"Error generating rental payment summary: {str(e)}")
        return None

@frappe.whitelist()
def export_payment_data(format_type="excel", filters=None):
    """
    Export payment data in various formats
    """
    try:
        if not filters:
            filters = {}
            
        # Get payment data
        payment_data = get_payment_entry_linking_report(
            filters.get("from_date"),
            filters.get("to_date"),
            filters.get("tenant"),
            filters.get("property_unit")
        )
        
        if format_type == "excel":
            return export_to_excel(payment_data)
        elif format_type == "csv":
            return export_to_csv(payment_data)
        elif format_type == "pdf":
            return export_to_pdf(payment_data)
        else:
            return {"error": "Unsupported format type"}
            
    except Exception as e:
        frappe.log_error(f"Error exporting payment data: {str(e)}")
        return {"error": str(e)}

def export_to_excel(payment_data):
    """
    Export payment data to Excel format
    """
    # Implementation would use frappe.utils.xlsxwriter or similar
    # For now, return data structure that can be processed by frontend
    return {
        "format": "excel",
        "data": payment_data,
        "filename": f"payment_report_{nowdate()}.xlsx"
    }

def export_to_csv(payment_data):
    """
    Export payment data to CSV format
    """
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = ["Payment Entry", "Customer", "Amount", "Date", "Reference", "Linked", "Tenant", "Property Unit"]
    writer.writerow(headers)
    
    # Write data
    for payment in payment_data.get("payment_details", []):
        writer.writerow([
            payment.get("payment_entry"),
            payment.get("customer"),
            payment.get("amount"),
            payment.get("date"),
            payment.get("reference"),
            "Yes" if payment.get("is_linked") else "No",
            payment.get("tenant"),
            payment.get("property_unit")
        ])
    
    return {
        "format": "csv",
        "content": output.getvalue(),
        "filename": f"payment_report_{nowdate()}.csv"
    }

def export_to_pdf(payment_data):
    """
    Export payment data to PDF format
    """
    # Implementation would use frappe.utils.pdf or similar
    # For now, return data structure
    return {
        "format": "pdf",
        "data": payment_data,
        "filename": f"payment_report_{nowdate()}.pdf"
    }

@frappe.whitelist()
def get_property_performance(property):
    """
    Get property performance data for dashboard
    """
    try:
        if not property:
            return {}
            
        # Get property document
        property_doc = frappe.get_doc("Property", property)
        
        # Get rental units for this property
        units = frappe.get_all(
            "Rental Unit",
            filters={"property": property},
            fields=["name", "unit_status", "monthly_rent", "current_tenant"]
        )
        
        # Calculate unit statistics
        total_units = len(units)
        occupied_units = len([u for u in units if u.unit_status == "Occupied"])
        available_units = len([u for u in units if u.unit_status == "Available"])
        maintenance_units = len([u for u in units if u.unit_status in ["Maintenance", "Renovation"]])
        
        # Calculate occupancy rate
        occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
        
        # Calculate rental income
        total_potential_rent = sum([flt(u.monthly_rent) for u in units if u.monthly_rent])
        current_rent = sum([flt(u.monthly_rent) for u in units if u.unit_status == "Occupied" and u.monthly_rent])
        
        # Get active contracts count
        active_contracts = frappe.db.count("Rental Contract", {
            "property": property,
            "contract_status": "Active"
        })
        
        return {
            "total_units": total_units,
            "occupied_units": occupied_units,
            "available_units": available_units,
            "maintenance_units": maintenance_units,
            "occupancy_rate": occupancy_rate,
            "total_potential_rent": total_potential_rent,
            "current_rent": current_rent,
            "active_contracts": active_contracts,
            "rental_efficiency": (current_rent / total_potential_rent * 100) if total_potential_rent > 0 else 0
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting property performance for {property}: {str(e)}")
        return {}

@frappe.whitelist()
def get_property_performance(property):
    """
    Get property performance data for dashboard
    """
    try:
        if not property:
            return {}
            
        # Get property document
        property_doc = frappe.get_doc("Property", property)
        
        # Get rental units for this property
        units = frappe.get_all(
            "Rental Unit",
            filters={"property": property},
            fields=["name", "unit_status", "monthly_rent", "current_tenant"]
        )
        
        # Calculate unit statistics
        total_units = len(units)
        occupied_units = len([u for u in units if u.unit_status == "Occupied"])
        available_units = len([u for u in units if u.unit_status == "Available"])
        maintenance_units = len([u for u in units if u.unit_status in ["Maintenance", "Renovation"]])
        
        # Calculate occupancy rate
        occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
        
        # Calculate rental income
        total_potential_rent = sum([flt(u.monthly_rent) for u in units if u.monthly_rent])
        current_rent = sum([flt(u.monthly_rent) for u in units if u.unit_status == "Occupied" and u.monthly_rent])
        
        # Get active contracts count
        active_contracts = frappe.db.count("Rental Contract", {
            "property": property,
            "contract_status": "Active"
        })
        
        return {
            "total_units": total_units,
            "occupied_units": occupied_units,
            "available_units": available_units,
            "maintenance_units": maintenance_units,
            "occupancy_rate": occupancy_rate,
            "total_potential_rent": total_potential_rent,
            "current_rent": current_rent,
            "active_contracts": active_contracts,
            "rental_efficiency": (current_rent / total_potential_rent * 100) if total_potential_rent > 0 else 0
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting property performance for {property}: {str(e)}")
        return {}

