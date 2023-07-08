$('#deletePersonModal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget)
    var first_name = button.data('first-name')
    var last_name = button.data('last-name')
    var action = button.data('action')

    $("#deletePersonForm").attr("action", action)
    $("#deletePersonModalBody").text(`Opravdu chcete smazat osobu ${first_name} ${last_name}?`)
})
