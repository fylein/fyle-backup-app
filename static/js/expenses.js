$("#new-backup-btn").click(function () {
    $(".data-filter-body").show();
});

$("#close-filters-btn").click(function () {
    $(".data-filter-body").hide();
    //Clear all the existing filters on close
    $("#id_name").val('');
    $("#id_state").val('default');
    $('#id_state').selectpicker('refresh');
    $('#id_approved_at_gte').val(null);
    $('#id_approved_at_lte').val(null);
    $('#id_updated_at_gte').val(null);
    $('#id_updated_at_lte').val(null);
});

$(function () {
    //Linked dates for approved_at filter
    $('#id_approved_at_gte').datetimepicker();
    $('#id_approved_at_lte').datetimepicker({
        useCurrent: false
    });
    $("#id_approved_at_gte").on("change.datetimepicker", function (e) {
        $('#id_approved_at_lte').datetimepicker('minDate', e.date);
    });
    $("#id_approved_at_lte").on("change.datetimepicker", function (e) {
        $('#id_approved_at_gte').datetimepicker('maxDate', e.date);
    });

    //Linked dates for updated at filter
    $('#id_updated_at_gte').datetimepicker();
    $('#id_updated_at_lte').datetimepicker({
        useCurrent: false
    });
    $("#id_updated_at_gte").on("change.datetimepicker", function (e) {
        $('#id_updated_at_lte').datetimepicker('minDate', e.date);
    });
    $("#id_updated_at_lte").on("change.datetimepicker", function (e) {
        $('#id_updated_at_gte').datetimepicker('maxDate', e.date);
    });
});
toastr.info('Are you the 6 fingered man?')