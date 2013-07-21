var bcm;

$(document).ready(function() {
    window.bcm = new BCM();
    window.bcm.init();
});

function BCM() {
    /* *
    /* Main controller for all things Box Chart Maker
    /* Instantiate other objects here
     */

    this.input = new Input();
    this.output = new Output();
}

BCM.prototype.init = function() {
    /* *
    /* Initialize here instead of in BCM() so that we can reference the `bcm`
    /* instance.
     */

     this.input.setActiveChartOptions();
     this.input.render();
     this.input.initValidation();
     this.output.initUI();
     this.output.showHtml();
}


function Box() {
    this.num = ++bcm.input.chart[0].num;
    this.color = "#A77EE4";
    this.data = {
        name: "Kevin Schaul",
        school: "University of Minnesota"
    };
    return this;
}

Box.prototype.setData = function(dataKey, dataValue) {
    this.data[dataKey] = dataValue;
    return dataValue;
}

Box.prototype.getData = function(dataKey) {
    return this.data[dataKey];
}


function Chart() {
    this.activeInput = false;
    this.type = "box";
    this.title = "Data title";
    this.color = "#ra777a";
    this.hoverColor = "#73b1b7";
    this.rowLength = 10;
    this.numItems = 36;
    this.element = $("#chart");
    this.margin = 2;
    this.dimensions = 15;
    this.visEngine = "html";
    this.id = "box_id";
    this.numberInTitle = false;
    this.num = 0;
    this.items = [];
    return this;
}

Chart.prototype.setOption = function(option, value) {
    this[option] = value;
    return this;
}

Chart.prototype.render = function() {
    if (this.visEngine === "html") {
        var html = "";
        html += "<div id=\"" + this.id + "\">\n"
                + "<h3 class=\"chartTitle\">" + this.title;
        if(this.numberInTitle === true){
            html += ":&nbsp;<span>" + this.numItems + "</span>";
        }
        html += "</h3>\n";
        this.items = [];
        for (var i = 0; i < this.numItems; i++) {
            this.items[i] = new Box();
        }
        for (var i = 0; i < this.items.length; i++) {
            var item = this.items[i];
            if (i % this.rowLength === 0) {
                html += "<a class=\"box\""
                        + "id=\"" + this.id + "\""
                        + " style=\"clear:both;\"></a>\n";
            } else {
                html += "<a class=\"box\""
                        + "id=\"" + this.id + "\""
                        + "></a>\n";
            }
        }
        html += "<div class=\"clear\"></div></div>";
        $(this.element).append(html);
    } else if (this.visEngine === "Raphael") {
        alert('Raphael - not yet implemented');
    } else {
        bcm.output.displayError("Invalid visEngine: " + this.visEngine);
    }
    return this;
}


function Input() {
    this.chart = new Array(new Chart());
    this.chart[0].activeInput = true;
    this.valid = true;
    var that = this;
    $('#boxmkr_form_submit').click(function() {
        bcm.output.clearError();
         if (that.validateInput().valid) {
             that.setActiveChartOptions();
             that.render();
             bcm.output.showHtml();
         } else {
             bcm.output.displayError("There is a problem with your input.");
         }
        return false;
    });
    $('#boxmkr_toggle_advanced_options').click(function() {
        if ($('#advanced_options').is(':visible')) { //TODO change these to jQuery toggles
            $('#advanced_options').hide('slow');
            $('#boxmkr_toggle_advanced_options').html('Show advanced options');
        } else {
            $('#advanced_options').show('slow');
            $('#boxmkr_toggle_advanced_options').html('Hide advanced options');
        }
        return false;
    });
    $('#boxmkr_toggle_embed_code').click(function() {
        if ($('#embed_code').is(':visible')) {
            $('#embed_code').hide('slow');
            $('#boxmkr_toggle_embed_code').html('Show embed code');
        } else {
            $('#embed_code').show('slow');
            $('#boxmkr_toggle_embed_code').html('Hide embed code');
        }
        return false;
    });
    $("#output").click(function() {
        this.select();
    });
    $(document).click(function() {
        $("#colorpicker").hide("slow");
        $("#hovercolorpicker").hide("slow");
    });
    $('#boxmkr_form_color').click(function(e) {
        // Overrides document.click function
        e.stopPropagation();
        $('#colorpicker').show('slow');
        $('#hovercolorpicker').hide('slow');
    });
    $('#boxmkr_form_color_hover').click(function(e) {
        // Overrides document.click function
        e.stopPropagation();
        $('#hovercolorpicker').show('slow');
        $('#colorpicker').hide('slow');
    });
    return this;
}

