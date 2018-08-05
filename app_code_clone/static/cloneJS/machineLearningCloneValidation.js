$(document).ready(function(){




//====================== CLONE VALIDATION========================
//selecting the clone file for validation
$("#selectCloneFile").on('change', function () {
    //alert($(this).val());



    var theUser = $("#user_id").text();
	var theCloneFile = $("#selectCloneFile").val();

    $.ajax({
        type: "POST",
        cache: false,
        url: "/srv_get_next_clone_pair_for_validation",
        data: 'theUser=' + theUser + '&theCloneFile='+theCloneFile,
        dataType:'json',
        success: function (option) {
            //alert(option.fragment1);
            //$("#txl_log").html(option.fragment1);
            //$("#txl_output").html(option.fragment2);
            $('#fragment_1_path').text(option.fragment_1_path);
            $('#fragment_1_start').text(option.fragment_1_startline);
            $('#fragment_1_end').text(option.fragment_1_endline);
            var_txl_log.getSession().setValue(option.fragment_1_clone);


            $('#fragment_2_path').text(option.fragment_2_path);
            $('#fragment_2_start').text(option.fragment_2_startline);
            $('#fragment_2_end').text(option.fragment_2_endline);
            var_txl_output.getSession().setValue(option.fragment_2_clone);


            var num_clones_validated = parseInt(option.clones_validated);
            var total_clones = parseInt(option.total_clones);
            $("#validation_percentage").text( ''+(num_clones_validated*100 / total_clones).toPrecision(2) );

            $("#num_validated_clones").text(option.clones_validated);
            $("#total_clones").text(option.total_clones);


        },
        error: function (xhr, status, error) {
            //on error, alert the possible error (system error)
            alert(xhr.responseText);

        }

        });




});




$("#autoValidate").on('click', function(){
    alert("starting auto validation....");

});






$("#upload_clone_files").on('click', function(){
        var form_data = new FormData($('#upload-file')[0]);

        //append some non-form data also
        form_data.append('userID',$('#user_id').text());
        $.ajax({
            type: 'POST',
            url: '/upload_new_clone_file',
            data: form_data,
            contentType: false,
            cache: false,
            processData: false,
            async: false,
            success: function(data) {
                //console.log('Success!');
                alert("Clone File Upload Success");
            },
            error: function (xhr, status, error) {
                //on error, alert the possible error (system error)
                alert(xhr.responseText);

        }


        });

});







});