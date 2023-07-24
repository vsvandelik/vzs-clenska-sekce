function registerModal(id) {
    $(`#${id}`).on('show.bs.modal', function (event) {
        var action = $(event.relatedTarget).data('action');
        var modal = $(`#${id}Dialog`);

        fetch(action)
            .then((response) => {
                return response.text();
            })
            .then((modal_html) => {
                modal.html(modal_html);
            });
    })
}
