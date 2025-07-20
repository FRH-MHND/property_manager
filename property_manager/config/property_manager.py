from frappe import _

def get_data():
    return [
        {
            "label": _("Property Management"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Property",
                    "label": _("Property"),
                    "description": _("Manage properties and their details")
                },
                {
                    "type": "doctype",
                    "name": "Rental Unit",
                    "label": _("Rental Unit"),
                    "description": _("Manage individual rental units")
                },
                {
                    "type": "doctype",
                    "name": "Tenant",
                    "label": _("Tenant"),
                    "description": _("Manage tenant information")
                }
            ]
        },
        {
            "label": _("Rental Management"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Rental Contract",
                    "label": _("Rental Contract"),
                    "description": _("Manage rental agreements and contracts")
                },
                {
                    "type": "doctype",
                    "name": "Rent Schedule",
                    "label": _("Rent Schedule"),
                    "description": _("Track rent payment schedules")
                }
            ]
        },
        {
            "label": _("Reports"),
            "items": [
                {
                    "type": "report",
                    "name": "Property Occupancy Report",
                    "label": _("Property Occupancy Report"),
                    "doctype": "Rental Unit",
                    "is_query_report": True
                },
                {
                    "type": "report",
                    "name": "Rent Collection Report",
                    "label": _("Rent Collection Report"),
                    "doctype": "Rent Schedule",
                    "is_query_report": True
                },
                {
                    "type": "report",
                    "name": "Tenant Payment History",
                    "label": _("Tenant Payment History"),
                    "doctype": "Rent Schedule",
                    "is_query_report": True
                }
            ]
        }
    ]

