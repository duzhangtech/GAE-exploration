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
});    
   
    
$(".navlinks").on({
    mouseenter: function () {
        $(this).css("border-bottom", "3px solid #11b99c");
    },
    mouseleave: function () {
        $(this).css("border-bottom", "0px");
    }
});
    

        
});