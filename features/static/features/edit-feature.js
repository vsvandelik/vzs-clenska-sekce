const assignableCheckbox = $("#id_assignable");

function changedAssignableCheckbox() {
    const checked = assignableCheckbox.prop("checked");
    const formGroups = assignableCheckbox.parent().parent().nextAll(".form-group");
    checked ? formGroups.show() : formGroups.hide();

    if (!checked) {
        formGroups.find("input[type=checkbox]").prop("checked", false);
        formsGroups.find("input[type=number]").val();
    }
}

$(function () {
    changedAssignableCheckbox();
    assignableCheckbox.change(changedAssignableCheckbox);
});