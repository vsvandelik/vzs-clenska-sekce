let selected_persons_list = $("#selected-persons");
let list_of_selected_persons = [];

function select_person(e) {
    let button = $(e.target);
    let tr = button.parent().parent();
    let person_pk = parseInt(button.val());
    let person_name = button.parent().prev().text();

    if (!list_of_selected_persons.includes(person_pk)) {
        list_of_selected_persons.push(person_pk);
        selected_persons_list.append(`<li>${person_name}<input type="hidden" name="members" value="${person_pk}"/></li>`);
        tr.remove();
    }
}

$(function () {
    $("#persons-list button").click(select_person);
});