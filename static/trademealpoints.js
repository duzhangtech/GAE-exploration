$(document).ready(function(){
    
    
//ENTRY FORMATTING FOR PRE PY REGEX POSTS
var cost = document.getElementsByClassName('cost'); 
var price = document.getElementsByClassName('price');
    
for (var ii = 0; ii < price.length; ii++) { 
    $(cost[ii]).text(parseFloat($(cost[ii]).text()).toFixed(1));
    $(price[ii]).text(parseFloat($(price[ii]).text()).toFixed(2));
    $(price[ii]).val(parseFloat($(price[ii]).val()).toFixed(2));
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
            url: "/submitfeed",
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
        
var clicked = false;

$("#sortmp").mouseenter(function () {
    if ($("#sortmp span div.triangle").hasClass('ascendwhite')) {
        $("#sortmp span div.triangle").removeClass('ascendwhite');
    }
    else if ($("#sortcost span div.triangle").hasClass('ascend'))  { //if low to high/ascending
        $("#sortmp span div.triangle").removeClass('ascend ascendblue').addClass('descend descendblue');
    } 
    else if ($("#sortcost span div.triangle").hasClass('descend')) {
        $("#sortmp span div.triangle").removeClass('descend descendblue').addClass('ascend ascendblue');
    }
});
$("#sortmp").mouseleave( function () {
    if (clicked) {
        clicked = false; 
        return;
    }
    if ($('#sortmp').attr("current") == 'false') {
        $("#sortmp span div.triangle").addClass('ascendwhite');
    }
    else if ($("#sortmp span div.triangle").hasClass('descend'))  {
        $("#sortmp span div.triangle").removeClass('descend descendblue').addClass('ascend');
    } 
    else if ($("#sortmp span div.triangle").hasClass('ascend')) {
        $("#sortmp span div.triangle").removeClass('ascend ascendblue').addClass('descend');
    }
}); 
//SORT BY MP
$('#sortmp').on('click', function () {
    clicked = true;
    $('#sortmp').attr("current", "true");
    $('.theader a').not($('#sortmp')).attr("current", "false");
    
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
   
    
$("#sortcost").mouseenter(function () {
    if ($("#sortcost span div.triangle").hasClass('ascendwhite')) {
        $("#sortcost span div.triangle").removeClass('ascendwhite');
    }
    else if ($("#sortcost span div.triangle").hasClass('ascend'))  { //if low to high/ascending
        $("#sortcost span div.triangle").removeClass('ascend ascendblue').addClass('descend descendblue');
    } 
    else if ($("#sortcost span div.triangle").hasClass('descend')) {
        $("#sortcost span div.triangle").removeClass('descend descendblue').addClass('ascend ascendblue');
    }
});
$("#sortcost").mouseleave( function () {
    if (clicked) {
        clicked = false; 
        return;
    }
    if ($('#sortcost').attr("current") == 'false') {
        $("#sortcost span div.triangle").addClass('ascendwhite');
    }
    else if ($("#sortcost span div.triangle").hasClass('descend'))  {
        $("#sortcost span div.triangle").removeClass('descend descendblue').addClass('ascend');
    } 
    else if ($("#sortprice span div.triangle").hasClass('ascend')) {
        $("#sortcost span div.triangle").removeClass('ascend ascendblue').addClass('descend');
    }
}); 
$('#sortcost').click(function () {
    clicked = true;
    $('#sortcost').attr("current", "true");
    $('.theader a').not($('#sortcost')).attr("current", "false");  
    $('.theader a').not($('#sortcost')).children('span.triangle').addClass('ascendwhite');

    var stat = $('#sortcost').attr("data");
    
    if (stat == "normalsorted")  {
        $('#sortcost').attr("data", "reversesorted");
        $('.entrylink').sort(function(a, b) {
            return $(b).find('span.cost').text() - $(a).find('span.cost').text();
        }).appendTo('#entrytable');    
        $("#sortcost span div.triangle").addClass('descend').removeClass('ascend descendblue');
    } 
    else if (stat == "reversesorted"  || typeof stat == "undefined") {
        $('#sortcost').attr("data", "normalsorted");
        $('.entrylink').sort(function(a, b) {
            return $(a).find('span.cost').text() - $(b).find('span.cost').text();
        }).appendTo('#entrytable');   
        $("#sortprice span div.triangle").addClass('ascend').removeClass('descend ascendblue');
    }
});
      
   
//SORT PRICE TRIANGLE
$("#sortprice").mouseenter(function () {
    if ($("#sortprice span div.triangle").hasClass('ascendwhite')) {
        $("#sortprice span div.triangle").removeClass('ascendwhite');
    }
    else if ($("#sortprice span div.triangle").hasClass('ascend'))  { //if low to high/ascending
            $("#sortprice span div.triangle").removeClass('ascend ascendblue').addClass('descend descendblue');
    } 
    else if ($("#sortprice span div.triangle").hasClass('descend')) {
        $("#sortprice span div.triangle").removeClass('descend descendblue').addClass('ascend ascendblue');
    }
});
    
$("#sortprice").mouseleave( function () { 
    if (clicked) {
        clicked = false; 
        return;
    }
    if ($('#sortprice').attr("current") == 'false') {
        $("#sortprice span div.triangle").addClass('ascendwhite');
    }
    else if ($("#sortprice span div.triangle").hasClass('descend'))  {
        $("#sortprice span div.triangle").removeClass('descend descendblue').addClass('ascend');
    } 
    else if ($("#sortprice span div.triangle").hasClass('ascend')) {
        $("#sortprice span div.triangle").removeClass('ascend ascendblue').addClass('descend');
    }
});
    
$('#sortprice').click(function () {
    clicked = true;
    $('#sortprice').attr("current", "true");
    $('.theader a').not($('#sortprice')).attr("current", "false");
    $('.theader a').not($('#sortprice')).children('span.triangle').addClass('ascendwhite');
    
    var stat = $('#sortprice').attr("data");
    
    if (stat == "normalsorted")  {
        $('#sortprice').attr("data", "reversesorted");
        $('.entrylink').sort(function(a, b) {
            return $(b).find('span.price').text() - $(a).find('span.price').text();
        }).appendTo('#entrytable'); 
        $("#sortprice span div.triangle").addClass('descend').removeClass('ascend descendblue');
    } 
    else {
        $('#sortprice').attr("data", "normalsorted");
        $('.entrylink').sort(function(a, b) {
            return $(a).find('span.price').text() - $(b).find('span.price').text();
        }).appendTo('#entrytable');    
        $("#sortprice span div.triangle").addClass('ascend').removeClass('descend ascendblue');
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
    $("#priceinput").attr('placeholder', '$0.01 to $1');
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