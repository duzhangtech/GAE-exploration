$(document).ready(function(){
    
    
//ENTRY FORMATTING
var cost = document.getElementsByClassName('cost'); 
var price = document.getElementsByClassName('price');
    
for (var ii = 0; ii < cost.length; ii++) { 
    $(cost[ii]).text(parseFloat($(cost[ii]).text()).toFixed(1));
    $(price[ii]).text(parseFloat($(price[ii]).text()).toFixed(2));
}
    
    
//FEEDBACK
$("#submit").click(function() {
    var feedback = $("#feedback").val();
    var name = $("#name").val();
    var email = $("#email").val();
    
    if (feedback.length == 0) {
        $("#error").show();
    } else {
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
   
    
//BORDER BOTTOM ON HOVER
$(".navlinks").on({
    mouseenter: function () {
        $(this).css("border-bottom", "3px solid #11b99c");
    },
    mouseleave: function () {
        $(this).css("border-bottom", "0px");
    }
});
    
    
//SHOW SORT HINT
$(".sort").on({
    mouseenter: function () {
        $('#derp').fadeIn();
    },
    mouseleave: function () {
        $('#derp').fadeOut();
    }
});
  
    
//SORT BY MP
$('#sortmp').on('click', function () {
    $('.entrylink').sort(function(a, b) {return $(a).find('span.amount').text() - $(b).find('span.amount').text();}) 
    .appendTo('#entrytable');
});
    
    
//SORT BY $
$('#sortcost').on('click', function () {
    $('.entrylink').sort(function(a, b) {return $(a).find('span.cost').text() - $(b).find('span.cost').text();}) 
    .appendTo('#entrytable');
});
      
    
//SORT BY $/MP
$('#sortprice').on('click', function () {
    $('.entrylink').sort(function(a, b) {return $(a).find('span.price').text() - $(b).find('span.price').text();})
    .appendTo('#entrytable');
});
  
    

});