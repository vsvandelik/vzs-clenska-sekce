const assignableCheckbox = $("#id_assignable");

function changedAssignableCheckbox() {
    const checked = assignableCheckbox.prop("checked");
    const formGroups = assignableCheckbox.parent().parent().nextAll(".form-group");
    checked ? formGroups.show() : formGroups.hide();

    if (!checked) {
        formGroups.find("input[type=checkbox]").prop("checked", false);
    }
}

$(function () {
    changedAssignableCheckbox();
    assignableCheckbox.change(changedAssignableCheckbox);
});