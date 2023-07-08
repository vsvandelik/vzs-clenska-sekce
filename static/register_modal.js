function register_modal(id) {
    $(`#${id}`).on('show.bs.modal', function (event) {
        var action = $(event.relatedTarget).data('action');
        var modal = $(`#${id}Dialog`);

        console.log(action)

        fetch(action)
            .then((response) => {
                return response.text();
            })
            .then((modal_html) => {
                modal.html(modal_html);
            });
    })
}
