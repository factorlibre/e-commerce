odoo.define(
    "website_sale_product_configurator_assortment.ProductConfiguratorModal",
    function (require) {
        "use strict";

        const core = require("web.core");
        const QWeb = core.qweb;
        const {
            OptionalProductsModal,
        } = require("@sale_product_configurator/js/product_configurator_modal");

        OptionalProductsModal._onChangeCombinationAssortment = function (
            ev,
            $parent,
            combination
        ) {
            $(".oe_advanced_configurator_modal")
                .find("#message_unavailable_" + combination.product_template_id)
                .remove();
            if (!this.isWebsite || !combination.product_avoid_purchase) {
                $parent.find(".fa-shopping-cart").parent().removeClass("disabled");
                return;
            }
            $parent
                .find(".td-product_name")
                .append(
                    QWeb.render(
                        "website_sale_product_assortment.product_availability",
                        combination
                    )
                );
            $parent.toggleClass("css_not_available", $parent.is(".main_product"));
            $parent.find(".fa-shopping-cart").parent().addClass("disabled");
        };

        OptionalProductsModal.include({
            /**
             * Añade las restriciones del surtido al método _onChangeCombination
             * @override
             */
            _onChangeCombination: function () {
                this._super.apply(this, arguments);
                OptionalProductsModal._onChangeCombinationAssortment.apply(
                    this,
                    arguments
                );
            },
        });
        return OptionalProductsModal;
    }
);
