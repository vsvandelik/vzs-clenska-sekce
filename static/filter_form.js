function registerFilterForm(formID, leaveOpen = false) {
    const filterForm = $("#" + formID);
    const filterFormToggler = $("#filter-toggler");

    $(function () {
        filterFormToggler.on('click', function () {
            $("i", this).each(function () {
                $(this).toggle();
            });
            filterForm.toggle();
        });
    })
}