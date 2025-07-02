frappe.ui.form.on("Frappe Exporter Settings", {
	refresh: function (frm) {
		// Add custom buttons for managing the doctype whitelist
		const html_field = frm.get_field("doctype_whitelisting_html");
		const $wrapper = $(html_field.wrapper).empty();

		const button_group = $(`<div class="btn-group" style="margin-bottom: 10px;"></div>`);

		const select_all_btn = $(`<button class="btn btn-default btn-xs">Select All</button>`);
		const unselect_all_btn = $(
			`<button class="btn btn-default btn-xs" style="margin-left: 5px;">Unselect All</button>`
		);

		button_group.append(select_all_btn).append(unselect_all_btn);
		$wrapper.append(button_group);

		// Fetch the list of custom doctypes from the new API path
		frappe.call({
			method: "frappe_exporter.api.get_custom_doctypes",
			callback: function (r) {
				if (r.message) {
					const all_doctypes = r.message;

					// "Select All" button functionality
					select_all_btn.on("click", () => {
						frm.clear_table("whitelisted_doctypes");
						all_doctypes.forEach((dt) => {
							frm.add_child("whitelisted_doctypes", {
								doctype_name: dt,
							});
						});
						frm.refresh_field("whitelisted_doctypes");
						frappe.show_alert({
							message: `Added all ${all_doctypes.length} custom doctypes to the whitelist.`,
							indicator: "green",
						});
					});

					// "Unselect All" button functionality
					unselect_all_btn.on("click", () => {
						frm.clear_table("whitelisted_doctypes");
						frm.refresh_field("whitelisted_doctypes");
						frappe.show_alert({
							message: "Cleared the doctype whitelist.",
							indicator: "orange",
						});
					});
				}
			},
		});
	},
});
