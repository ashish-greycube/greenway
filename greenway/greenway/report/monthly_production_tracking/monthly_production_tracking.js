// Copyright (c) 2026, Greycube Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Monthly Production Tracking"] = {
	"filters": [
		{
			"fieldname" : "name",
			"fieldtype" : "Link",
			"label" : "Item Code",
			"options" : "Item",
			"reqd" : 1
		},
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"reqd" : "1",
			"default" : frappe.datetime.add_months(frappe.datetime.get_today(), -12)
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd" : 1,
		},

	]
};

