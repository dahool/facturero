/*
 * jQuery UI Contrib Form @VERSION
 *
 * Copyright (c) 2009 AUTHORS.txt
 * (http://code.google.com/p/jqueryui-contrib/wiki/About)
 * Licensed under the MIT (MIT-LICENSE.txt)
 *
 * http://code.google.com/p/jqueryui-contrib/wiki/docform
 *
 * Depends:
 *	ui.core.js
 *	ui.button.js
 *	ui.buttongroup.js
 *	ui.notifier.js
 */

(function($) {

$.widget("ui.form", {

	_init: function() {
		var self = this,
			options = this.options;

		this.element.addClass("ui-widget");
		if($.ui.notifier)
			this.notifier = $("<div></div>")
				.prependTo(this.element)
				.notifier();

		this.method = this.element.attr("method") || "GET";
        this.method = this.method.toUpperCase();
		this.action = this.element.attr("action") || "#";
		this.inputs = this.element.find("input");

		$.extend(options.validators, $.ui.form.validators)

		this._createButtons(this.options.buttons);
		this.textInputs = this.element.find("input[type=text], input[type=password]");
	},

	destroy: function() {
		if(this.notifier)
			this.notifier.remove();
	},

	submit: function() {
		var self = this,
			data = {};
		if(!this._validate())
			return;
		
		self.inputs.each(function() {
			data[$(this).attr("name")] = $(this).val();
		});

		$.ajax({
			cache: false,
			type: self.method,
			url: self.action,
			data: data,
			error: function(request, textStatus, errorThrown) {
				var msg = "An unknown error has occurred";

				if(request.responseText)
					msg = request.responseText;
				else if(textStatus)
					msg = textStatus;
				else if(errorThrown)
					msg = errorThrown;

				self.notifier.notifier("option", "text", msg)
					.notifier("option", "style", $.ui.notifier.ERROR)
					.show("bounce");
			},
			beforeSend: function(request)
			{
				self.notifier.hide();
				self.inputs.removeClass("ui-state-error");
			},
			success: self.options.success
		});
	},

	reset: function()
	{
		this.element.each(function() {
			this.reset();
		});
		this.notifier.hide();
		this.inputs.removeClass("ui-state-error");
	},

	_setData: function(key, value) {
		switch(key) {
			case 'buttons':
				this._createButtons(value);
				break;
			case 'validators':
				$.extend(value, $.ui.form.validators);
				break;
		}
		$.widget.prototype._setData.apply(this, arguments);
	},

	_keyPress: function(self, event) {
		if(event.which == 13)
		{
			event.preventDefault();
			event.data.submit();
		}
	},

	_validate: function()
	{
		var self = this,
			options = this.options,
			msg = "";

		this.inputs.removeClass("ui-state-error");
		this.inputs.each(function() {
			var input = this;
			$.each(self.options.validators, function(name) {
				if($(input).hasClass(name)) {
					ret = this.apply(input, arguments);
					if(typeof(ret) != "undefined") {
						msg += ret;
						$(input).addClass("ui-state-error");
					}
				}
			});
		});
		if(msg != "") {
			this.notifier.notifier("option", "text", msg)
				.notifier("option", "style", $.ui.notifier.ERROR)
				.show("bounce");
			return false;
		}
		return true;
	},

	_createButtons: function(buttons)
	{
		/*this.element.find(".ui-buttongroup").remove();
		$("<div></div>").appendTo(this.element)
		.buttongroup({
			buttons: buttons,
			scope: this.element[0]
		})*/
	}
});

$.extend($.ui.form, {
	version: "@VERSION",
	validators: {
		required: function() {
			if($(this).val() == "") {
				return $(this).attr("name").toUpperCase() + " is required";
			}
		}
	},
	defaults: {
		buttons: {},
		success: function() {},
		validators: {}
	}
});

})(jQuery);
