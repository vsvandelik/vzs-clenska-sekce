const assignableCheckbox = $("#id_assignable");

function changedAssignableCheckbox() {
    ""
    "Toggle visibility for all divs with class form-group which are after the assignable checkbox."
    ""
    const checked = assignableCheckbox.prop("checked");
    const formGroups = assignableCheckbox.parent().parent().nextAll(".form-group");
    checked ? formGroups.show() : formGroups.hide();
}

$(function () {
    changedAssignableCheckbox();
    assignableCheckbox.change(changedAssignableCheckbox);
});