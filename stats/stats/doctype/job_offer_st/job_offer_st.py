# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.model.mapper import get_mapped_doc
from stats.api import get_monthly_salary_from_job_offer

class JobOfferST(Document):
	def validate(self):
		self.fetch_salary_tables_from_contract_type()
		self.calculate_salary_earnings_and_deduction()
		self.validate_offer_term_details()
		self.validate_duplicate_entry_for_offer_term_with_monthly_salary_component()
		self.validate_value_in_offer_details()
		self.validate_total_monthly_salary_earnings_and_deductions()

	def fetch_salary_tables_from_contract_type(self):
		if self.contract_type:
			contract_type = frappe.get_doc("Contract Type ST", self.contract_type)
			if len(self.offer_details) > 0:
				if len(self.earning) == 0:
					for ear in contract_type.earning:
						earn = self.append("earning", {})
						earn.earning = ear.earning
						earn.percent = ear.percent

				if len(self.deduction) == 0:
					for ded in contract_type.deduction:
						dedu = self.append("deduction", {})
						dedu.deduction = ded.deduction
						dedu.percent = ded.percent
			else:
				frappe.throw(_("Please fill offer deatils first"))

	def validate_offer_term_details(self):
		offer_term_in_offer_details_list = []
		if len(self.offer_details):
			offer_term_with_monthly_salary_component = frappe.db.exists("Offer Term", {"custom_is_monthly_salary_component": 1})
			if offer_term_with_monthly_salary_component:
				for row in self.offer_details:
					offer_term_in_offer_details_list.append(row.offer_term)
				if offer_term_with_monthly_salary_component not in offer_term_in_offer_details_list:
					frappe.throw(_("There must be one offer term with monthly salary component "))

	def validate_duplicate_entry_for_offer_term_with_monthly_salary_component(self):
		offer_term_with_monthly_salary_component = frappe.db.exists("Offer Term", {"custom_is_monthly_salary_component": 1})
		offer_details_list = []
		if len(self.offer_details):
			for row in self.offer_details:
				if row.offer_term not in offer_details_list:
					offer_details_list.append(row.offer_term)
				else :
					if row.offer_term == offer_term_with_monthly_salary_component:
						frappe.throw(_("Row #{0}: You cannot add {1} again.").format(row.idx,row.offer_term))

	def validate_value_in_offer_details(self):
		if len(self.offer_details):
			for row in self.offer_details:
				is_monthly_salary_component = frappe.db.get_value("Offer Term",row.offer_term,"custom_is_monthly_salary_component")
				if is_monthly_salary_component == 1:
					if not row.value:
						frappe.throw(_("Row #{0}: Value cannot be 0").format(row.idx))

	def calculate_salary_earnings_and_deduction(self):
		monthly_salary = 0

		if len(self.offer_details) > 0:
			for offer in self.offer_details:
				monthly_salary_component = frappe.db.get_value('Offer Term', offer.offer_term, 'custom_is_monthly_salary_component')
				if monthly_salary_component == 1:
					monthly_salary = offer.value

		# total_monthly_salary = 0
		if monthly_salary > 0 :
			if len(self.earning)>0:
				for ear in self.earning:
					if int(ear.percent) > 0:
						ear.amount = (monthly_salary) * (ear.percent / 100)
						# total_monthly_salary = total_monthly_salary + ear.amount

			if len(self.deduction)>0:
				for ded in self.deduction:
					if ded.percent > 0:
						ded.amount = (monthly_salary) * (ded.percent / 100)
						# total_monthly_salary = total_monthly_salary + ded.amount

			# print(total_monthly_salary, '--total_monthly_salary')
			print(monthly_salary, '---monthly_salary')
			# if total_monthly_salary != monthly_salary:
			# 	frappe.throw(_("Total of earnings and deductions amount must be {0}").format(monthly_salary))

	def validate_total_monthly_salary_earnings_and_deductions(self):
		if not self.is_new():
			monthly_salary = get_monthly_salary_from_job_offer(self.name)
			if monthly_salary > 0 :
				total_monthly_salary = 0
				if len(self.earning)>0:
					for ear in self.earning:
						total_monthly_salary = total_monthly_salary + ear.amount
				if len(self.deduction)>0:
					for ded in self.deduction:
						total_monthly_salary = total_monthly_salary + ded.amount

				if total_monthly_salary != monthly_salary:
					frappe.throw(_("Total of earnings and deductions amount must be {0} not {1}.").format(monthly_salary, total_monthly_salary))

@frappe.whitelist()
def make_employee(source_name, target_doc=None):
	doc = frappe.get_doc("Job Offer ST", source_name)
	# doc.validate_employee_creation()

	def set_missing_values(source, target):
		target.custom_job_offer_reference = source.name
		target.personal_email = source.email
		target.status = "Active"
		target.first_name = source.candidate_name
		target.department = source.main_department
		target.custom_sub_department = source.sub_department
		target.custom_contract_type = source.contract_type
		target.employment_type = source.employment_type
		target.custom_idresidency_number = source.id_igama_no
		target.custom_id_expiration_date = source.id_expiration_date
		target.cell_number = source.phone_no

	doc = get_mapped_doc(
		"Job Offer ST",
		source_name,
		{
			"Job Offer ST": {
				"doctype": "Employee",
				"field_map": {
					"first_name": "candidate_name",
					"employee_grade": "grade",
				},
			}
		},
		target_doc,
		set_missing_values,
	)
	return doc