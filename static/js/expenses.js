$('#new-backup-btn').click(function () {
    $('.data-filter-body').show();
});

$('#close-filters-btn').click(function () {
    $('.data-filter-body').hide();
    //Clear all the existing filters on close
    $('#id_name').val('');
    $('#id_state').val('default');
    $('#id_state').selectpicker('refresh');    
    $('#id_fund_source').val('default');
    $('#id_fund_source').selectpicker('refresh');    
    $('#id_reimbursable').val('default');
    $('#id_reimbursable').selectpicker('refresh');
    $('#id_approved_at_gte').val(null);
    $('#id_approved_at_lte').val(null);
    $('#id_updated_at_gte').val(null);
    $('#id_updated_at_lte').val(null);
    $('#id_reimbursed_at_gte').val(null);
    $('#id_reimbursed_at_lte').val(null);
    $('#id_spent_at_gte').val(null);
    $('#id_spent_at_lte').val(null);
});

$(function () {
    //Linked dates for approved_at filter
    $('#id_approved_at_gte').datetimepicker();
    $('#id_approved_at_lte').datetimepicker({
        useCurrent: false
    });
    $('#id_approved_at_gte').on('change.datetimepicker', function (e) {
        $('#id_approved_at_lte').datetimepicker('minDate', e.date);
    });
    $('#id_approved_at_lte').on('change.datetimepicker', function (e) {
        $('#id_approved_at_gte').datetimepicker('maxDate', e.date);
    });

    //Linked dates for updated at filter
    $('#id_updated_at_gte').datetimepicker();
    $('#id_updated_at_lte').datetimepicker({
        useCurrent: false
    });
    $('#id_updated_at_gte').on('change.datetimepicker', function (e) {
        $('#id_updated_at_lte').datetimepicker('minDate', e.date);
    });
    $('#id_updated_at_lte').on('change.datetimepicker', function (e) {
        $('#id_updated_at_gte').datetimepicker('maxDate', e.date);
    });

    //Linked dates for reimbursed at filter
    $('#id_reimbursed_at_gte').datetimepicker();
    $('#id_reimbursed_at_lte').datetimepicker({
        useCurrent: false
    });
    $('#id_reimbursed_at_gte').on('change.datetimepicker', function (e) {
        $('#id_reimbursed_at_lte').datetimepicker('minDate', e.date);
    });
    $('#id_reimbursed_at_lte').on('change.datetimepicker', function (e) {
        $('#id_reimbursed_at_gte').datetimepicker('maxDate', e.date);
    });

    //Linked dates for spent at filter
    $('#id_spent_at_gte').datetimepicker();
    $('#id_spent_at_lte').datetimepicker({
        useCurrent: false
    });
    $('#id_spent_at_gte').on('change.datetimepicker', function (e) {
        $('#id_spent_at_lte').datetimepicker('minDate', e.date);
    });
    $('#id_spent_at_lte').on('change.datetimepicker', function (e) {
        $('#id_spent_at_gte').datetimepicker('maxDate', e.date);
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
        $('.approved_at').show()
    } else {
        $('.approved_at').hide();
        $('#id_approved_at_gte').val(null);
        $('#id_approved_at_lte').val(null);
    }
});

// Auto-refresh on minimum one task with IN PROGRESS state
function refreshBackupList(){
    $.ajax({
        method: 'GET',
        url: '/main/backups/list/',
        success: function(data) {
            $('#backup-list-table tbody').empty();
            data = data['backups']
            $.each(data, function (key, expense) {
                var id = expense.id;
                var name = expense.name;
                var created_at = (expense.created_at).substr(0, 10);
                var current_state = expense.current_state;
                var email_icon = '';
                if (current_state == 'IN PROGRESS')
                    document.getElementById('in_progress_count')
                if (current_state == 'READY')
                    email_icon = '<a href="/main/backups/notify/'+ id +'" title="Resend Backup Email"><i class="fa fa-envelope"></i></a>';
                $('#backup-list-table tbody').append(
                   '<tr class="expenses-table-row"><td>' + name + '</td><td>' + created_at + '</td><td>' + current_state + '</td><td>' + email_icon + '</td></tr>'
                )
            })
            let inProgressList = data.filter(expense => expense.current_state == 'IN PROGRESS');
            if (inProgressList.length > 0)
                setTimeout(function(){refreshBackupList();}, 2000);
        },
        error: function(data) {
            console.log('Error refreshing backups list')
            console.log(data)
        }
    });
}

$(document).ready (function(){
    refreshBackupList();
    window.setInterval(function () { 
        $('.alert').alert('close'); 
    }, 2000); 
}); 

