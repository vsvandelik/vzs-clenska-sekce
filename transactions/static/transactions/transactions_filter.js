const filterForm = $("#transactions-filter-form");
const filterFormToggler = $("#filter-toggler");

$(function () {
    $('i[data-status="open"]', filterFormToggler).hide();
    filterForm.hide();
    filterFormToggler.on('click', function () {
        $("i", this).each(function () {
            $(this).toggle();
        });
        filterForm.toggle();
    });
})
