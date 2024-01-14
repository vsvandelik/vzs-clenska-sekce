const selectedPersonsListUI = $("#selected-persons");
const selectedPersonsListArray = [];

function selectPerson(e) {
    const button = $(e.target);
    const tr = button.parent().parent();
    const personPK = parseInt(button.val());
    const personName = button.parent().prev().prev().text();

    if (!selectedPersonsListArray.includes(personPK)) {
        selectedPersonsListArray.push(personPK);
        selectedPersonsListUI.append(
            `<li class="d-block bg-info p-1 m-1 rounded float-left">${personName}<input type="hidden" name="members" value="${personPK}"/></li>`
        );
        tr.remove();
    }
}

$(function () {
    $("#persons-list button").click(selectPerson);
});