Input.prototype.render = function() {
    $(this.chart[0].element).empty(); //TODO make element a part of Input
    for (var i = 0; i < this.chart.length; i++) {
        this.chart[i].render();
        $(this.chart[i].element).append(
            "\n\n" +
            "<style type=text/css>\n" +
            "   .clear { clear: both; }\n" +
            "   .box#" + this.chart[i].id + " {\n" +
            "       float: left;\n" +
            "       margin-right: " + this.chart[i].margin  + "px;\n" +
            "       margin-bottom: " + this.chart[i].margin  + "px;\n" +
            "       height: " + this.chart[i].dimensions  + "px;\n" +
            "       width: " + this.chart[i].dimensions  + "px;\n" +
            "       background-color: " + this.chart[i].color + ";\n" +
            "   }\n" +
            "   .box#" + this.chart[i].id + ":hover {\n" +
            "       background-color: " + this.chart[i].hoverColor + ";\n" +
            "   }\n" +
            "</style>\n"
            );
    }
    return this;
}

Input.prototype.setActiveChartOptions = function() {
    var activeChart;
    for (var i = 0; i < this.chart.length; i++) {
        if (this.chart[i].activeInput) {
            activeChart = this.chart[i];
            // TODO add break?
        }
    }
    activeChart.setOption("numItems", $("#boxmkr_form_numBoxes").val());
    activeChart.setOption("rowLength", $("#boxmkr_form_rowLength").val());
    activeChart.setOption("title", $("#boxmkr_form_label").val());
    activeChart.setOption("gravity", $("#boxmkr_form_gravity").val());
    activeChart.setOption("color", $("#boxmkr_form_color").val());
    activeChart.setOption("hoverColor", $("#boxmkr_form_color_hover").val());
    activeChart.setOption("margin", $("#boxmkr_form_box_margin").val());
    activeChart.setOption("dimensions",
            $("#boxmkr_form_box_dimensions").val());
    activeChart.setOption("id", $("#boxmkr_form_id").val());
    activeChart.setOption("numberInTitle", $("#boxmkr_form_numberInTitle").is(':checked'));
    activeChart.setOption("visEngine", $("#boxmkr_form_vis_engine").val());
    return this;
}

Input.prototype.initValidation = function() {
    var that = this;
    $('#boxmkr_form_numBoxes').change(function() {
        bcm.output.clearError();
        that.validateNum(0, 1000, $('#boxmkr_form_numBoxes').val(),
                '#boxmkr_form_numBoxes');
    });
    $('#boxmkr_form_rowLength').change(function() {
        bcm.output.clearError();
        that.validateNum(0, 100, $('#boxmkr_form_rowLength').val(),
                '#boxmkr_form_rowLength');
    });
    $('#boxmkr_form_label').change(function() {
        bcm.output.clearError();
        that.validateLabel($('#boxmkr_form_label').val(), '#boxmkr_form_label');
    });
    $('#boxmkr_form_color').change(function() {
        bcm.output.clearError();
        that.validateHex($('#boxmkr_form_color').val(), '#boxmkr_form_color');
    });
    $('#boxmkr_form_color_hover').change(function() {
        bcm.output.clearError();
        that.validateHex($('#boxmkr_form_color_hover').val(),
                '#boxmkr_form_color_hover');
    });
    $('#boxmkr_form_box_dimensions').change(function() {
        bcm.output.clearError();
        that.validateNum(0, 100, $('#boxmkr_form_box_dimensions').val(),
                '#boxmkr_form_box_dimensions');
    });
    $('#boxmkr_form_box_margin').change(function() {
       bcm.output.clearError();
        that.validateNum(0, 25, $('#boxmkr_form_box_margin').val(),
                '#boxmkr_form_box_margin');
    });
    return this;
}

