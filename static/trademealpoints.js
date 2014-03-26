$(document).ready(function(){
    
    
//FEEDBACK
$("#submit").click(function() {
    var feedback = $("#feedback").val();
    var name = $("#name").val();
    var email = $("#email").val();
    
    if (feedback.length == 0) {
        $("#error").show();
    }
    
    else {
    $.ajax({
        type: "POST",
        url: "/faq",
        data: 'feedback=' + feedback + "&name=" + name + "&email=" + email,
        success: function() {
        
        $("#feedback_title").replaceWith("<div id = 'feedback_title' style = 'font-size:24px;color: #32ac97;margin-bottom:200px;margin-top:5px;'>THANKS!</div>");
        $("#feedback").remove();
        $("#error").remove();
        $("#name").remove();
        $("#email").remove();
        $("#submit").remove();
    ;}
    });
    }
    return false;
});    
    
    
//EDIT OFFER
$('#edit_button').on('click', function() {
    var fill = true;
    $('.edit').each(function() {
        if ($(this).length == 0) {
            fill = false;
        }
    });
    
    if (fill == true) {
        $('#deletestat').text('');
        $('#editstat').text('Your offers have been updated!');
    } 
    else if (fill == false) {
        $('#deletestat').text('');
        $('#editstat').text('Fill each box');
    }
});
        
        
//DELETE OFFER
$('#delete_button').on('click', function() {
    var fill = true;
    $('.delete').each(function() {
        if ($(this).length == 0) {
            fill = false;
        }
    });
    
    if (fill == true) {
        var match = false;
        
        var amount = $('.deleteamount').val();
        var price = $('.deleteprice').val();
        
        var offers = document.getElementsByClassName('edit').split(/\s+/);
        for (var i = 0; i < classList.length; i+2) {
            if (offers[i] == amount && offers[i+1] == price) {
                match = true;
                offers[i].remove();
                offers[i+1].remove();
            }
        }
        
        if (match = false) {
            $('#editstat').text('');
            $('#deletestat').text("You don't have that offer on the fase");
        }
        else if (match == true) {
            $('#editstat').text('');
            $('#deletestat').text("Well, there's a goner.");
        }
    } 
    else if (fill == false) {
        $('#editstat').text('');
        $('#deletestat').text('Fill each box');
    }
});
    
        
        
});