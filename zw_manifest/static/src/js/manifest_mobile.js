odoo.define('zw_manifest.manifest_mobile', function (require) {
    "use strict";
    var core = require('web.core');
    var Widget = require('web.Widget');

    var ManifestMobileWidget = Widget.extend({
        events: {
            'click .advance_status': '_onAdvanceStatus',
        },
        _onAdvanceStatus: function (ev) {
            var manifest_id = $(ev.currentTarget).data('manifest-id');
            this._rpc({
                model: 'waste.manifest',
                method: 'action_advance_status',
                args: [manifest_id],
            }).then(function () {
                window.location.reload();
            });
        },
    });

    core.action_registry.add('zw_manifest.manifest_mobile', ManifestMobileWidget);
    return ManifestMobileWidget;
});
