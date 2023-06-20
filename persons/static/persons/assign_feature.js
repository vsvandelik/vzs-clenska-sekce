const feature_type_select_box = $("#id_feature");
const assign_form = $("#assign-form");

function changed_select_box(e) {
    let selected_feature = parseInt(feature_type_select_box.val());
    if (isNaN(selected_feature)) {
        $("input", assign_form).each(function () {
            $(this).parent().parent().show();
        });
        return;
    }

    Object.entries(features[selected_feature]).forEach(entry => {
        const [key, value] = entry;
        let input_div_form_group = $(`input[name=${key}]`, assign_form).parent().parent();
        if (value)
            input_div_form_group.show();
        else
            input_div_form_group.hide();
    });
}

$(function () {
    changed_select_box();
    feature_type_select_box.change(changed_select_box);
});
