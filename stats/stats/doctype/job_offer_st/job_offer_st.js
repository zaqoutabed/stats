// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Job Offer ST", {
	setup(frm) {
		frm.set_query("main_department", function (doc) {
			return {
				query: "stats.api.get_main_department",
			};
		});
		frm.set_query("sub_department", function (doc) {
			if (frm.doc.main_department) {
				return {
					filters: {
						parent_department: frm.doc.main_department,
						is_group: 0
					}
				};
			}
		})
	},
	refresh: function (frm) {
		if (frm.doc.status == 'Accepted') {
			frm.set_df_property('date_of_birth', 'reqd', 1)
			frm.add_custom_button(
				__("Create Employee"),
				function () {
					frappe.model.open_mapped_doc({
						method: "stats.stats.doctype.job_offer_st.job_offer_st.make_employee",
						frm: frm,
					});
				});
		}
	}
});

frappe.ui.form.on("Job Offer Details ST", {
	value: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn]
		if (row.offer_term) {
			frappe.db.get_value('Offer Term', row.offer_term, 'custom_is_monthly_salary_component')
				.then(r => {
					if(r.message.custom_is_monthly_salary_component == 1){
						console.log(r.message.custom_is_monthly_salary_component == 1)
						frm.save()
					} // Open
				})
		}
	}
})