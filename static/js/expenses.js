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

// Show approved_at field only for valid states
$('#id_state').on('changed.bs.select', function (e, clickedIndex, newValue, oldValue) {
    var selected_list = $(e.currentTarget).val();
    var show_approved_at_for_states = ['APPROVED', 'PAYMENT_PENDING', 'PAYMENT_PROCESSING', 'PAID'];
    var show = false;
    // If no state is selected
    show = selected_list.length == 0 ? true : false;

    for(var i=0; i<selected_list.length; i++){
        if(show_approved_at_for_states.indexOf(selected_list[i]) > -1 ){
            show = true;
            break;
        }
    }
    if(show){
        $(".approved_at").show()
    } else {
        $(".approved_at").hide();
        $('#id_approved_at_gte').val(null);
        $('#id_approved_at_lte').val(null);
    }
});

$('#id_state option').prop('selected', true);
$(document).ready (function(){
    window.setInterval(function () { 
        $(".alert").alert('close'); 
    }, 2000); 
});