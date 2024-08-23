// Copyright (c) 2024, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Business Trip Processing ST", {
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

    refresh(frm) {
        if (!frm.is_new() && (frm.doc.business_trip_detail).length < 1) {
            frm.add_custom_button(__('Fetch Business Trips'), () => fetch_business_trips_from_business_trip_request(frm));
        }
    }
});

let fetch_business_trips_from_business_trip_request = function (frm) {
    frappe.call({
        method: "stats.stats.doctype.business_trip_processing_st.business_trip_processing_st.fetch_business_trip_request",
        args: {
            name: frm.doc.name
        },
        callback: function (r) {
            console.log(r.message,"response")
            r.message.forEach((ele) => {
                var d = frm.add_child("business_trip_detail");
                // d.business_trip_reference = ele.name
                frappe.model.set_value(d.doctype, d.name, "business_trip_reference", ele.name)
            })
            frm.refresh_field('business_trip_detail')
            frm.save()
        }
    })
}