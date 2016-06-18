
/*$(document).on('change', ':file', function() {
    console.log('change...');
    var input = $(this),
        label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
    input.trigger('fileselect', [label]);
});*/
$(document).ready(function() {
    $(':file').on('fileselect', function(event, label) {
        var input = $(this).parents('.input-group').find(':text');
        input.val(label);
    });
});
