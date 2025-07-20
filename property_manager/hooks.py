app_name = "property_manager"
app_title = "Property Manager"
app_publisher = "Farah"
app_description = "Property management system for rental units with contracts and invoicing"
app_email = "farah@domain.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/property_manager/css/property_manager.css"
# app_include_js = "/assets/property_manager/js/property_manager.js"

# include js, css files in header of web template
# web_include_css = "/assets/property_manager/css/property_manager.css"
# web_include_js = "/assets/property_manager/js/property_manager.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "property_manager/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Rental Contract": "public/js/rental_contract.js",
    "Rent Schedule": "public/js/rent_schedule.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "property_manager.install.before_install"
# after_install = "property_manager.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "property_manager.uninstall.before_uninstall"
# after_uninstall = "property_manager.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "property_manager.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Rental Contract": {
        "on_submit": "property_manager.property_manager.doctype.rental_contract.rental_contract.generate_rent_schedules"
    },
    "Rent Schedule": {
        "on_update": "property_manager.property_manager.doctype.rent_schedule.rent_schedule.create_sales_invoice_on_payment"
    }
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    "daily": [
        "property_manager.property_manager.doctype.rent_schedule.rent_schedule.mark_overdue_rents"
    ],
    "monthly": [
        "property_manager.property_manager.doctype.rent_schedule.rent_schedule.generate_monthly_schedules"
    ],
}

# Testing
# -------

# before_tests = "property_manager.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "property_manager.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "property_manager.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["property_manager.utils.before_request"]
# after_request = ["property_manager.utils.after_request"]

# Job Events
# ----------
# before_job = ["property_manager.utils.before_job"]
# after_job = ["property_manager.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"partial": 1,
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"property_manager.auth.validate"
# ]

