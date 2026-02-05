# Copyright (c) 2026, Greycube Technologies and contributors
# For license information, please see license.txt

import frappe
import frappe.utils
from datetime import datetime

def execute(filters=None):
	if not filters : filter = {}
	columns, data = [], []

	columns = get_columns()
	data = get_data(filters)

	chart = get_chart_data(data)
	return columns, data, None, chart

def get_columns():
	return [
		{
			"fieldname" : "month",
			"fieldtype" : "Data",
			"label" : "Product Month",
			"width" : 150
		},
		{
			"fieldname" : "planned_qty",
			"fieldtype" : "Float",
			"label" : "Planned Qty",
			"width" : 150
		},
		{
			"fieldname" : "actual_qty",
			"fieldtype" : "Float",
			"label" : "Actual Qty",
			"width" : 150
		}
	]

def get_data(filters):

	conditions = {}
	for key, value in filters.items():
		if filters.get(key):
			conditions[key] = value
		

	d = frappe.db.sql(
		f"""
		SELECT
			IFNULL(CONCAT(MONTHNAME(L.planned_start_date), " ", YEAR(L.planned_start_date)), CONCAT(MONTHNAME(R.posting_date), " ", YEAR(R.posting_date))) AS month,
			IFNULL(L.planned_qty, 0) AS planned_qty,
			IFNULL(R.actual_qty, 0) AS actual_qty
			
		FROM (
			SELECT
				SUM(qty) as planned_qty,
				planned_start_date,
				name
			FROM `tabWork Order`
			WHERE 
				production_item = "{conditions["name"]}"
				AND (planned_start_date BETWEEN "{conditions["from_date"]}" AND "{conditions["to_date"]}")
				AND docstatus = 1
			GROUP BY MONTHNAME(planned_start_date), YEAR(planned_start_date)
			ORDER BY MIN(planned_start_date)
		) L
		LEFT JOIN (
			SELECT 
				SUM(fg_completed_qty) as actual_qty,
				posting_date,
				work_order,
				two.name AS name
			FROM `tabWork Order` two
			LEFT JOIN (
					SELECT 
						ise.work_order AS work_order,
						ise.posting_date AS posting_date,
						ise.stock_entry_type AS stock_entry_type,
						ise.fg_completed_qty AS fg_completed_qty,
						ise.docstatus AS docstatus
					FROM `tabStock Entry` ise
					JOIN `tabStock Entry Detail` ised
					ON ised.is_finished_item = 1
						AND ised.parent = ise.name
				) tse
			ON two.name = tse.work_order
				AND tse.stock_entry_type = "Manufacture"
			WHERE 
				two.production_item = "{conditions["name"]}"
				AND (posting_date BETWEEN "{conditions["from_date"]}" AND "{conditions["to_date"]}")
				AND tse.docstatus = 1
			GROUP BY MONTHNAME(posting_date), YEAR(posting_date)
			ORDER BY MIN(posting_date)
		)R
		ON MONTHNAME(L.planned_start_date) = MONTHNAME(R.posting_date)
			AND YEAR(L.planned_start_date) = YEAR(R.posting_date)

		UNION 

		SELECT
			IFNULL(CONCAT(MONTHNAME(L.planned_start_date), " ", YEAR(L.planned_start_date)), CONCAT(MONTHNAME(R.posting_date), " ", YEAR(R.posting_date))) AS month,
			IFNULL(L.planned_qty, 0) AS planned_qty,
			IFNULL(R.actual_qty, 0) AS actual_qty
		FROM (
			SELECT
				SUM(qty) as planned_qty,
				planned_start_date,
				name
			FROM `tabWork Order`
			WHERE 
				production_item = "{conditions["name"]}"
				AND (planned_start_date BETWEEN "{conditions["from_date"]}" AND "{conditions["to_date"]}")
				AND docstatus = 1
			GROUP BY MONTHNAME(planned_start_date), YEAR(planned_start_date)
			ORDER BY MIN(planned_start_date)
		) L
		RIGHT JOIN (
			SELECT 
				SUM(fg_completed_qty) as actual_qty,
				posting_date,
				work_order,
				two.name AS name
			FROM `tabWork Order` two
			LEFT JOIN (
					SELECT 
						ise.work_order AS work_order,
						ise.posting_date AS posting_date,
						ise.stock_entry_type AS stock_entry_type,
						ise.fg_completed_qty AS fg_completed_qty,
						ise.docstatus AS docstatus
					FROM `tabStock Entry` ise
					JOIN `tabStock Entry Detail` ised
					ON ised.is_finished_item = 1
						AND ised.parent = ise.name
				) tse
			ON two.name = tse.work_order
				AND tse.stock_entry_type = "Manufacture"
			WHERE 
				two.production_item = "{conditions["name"]}"
				AND (posting_date BETWEEN "{conditions["from_date"]}" AND "{conditions["to_date"]}")
				AND tse.docstatus = 1
			GROUP BY MONTHNAME(posting_date), YEAR(posting_date)
			ORDER BY MIN(posting_date)
		)R
		ON MONTHNAME(L.planned_start_date) = MONTHNAME(R.posting_date)
			AND YEAR(L.planned_start_date) = YEAR(R.posting_date)


		""", as_dict=1
	)

	from_date_string = conditions["from_date"]
	to_date_string = conditions["to_date"]
	from_date_object = datetime.strptime(str(from_date_string), '%Y-%m-%d')
	to_date_object = datetime.strptime(str(to_date_string), '%Y-%m-%d')
	months = []

	while from_date_string<=to_date_string:
		this_month = frappe.utils.get_datetime(from_date_string).strftime("%B")
		this_year = str((from_date_object.year))
		months.append(this_month + " " + this_year)
		from_date_string = (frappe.utils.add_months(from_date_string, 1))
		from_date_object = datetime.strptime(str(from_date_string), '%Y-%m-%d')

	prep_data = []

	for month in months:
		entry = {
			"month" : month,
			"planned_qty" : 0,
			"actual_qty" : 0
		}
		prep_data.append(entry)
	
	for data in prep_data:
		for entry in d:
			if data["month"] == entry["month"]:
				data["planned_qty"] = entry["planned_qty"]
				data["actual_qty"] = entry["actual_qty"]


	return prep_data

def get_chart_data(data):
	if not data:
		return None
	
	labels = []
	for entry in data:
		labels.append(entry["month"])

	datasets = [
		{
			"name": "Planned Qty",
			"type": "bar",
			"values": add_value("planned_qty", data)
		},
		{
			"name": "Actual Qty", 
			"type": "bar",
			"values": add_value("actual_qty", data)
    	}
	]

	chart = {

		"data" : {
			"labels": labels,
			"datasets": datasets
		},
		"type": "bar",
		"height": 300,
		"colors": ["#fcff5e", "#ff6529"],
		"valuesOverPoints" : 1,
	}
	
	return chart



def add_value(str, data):
	list = []
	for entry in data:
		list.append(entry[str])
	
	return list

