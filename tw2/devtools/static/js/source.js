function showWidgetSource(name) {
        var selector = ('#' + name + '-widget-source').replace(/\./g, '\\.');
        $(selector).show();
        $(selector).dialog({
                'title': 'Demo Source Code:  "' + name + '"',
                'width': '66%',
        });
}

$(document).ready( function () {
        // Hide all the widget source things from the get-go
        $("div[id$='-widget-source']").hide();
});
