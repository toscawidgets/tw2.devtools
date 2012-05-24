function toggleDocs(id) {
    var docdiv = $('div[id=' + id + '-doc]');
    var link = docdiv.parent().parent().parent().parent().prev();
    if ( link.text() == 'Show Documentation' ) {
        link.text('Hide Documentation');
    } else {
        link.text('Show Documentation');
    }
    docdiv.slideToggle('slow');

}
$(document).ready(function() {
    $('div[id$=-doc]').hide();
});
