const googleGroupEmailField = $("#id_google_email");
const googleGroupAuthorityCheckboxFormGroup = $("#id_google_as_members_authority").parent().parent();

function changedGoogleGroupEmailField() {
    const value = googleGroupEmailField.val();
    googleGroupAuthorityCheckboxFormGroup.toggle(!!value);
}

$(function () {
    changedGoogleGroupEmailField();
    googleGroupEmailField.on("input", changedGoogleGroupEmailField);
});
