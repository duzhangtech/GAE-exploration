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
    var stat = $('#sortmp').attr("data");

    if (stat == "normalsorted")  {
        $('#sortmp').attr("data", "reversesorted");
        
        $('.entrylink').sort(function(a, b) {
            return $(b).find('span.amount').text() - $(a).find('span.amount').text();
        }).appendTo('#entrytable');    
    } 
    
    else if (stat == "reversesorted" || typeof stat == "undefined") {
        $('#sortmp').attr("data", "normalsorted");
        
        $('.entrylink').sort(function(a, b) {
            return $(a).find('span.amount').text() - $(b).find('span.amount').text();
        }).appendTo('#entrytable');    
    }
    
});
    
    
//SORT BY $
$('#sortcost').on('click', function () {
    var stat = $('#sortcost').attr("data");
    
    if (stat == "normalsorted")  {
        $('#sortcost').attr("data", "reversesorted");
        
        $('.entrylink').sort(function(a, b) {
            return $(b).find('span.cost').text() - $(a).find('span.cost').text();
        }).appendTo('#entrytable');    
    } 
    
    else if (stat == "reversesorted"  || typeof stat == "undefined") {
        $('#sortcost').attr("data", "normalsorted");
        
        $('.entrylink').sort(function(a, b) {
            return $(a).find('span.cost').text() - $(b).find('span.cost').text();
        }).appendTo('#entrytable');    
    }
});
      
    
//SORT BY $/MP
$('#sortprice').on('click', function () {
    var stat = $('#sortprice').attr("data");
    
    if (stat == "normalsorted")  {
        $('#sortprice').attr("data", "reversesorted");
        
        $('.entrylink').sort(function(a, b) {
            return $(b).find('span.price').text() - $(a).find('span.price').text();
        }).appendTo('#entrytable');    
    } 
    
    else if (stat == "reversesorted"  || typeof stat == "undefined") {
        $('#sortprice').attr("data", "normalsorted");
        
        $('.entrylink').sort(function(a, b) {
            return $(a).find('span.price').text() - $(b).find('span.price').text();
        }).appendTo('#entrytable');    
    }
});
  
  
//AMOUNT HINT
$("#amountinput").focus(function() {
    $("#amountinput").attr('placeholder', '150 to 2000 mp');
});
    
$("#amountinput").blur(function() {
    $("#amountinput").attr('placeholder', 'number of mp');
});
   
//PRICE HINT
$("#priceinput").focus(function() {
    $("#priceinput").attr('placeholder', '$0.01 to $1/mp');
});
    
$("#priceinput").blur(function() {
    $("#priceinput").attr('placeholder', 'price per mp');
});
    

//AMOUNT REGEX
function okayamount(amount) {
    
}
    
//PRICE REGEX
function okayamount(amount) {
    
}
    
//EMAIL REGEX
function okayamount(amount) {
    
}
    
//AMOUNT OKAY
$("#amountinput").keyup(function() {
    var amount = $("#amountinput").val();
    
    if (okayamount(amount)) {
        //show okay message
    } else {
        //boo
    }
});
    
//PRICE OKAY
$("#amountinput").keyup(function() {
    var amount = $("#amountinput").val();
    
    if (okayamount(amount)) {
        //show okay message
    } else {
        //boo
    }
});
    
//EMAIL OKAY
$("#amountinput").keyup(function() {
    var amount = $("#amountinput").val();
    
    if (okayamount(amount)) {
        //show okay message
    } else {
        //boo
    }
});


});