function registerFilterForm(formID, leaveOpen = false) {
    const filterForm = $("#" + formID);
    const filterFormToggler = $("#filter-toggler");

    $(function () {
        if (!leaveOpen) {
            $('i[data-status="open"]', filterFormToggler).hide();
            filterForm.hide();
        } else {
            $('i[data-status="closed"]', filterFormToggler).hide();
        }

        filterFormToggler.on('click', function () {
            $("i", this).each(function () {
                $(this).toggle();
            });
            filterForm.toggle();
        });
    })
}