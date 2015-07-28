/**
 * Created by Salandora on 17.07.2015.
 */
$(function() {
    function BossacViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];

        self._displayNotification = function(response) {
            if (response == "success") {
                new PNotify({
                    title: gettext("Flashing firmware succeeded"),
                    text: gettext("Congratulations flashing the firmware was a success!"),
                    type: "success",
                    hide: false
                })
            } else {
                new PNotify({
                    title: gettext("Something went wrong"),
                    text: gettext("Flashing the firmware failed, please see the log for details"),
                    type: "error",
                    hide: false
                });
            }
        };

        self.bar_progress = function(bar_type, progress) {
            if(progress == "reset"){
                var bar_types = ["bossac_read", "bossac_write", "bossac_verify", "bossac_done"];
                _.each(bar_types, function(bar_type){
                    $("#"+bar_type+"_progress", $("#status_plugin_flasharduino_bossac")).removeClass();
                    $("#"+bar_type+"_progress", $("#status_plugin_flasharduino_bossac")).addClass("progress progress-info");
                });
            }

            if(progress == "busy"){
                $("#"+bar_type+"_progress", $("#status_plugin_flasharduino_bossac")).removeClass("progress-info");
                $("#"+bar_type+"_progress", $("#status_plugin_flasharduino_bossac")).addClass("progress-striped progress-warning active");
            }
            if(progress == "done"){
                $("#"+bar_type+"_progress", $("#status_plugin_flasharduino_bossac")).removeClass("progress-striped progress-warning active");
                $("#"+bar_type+"_progress", $("#status_plugin_flasharduino_bossac")).addClass("progress-success");
            }

        };

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "flasharduino") {
                return;
            }

            if (!data.hasOwnProperty("programmer") || data["programmer"] != "bossac" || !data.hasOwnProperty("type")) {
                    return;
            }

            var messageType = data.type;
            if (messageType == "progress") {
                var progress = data.progress;
                var bar_type = data.bar_type;

                self.bar_progress(bar_type, progress);
            } else if (messageType == "result") {
                var result = data.result
                self._displayNotification(result);
                window.setTimeout(function() {
                    $('#status_plugin_flasharduino_bossac').removeClass('active');
                }, 1000);
            }
        };

        self.onBeforeBinding = function () {
            self.settings = self.settingsViewModel.settings;
        };

     }
    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable ADDITIONAL_VIEWMODELS
    ADDITIONAL_VIEWMODELS.push([
        BossacViewModel,
        ["settingsViewModel"],
        ["#settings_plugin_flasharduino_bossac", "#status_plugin_flasharduino_bossac"]
    ]);
});
