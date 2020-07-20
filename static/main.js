// Replace feather icons
(function () {
    'use strict'
    feather.replace()

}());


// Add active attr to a clicked link
$(document).ready(function() {
    let route = window.location.pathname;
    $('a.nav-link').each(function(){
        if ($(this).attr("href") == route) {
            $(this).addClass("active");
        }
    });
});

// Populate select options based on type of the order
function changeFunc($type) {
    $.get('/ordertype?type=' + $type, function(data) {
        let dict = JSON.parse(data);
        let from = dict["from"];
        let to = dict["to"];
        $("#from-select").empty();
        $("#to-select").empty();
        if ($type == 1) {
            $("#from-select").append("<option value='' disabled selected>Warehouse</option>");
            $("#to-select").append("<option value='' disabled selected>Customer</option>");
        }
        if ($type == 2) {
            $("#from-select").append("<option value='' disabled selected>Supplier</option>");
            $("#to-select").append("<option value='' disabled selected>Warehouse</option>");
        }
        if ($type == 3) {
            $("#from-select").append("<option value='' disabled selected>Warehouse</option>");
            $("#to-select").append("<option value='' disabled selected>Warehouse</option>");
        }
        for(var i in from) {
            $("#from-select").append("<option value=" + from[i]['id'] + ">" + from[i]['name'] + "</option>");
        }
        for(var i in to) {
            $("#to-select").append("<option value=" + to[i]['id'] + ">" + to[i]['name'] + "</option>");
        }
    });
};

// Make table rows clicable when needed
$(document).ready(function($) {
    $(".clickable-row").click(function() {
        window.location = $(this).data("href");
    });
});


// Populate select options based on type of the order
function fetchUnit($id) {
    $.get('/fetchunit?id=' + $id, function(data) {
        let unit = data;
        $("#itemUnit").text(unit);
    });
};

$(document).ready(function($) {
    let val = $("select#addProductId").val();
    if (val) {
        fetchUnit(val);
    }
});

// Search the tables by text inside them
$("#searchInput").keyup(function () {
    var rows = $("#filterBody").find("tr").hide();
    if (this.value.length) {
        var data = this.value.split(" ");
        $.each(data, function (i, v) {
            rows.filter(":contains('" + v + "')").show();
        });
    } else rows.show();
});
