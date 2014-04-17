$(document).ready(function(){
    
(function(a){(jQuery.browser=jQuery.browser||{}).mobile=/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows (ce|phone)|xda|xiino/i.test(a)||/1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0,4))})(navigator.userAgent||navigator.vendor||window.opera);

if (jQuery.browser.mobile) {
    $('body').css({ "min-width": "" });
} else {
    $('body').css({"min-width": "370px" });
}
  
    
//if(document.URL == 'http://trademealpoints.appspot.com/' || document.URL == 'http://trademealpoints.appspot.com/buy') {
if(document.URL == 'http://localhost:10080/buy' || document.URL == 'http://localhost:10080/') {
    $('.navlinks, .current_link').addClass('animated slideInLeft');
    $('#front-title, .center').hide();
    setTimeout(function() {
        $('#front-title, .center').show();
        $('#front-title').addClass('animated bounceInDown');
        $('.center').addClass('animated fadeInUp');
    }, 200);
} 
    
//if(document.URL == 'http://trademealpoints.appspot.com/getkarma') {
if(document.URL == 'http://localhost:10080/getkarma') {
    $('body').css('paddingLeft', '0px').css('paddingRight', '0px');
    $('.coolinput').val("10");
    $('.coolinput').focus();
}   
    
    
$('.deletebutton').click(function() {
    var url = document.URL;
    var email = url.substring(url.indexOf('e=')+2, url.indexOf('&v='));
    var amount = $(this).parent().children('.myamount').val();
    var price = $(this).parent().children('.myprice').val();
    console.log(email);
    console.log(amount);
    console.log(price);
    $.ajax({
        type: "POST",
        url: "/delete",
        data: 'email=' + email + "&amount=" + amount + "&price=" + price,
        success: function() {
            location.reload();
        ;}
    });
    
});

    
if (document.URL.indexOf('/change?') != -1) {
    $(".myamount").focus();
}
    
    
$(".coolinput").css("width", "30px"); 
//EXPAND INPUT BOX IF CHAR > 2
$(".coolinput").keyup(function() {
    var amount = $(".coolinput").val();
    if (amount.length > 0) {
        $(".coolinput").css("width", 15*amount.length + "px");
    } else {
        $(".coolinput").css("width", "15px");
    }
});
    
    
//MIN $1
$("input[type=text].coolinput").blur(function() {
    var amount = $(this).val();
    if (amount.length == 0) {
        $(this).val("1");
    }
});
    
function respond() {
    if ($(window).width() > 450) {
        $('#expirepic').removeClass('hide');
        $('#mmpic, #yypic').addClass('hide');
        $('#paymonth').attr('placeholder', 'MM');
        $('#payyear').attr('placeholder', 'YY');
    } else {
        $('#expirepic').addClass('hide');
        $('#mmpic, #yypic').removeClass('hide');
        $('#paymonth').attr('placeholder', 'Expiration month');
        $('#payyear').attr('placeholder', 'Expiration year');
    }
}
respond();
    
$(window).resize(function() {
   respond();
});

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
            
            $("#feedback_title").replaceWith("<div id = 'feedback_title' style = 'font-size:24px;color: #4cb8ca;margin-bottom:200px;margin-top:5px;'>THANKS!</div>");
            $("#feedback, #error, #submit").remove();
            ;}
        });
    }
});    
   
    
//BORDER BOTTOM ON HOVER
$(".navlinks").on({
    mouseenter: function () {
        $(this).css("border-bottom", "3px solid #4cb8ca");
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
    else if ($("#sortmp span div.triangle").hasClass('ascend'))  { //if low to high/ascending
        $("#sortmp span div.triangle").removeClass('ascend ascendblue').addClass('descend descendblue');
    } 
    else if ($("#sortmp span div.triangle").hasClass('descend')) {
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
    $('#sortcost span div.triangle, #sortprice span div.triangle').addClass('ascend ascendwhite').removeClass('descend');

    var stat = $('#sortmp').attr("data");

    if (stat == "normalsorted")  {
        $('#sortmp').attr("data", "reversesorted");
        $('.entrylink').sort(function(a, b) {
            return $(b).find('span.amount').text() - $(a).find('span.amount').text();
        }).appendTo('#entrytable');
        $("#sortmp span div.triangle").addClass('descend').removeClass('ascend descendblue');
    } 
    
    else if (stat == "reversesorted" || typeof stat == "undefined") {
        $('#sortmp').attr("data", "normalsorted");
        $('.entrylink').sort(function(a, b) {
            return $(a).find('span.amount').text() - $(b).find('span.amount').text();
        }).appendTo('#entrytable');  
        $("#sortmp span div.triangle").addClass('ascend').removeClass('descend ascendblue');
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
    else if ($("#sortcost span div.triangle").hasClass('ascend')) {
        $("#sortcost span div.triangle").removeClass('ascend ascendblue').addClass('descend');
    }
}); 
$('#sortcost').click(function () {
    clicked = true;
    $('#sortcost').attr("current", "true");
    $('.theader a').not($('#sortcost')).attr("current", "false");  
    $('#sortmp span div.triangle, #sortprice span div.triangle').addClass('ascend ascendwhite').removeClass('descend');
    
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
        $("#sortcost span div.triangle").addClass('ascend').removeClass('descend ascendblue');
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
    else if ($("#sortprice span div.triangle").hasClass('descend'))  { //normal up
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
    $('#sortmp span div.triangle, #sortcost span div.triangle').addClass('ascend ascendwhite').removeClass('descend');
    
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
    $("#priceinput").attr('placeholder', '0.01 to 1');
});
    
$("#priceinput").blur(function() {
    $("#priceinput").attr('placeholder', 'price per mp');
});


});