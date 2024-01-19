# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, http
from odoo.http import request

from odoo.addons.sale.controllers.variant import VariantController


class WebsiteSaleVariantController(VariantController):
    @http.route(
        ["/sale/get_combination_info_minimal_price"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def get_combination_info_minimal_price(self, product_template_ids, **kw):
        """Special route to use website logic in get_combination_info override.
        This route is called in JS by appending _website to the base route.
        """
        res = []
        templates = (
            request.env["product.template"]
            .sudo()
            .browse(product_template_ids)
            .filtered("is_published")
        )
        pricelist = request.env["website"].get_current_website().get_current_pricelist()
        cheapest_info = templates._get_cheapest_info(pricelist)
        for template in templates:
            info = cheapest_info.get(template.id)
            vals = {
                "id": template.id,
                "distinct_prices": info.get("has_distinct_price"),
                "distinct_prices_tmpl": info.get("has_distinct_price_from_tmpl"),
            }
            if info.get("product_id") and (
                info.get("has_distinct_price")
                or info.get("has_distinct_price_from_tmpl")
            ):
                combination = template._get_combination_info(
                    product_id=info.get("product_id"),
                    add_qty=info.get("add_qty"),
                    pricelist=pricelist,
                )
                vals.update(
                    {
                        "price": combination.get("price"),
                        "currency": {
                            "position": template.currency_id.position,
                            "symbol": template.currency_id.symbol,
                        },
                    }
                )
            res.append(vals)
        return res

    @http.route(
        ["/sale/get_combination_info_pricelist_atributes"],
        type="json",
        auth="public",
        website=True,
    )
    def get_combination_info_pricelist_atributes(self, product_id, **kwargs):
        """Special route to use website logic in get_combination_info override.
        This route is called in JS by appending _website to the base route.
        """
        pricelist = request.env["website"].get_current_website().get_current_pricelist()
        product = (
            request.env["product.product"]
            .browse(product_id)
            .with_context(pricelist=pricelist.id)
        )
        # Getting all min_quantity of the current product to compute the possible
        # price scale.
        items = pricelist.with_context(has_min_qty=True)._get_applicable_rules(
            product, fields.Datetime.today()
        )
        qty_list = items.filtered(
            lambda i: i._is_applicable_for(product, i.min_quantity)
        ).mapped("min_quantity")
        qty_list = sorted(set(qty_list))
        res = []
        last_price = product.with_context(quantity=0)._get_contextual_price()
        for min_qty in qty_list:
            new_price = product.with_context(quantity=min_qty)._get_contextual_price()
            if new_price != last_price:
                res.append(
                    {
                        "min_qty": min_qty,
                        "price": new_price,
                        "currency": {
                            "position": product.currency_id.position,
                            "symbol": product.currency_id.symbol,
                        },
                    }
                )
                last_price = new_price
        return (res, product.uom_name)
