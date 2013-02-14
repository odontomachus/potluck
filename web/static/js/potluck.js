potluck = {
    scrolled: false,
}

$(function () {
    $('#potluck').animate({
	top: '+=980',
    }, 2200);
    $('#scroll').delay(1600).animate({
	bottom: '+=80',
    }, 1100, 'easeOutElastic');
});

function isScrolledIntoView(elem)
{
    var docViewTop = $(window).scrollTop();
    var docViewBottom = docViewTop + $(window).height();

    var elemTop = $(elem).offset().top;
    var elemBottom = elemTop + $(elem).height();

    return elemBottom <= docViewBottom;
}

$(window).scroll(function() {
    if (!potluck.scrolled && isScrolledIntoView($('#cicero'))) {
	potluck.scrolled = true;
	$('#cicero img').animate({
	    height: '0px',
	    width: '+=0',
	    }, 1500);
	$('body').animate({
	    scrollTop: 0
	},1600);
	$('div.wrapper').css('height', 'auto');
		    
	$('#potluck').delay(100)
	    .animate({
		top: '0px',
	    }, 1500)
	    .css('position', 'relative');
    };
});

$('div.responses .tabs li').click( function() {
    if ($(this).hasClass('selected')) return;

    var cClass = $(this).attr('class').split('/\s/')[0];
    $(this).siblings('.selected').removeClass('selected');
    $(this).addClass('selected');
    $('div.attendance .selected').removeClass('selected').hide();
    $('div.attendance .' + cClass).addClass('selected').show();
});

$('div.response div.confirm a').click( function() {
    if ($(this).hasClass('selected')) return false;

    if ($(this).hasClass('yes')) {
	$('div.food').removeClass('hidden');
    }
    else {
	$('div.food').addClass('hidden');
    };

    var cClass = $(this).attr('class');
    $('div.response .selected').removeClass('selected');
    $(this).addClass('selected');
    $('div.response input#response').attr('value', cClass.trim());
    $.post('', $('form#food_form').serialize());

    return false;
});

$('a.location').hover(function() {
    $('div.contact').show();
}, function() {
    $('div.contact').hide();
});