Input.prototype.validateInput = function() {
    this.valid = true;
    if (this.valid && !this.validateNum(0, 1000,
                $('#boxmkr_form_numBoxes').val(), '#boxmkr_form_numBoxes')) {
        this.valid = false;
    }
    if (this.valid && !this.validateNum(0, 100,
                $('#boxmkr_form_rowLength').val(), '#boxmkr_form_rowLength')) {
        this.valid = false;
    }
    if (this.valid && !this.validateLabel($('#boxmkr_form_label').val(),
                '#boxmkr_form_label')) {
        this.valid = false;
    }
    if (this.valid && !this.validateHex($('#boxmkr_form_color').val(),
                '#boxmkr_form_color')) {
        this.valid = false;
    }
    if (this.valid && !this.validateHex($('#boxmkr_form_color_hover').val(),
                '#boxmkr_form_color_hover')) {
        this.valid = false;
    }
    if (this.valid && !this.validateNum(0, 100,
                $('#boxmkr_form_box_dimensions').val(),
                '#boxmkr_form_box_dimensions')) {
        this.valid = false;
    }
    if (this.valid && !this.validateNum(0, 25,
                $('#boxmkr_form_box_margin').val(),
                '#boxmkr_form_box_margin')) {
        this.valid = false;
    }
    return this;
}

Input.prototype.validateNum = function(min, max, value, selector) {
    this.clearInputFeedback(selector);
    var re = /^[0-9]+$/;
    if (value >= min && value <= max && re.exec(value)) {
        //addInputFeedback(selector, 'success');
        return true;
    } else {
        this.addInputFeedback(selector, 'error');
        return false;
    }
}

Input.prototype.validateHex = function(value, selector) {
    this.clearInputFeedback(selector);
    var re = /^#([A-Za-z0-9]{6})$/;
    if (re.exec(value)) {
        //addInputFeedback(selector, 'success');
        return true;
    } else {
        this.addInputFeedback(selector, 'error');
        return false;
    }
}

Input.prototype.validateLabel = function(value, selector) {
    this.clearInputFeedback(selector);
    var re = /^[^<>]*$/;
    if (re.exec(value)) {
        //addInputFeedback(selector, 'success');
        return true;
    } else {
        this.addInputFeedback(selector, 'error');
        return false;
    }
}

Input.prototype.clearInputFeedback = function(selector) {
    $(selector).parents('.control-group')
            .removeClass('error')
            .removeClass('success');
    return this;
}

Input.prototype.addInputFeedback = function(selector, feedback) {
    $(selector).parents('.control-group').addClass(feedback);
    return this;
}


function Output() {
    this.element = $("#output");
    this.errorElement = $("#error");
    return this;
}

Output.prototype.showHtml = function() {
    $(this.element).html(
            $("<div/>").text($(window.bcm.input.chart[0].element).html()).html()
    );
    return this;
}

Output.prototype.displayError = function(description) {
    var message = "<div class=\"alert alert-error\">"
            +  "<p><strong>Uh oh!</strong> " + description + "</p></div>";
    $(this.errorElement).html(message).show("fast");
    return this;
}

Output.prototype.clearError = function() {
    $(this.errorElement).hide("slow").empty();
    return this;
}

Output.prototype.initUI = function() {
    $(this.errorElement).hide();
    $("#colorpicker").farbtastic("#boxmkr_form_color");
    $("#hovercolorpicker").farbtastic("#boxmkr_form_color_hover");
    $('#colorpicker').hide();
    $('#hovercolorpicker').hide();
    return this;
}

