
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
	    
	$('#potluck').delay(100)
	    .animate({
		top: '0px',
	    }, 1500)
	    .css('position', 'relative');
    };
});
