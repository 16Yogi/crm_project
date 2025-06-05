$(document).ready(function () {
    var rowsPerPage = 4;
    var rows = $('#dataTable tbody tr');
    var rowsCount = rows.length;
    var pageCount = Math.ceil(rowsCount / rowsPerPage);
    var pagination = $('#pagination');

    // Generate pagination buttons
    for (var i = 1; i <= pageCount; i++) {
        pagination.append('<li class="page-item"><a class="page-link" href="#">' + i + '</a></li>');
    }

    // Show first page rows initially
    rows.hide();
    rows.slice(0, rowsPerPage).show();

    // Pagination click
    pagination.find('a').click(function (e) {
        e.preventDefault();
        var pageIndex = $(this).text() - 1;
        var start = pageIndex * rowsPerPage;
        var end = start + rowsPerPage;

        rows.hide().slice(start, end).show();

        $('.page-item').removeClass('active');
        $(this).parent().addClass('active');
    });

    // Activate first page
    pagination.find('li:first').addClass('active');
});
