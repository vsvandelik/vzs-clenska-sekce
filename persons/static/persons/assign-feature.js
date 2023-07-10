const featureTypeSelectBox = $("#id_feature");
const tierField = $("#id_tier");
const assignForm = $("#assign-form");

function changedSelectBox() {
    const selectedFeature = parseInt(featureTypeSelectBox.val());

    if (isNaN(selectedFeature)) {
        $("input", assignForm).each(function () {
            $(this).parent().parent().show();
        });
        tierField.val("");
        return;
    }

    Object.entries(features[selectedFeature].fields_visibility).forEach(([key, value]) => {
        const inputDivFormGroup = $(`input[name=${key}]`, assignForm).parent().parent();
        value ? inputDivFormGroup.show() : inputDivFormGroup.hide();
    });

    tierField.val(features[selectedFeature].tier);
}

$(function () {
    changedSelectBox();
    featureTypeSelectBox.change(changedSelectBox);
});