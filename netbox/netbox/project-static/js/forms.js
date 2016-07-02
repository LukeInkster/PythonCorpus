$(document).ready(function() {

    // "Select all" checkbox in a table header
    $('th input:checkbox').click(function (event) {
        $(this).parents('table').find('td input:checkbox').prop('checked', $(this).prop('checked'));
    });

    // Slugify
    function slugify(s, num_chars) {
        s = s.replace(/[^\-\.\w\s]/g, '');   // Remove unneeded chars
        s = s.replace(/^\s+|\s+$/g, '');     // Trim leading/trailing spaces
        s = s.replace(/[\-\.\s]+/g, '-');    // Convert spaces and decimals to hyphens
        s = s.toLowerCase();                 // Convert to lowercase
        return s.substring(0, num_chars);    // Trim to first num_chars chars
    }
    var slug_field = $('#id_slug');
    slug_field.change(function() {
        $(this).attr('_changed', true);
    });
    if (slug_field) {
        var slug_source = $('#id_' + slug_field.attr('slug-source'));
        slug_source.keyup(function() {
            if (slug_field && !slug_field.attr('_changed')) {
                slug_field.val(slugify($(this).val(), 50));
            }
        })
    }

    // Helper select fields
    $('select.helper-parent').change(function () {

        // Resolve child field by ID specified in parent
        var child_field = $('#id_' + $(this).attr('child'));

        // Wipe out any existing options within the child field
        child_field.empty();
        child_field.append($("<option></option>").attr("value", "").text(""));

        // If the parent has a value set, fetch a list of child options via the API and populate the child field with them
        if ($(this).val()) {

            // Construct the API request URL
            var api_url = $(this).attr('child-source');
            var parent_accessor = $(this).attr('parent-accessor');
            if (parent_accessor) {
                api_url += '?' + parent_accessor + '=' + $(this).val();
            } else {
                api_url += '?' + $(this).attr('name') + '_id=' + $(this).val();
            }
            var api_url_extra = $(this).attr('child-filter');
            if (api_url_extra) {
                api_url += '&' + api_url_extra;
            }

            var disabled_indicator = $(this).attr('disabled-indicator');
            var disabled_exempt = child_field.attr('exempt');
            var child_display = $(this).attr('child-display');
            if (!child_display) {
                child_display = 'name';
            }

            $.ajax({
                url: api_url,
                dataType: 'json',
                success: function (response, status) {
                    console.log(response);
                    $.each(response, function (index, choice) {
                        var option = $("<option></option>").attr("value", choice.id).text(choice[child_display]);
                        if (disabled_indicator && choice[disabled_indicator] && choice.id != disabled_exempt) {
                            option.attr("disabled", "disabled")
                        }
                        child_field.append(option);
                    });
                }
            });

        }

        // Trigger change event in case the child field is the parent of another field
        child_field.change();

    });

    // API select widget
    $('select[filter-for]').change(function () {

        // Resolve child field by ID specified in parent
        var child_name = $(this).attr('filter-for');
        var child_field = $('#id_' + child_name);

        // Wipe out any existing options within the child field
        child_field.empty();
        child_field.append($("<option></option>").attr("value", "").text(""));

        if ($(this).val()) {

            var api_url = child_field.attr('api-url');
            var disabled_indicator = child_field.attr('disabled-indicator');
            var initial_value = child_field.attr('initial');
            var display_field = child_field.attr('display-field') || 'name';

            // Gather the values of all other filter fields for this child
            $("select[filter-for='" + child_name + "']").each(function() {
                var filter_field = $(this);
                if (filter_field.val()) {
                    api_url = api_url.replace('{{' + filter_field.attr('name') + '}}', filter_field.val());
                } else {
                    // Not all filters have been selected yet
                    return false;
                }

            });

            // If all URL variables have been replaced, make the API call
            if (api_url.search('{{') < 0) {
                $.ajax({
                    url: api_url,
                    dataType: 'json',
                    success: function (response, status) {
                        $.each(response, function (index, choice) {
                            var option = $("<option></option>").attr("value", choice.id).text(choice[display_field]);
                            if (disabled_indicator && choice[disabled_indicator] && choice.id != initial_value) {
                                option.attr("disabled", "disabled")
                            }
                            child_field.append(option);
                        });
                    }
                });
            }

        }

        // Trigger change event in case the child field is the parent of another field
        child_field.change();

    });
});
