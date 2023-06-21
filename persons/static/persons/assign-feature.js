const featureTypeSelectBox = $("#id_feature");
const assignForm = $("#assign-form");

function changedSelectBox() {
  const selectedFeature = parseInt(featureTypeSelectBox.val());

  if (isNaN(selectedFeature)) {
    $("input", assignForm).each(function () {
      $(this).parent().parent().show();
    });
    return;
  }

  Object.entries(features[selectedFeature]).forEach(([key, value]) => {
    const inputDivFormGroup = $(`input[name=${key}]`, assignForm).parent().parent();
    value ? inputDivFormGroup.show() : inputDivFormGroup.hide();
  });
}

$(function () {
  changedSelectBox();
  featureTypeSelectBox.change(changedSelectBox);
});