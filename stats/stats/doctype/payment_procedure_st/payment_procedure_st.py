# Copyright (c) 2024, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
import erpnext
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form,today


class PaymentProcedureST(Document):

	def on_submit(self):
		if not self.payment_type:
			frappe.throw(_("Please select payment type"))
		self.create_payment_journal_entry_from_payment_procedure()

	def create_payment_journal_entry_from_payment_procedure(self):
		payment_je_doc = frappe.new_doc("Journal Entry")
		payment_je_doc.voucher_type = "Journal Entry"
		payment_je_doc.posting_date = today()
		payment_je_doc.custom_payment_procedure_reference = self.name

		accounts = []

		company = erpnext.get_default_company()
		company_business_trip_budget_expense_account = frappe.db.get_value("Company",company,"custom_business_trip_budget_expense_account")
		company_default_cost_center = frappe.db.get_value("Company",company,"cost_center")
		total_employee_amount = 0
		for row in self.employees:
			total_employee_amount = total_employee_amount + (row.amount or 0)

		if self.payment_type == "Direct":
			accounts_row = {
				"account":company_business_trip_budget_expense_account,
				"cost_center":company_default_cost_center,
				"debit_in_account_currency":total_employee_amount,
			}
			accounts.append(accounts_row)
			mode_of_payment_account = frappe.db.get_value("Mode of Payment Account",{"parent":self.mode_of_payment},["default_account"])
			if mode_of_payment_account:
				accounts_row_2 = {
					"account":mode_of_payment_account,
					"cost_center":company_default_cost_center,
					"credit_in_account_currency":total_employee_amount,
				}
				accounts.append(accounts_row_2)
			else:
				frappe.throw(_("Please set company default {0} account in {1}").format(self.mode_of_payment,get_link_to_form("Mode of Payment",self.mode_of_payment)))
		
		elif self.payment_type == "Indirect":
			mode_of_payment_account = frappe.db.get_value("Mode of Payment Account",{"parent":self.mode_of_payment},["default_account"])
			
			if self.middle_bank_account:
				accounts_row_2 = {
					"account":self.middle_bank_account,
					"cost_center":company_default_cost_center,
					"debit_in_account_currency":total_employee_amount,
				}
				accounts.append(accounts_row_2)

			if mode_of_payment_account:
				accounts_row = {
					"account":mode_of_payment_account,
					"cost_center":company_default_cost_center,
					"credit_in_account_currency":total_employee_amount,
				}
				accounts.append(accounts_row)
			else:
				frappe.throw(_("Please set company default {0} account in {1}").format(self.mode_of_payment,get_link_to_form("Mode of Payment",self.mode_of_payment)))

		payment_je_doc.set("accounts",accounts)
		payment_je_doc.run_method('set_missing_values')
		payment_je_doc.save(ignore_permissions=True)

		frappe.msgprint(_("Payment Journal Entry is created from Payment Procedure {0}").format(get_link_to_form("Journal Entry",payment_je_doc.name)),alert=1)