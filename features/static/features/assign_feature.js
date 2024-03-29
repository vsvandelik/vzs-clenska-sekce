const featureTypeSelectBox = $("#id_feature");
const feeField = $("#id_fee");
const assignForm = $("#assign-form");

function changedSelectBox() {
    const selectedFeature = parseInt(featureTypeSelectBox.val());

    if (isNaN(selectedFeature)) {
        $("input", assignForm).each(function () {
            $(this).closest(".form-group").show();
        });
        feeField.val("");
        return;
    }

    Object.entries(features[selectedFeature].fields_visibility).forEach(([key, value]) => {
        const inputDivFormGroup = $(`input[name=${key}]`, assignForm).closest(".form-group");
        value ? inputDivFormGroup.show() : inputDivFormGroup.hide();
    });

    feeField.val(features[selectedFeature].fee);
}

$(function () {
    changedSelectBox();
    featureTypeSelectBox.change(changedSelectBox);
});
