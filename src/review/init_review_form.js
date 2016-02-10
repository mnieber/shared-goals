$(document).ready(function() {
    $('#rateit-review').bind('rated', function() {
        $('#id_rating').val($(this).rateit('value'));
    });

    $("#review-form").submit(function(event) {

        // Stop form from submitting normally
        event.preventDefault();

        // Send the data using post
        var posting = $.post(
            $("#review-form").data("ajax-url"),
            $(this).serialize() + "&submit=" + $(document.activeElement)[0].id
        );

        // Put the results in a div
        posting.done(function(data) {
            $("#reviews").html(data);
            sgreviews();
        });
    });
});
