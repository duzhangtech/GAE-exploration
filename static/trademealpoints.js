$(document).ready(function(){
    
//SELL
$('#sell-link').click(function () {
    $('#buy').slideUp();
    $('#sell').show();
});
    
//FEEDBACK
$("#submit").click(function() {
    var feedback = $("#feedback").val();
    var name = $("#name").val();
    var email = $("#email").val();
    
    if (feedback.length == 0) {
        $("#error").remove();
        $("#feed").append("<div id = 'error' style = 'height:50px;'>What do you think about this app?</div>");
    }
    
    else {
    $.ajax({
        type: "POST",
        url: "/faq",
        data: 'feedback=' + feedback + "&name=" + name + "&email=" + email,
        success: function() {
        
        $("#feedback_title").replaceWith("<div id = 'feedback_title' style = 'font-size:24px;color: #32ac97;margin-bottom:25px;margin-top:5px;'>THANKS!</div>");
        $("#feedback").remove();
        $("#name").remove();
        $("#email").remove();
        $("#submit").remove();
        $("#error").remove();
     }
    });
    }
    return false;
});
     
     
});