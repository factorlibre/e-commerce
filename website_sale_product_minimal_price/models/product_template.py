# Copyright 2019 Tecnativa - Sergio Teruel
# Copyright 2020 Tecnativa - Pedro M. Baeza
# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from markupsafe import Markup

from odoo import _, models

from odoo.addons.sale.models.product_template import (
    ProductTemplate as ProductTemplateSale,
)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_product_subpricelists(self, pricelist_id):
        return pricelist_id.item_ids.filtered(
            lambda i: (
                i.applied_on == "3_global"
                or (
                    i.applied_on == "2_product_category" and i.categ_id == self.categ_id
                )
                or (i.applied_on == "1_product" and i.product_tmpl_id == self)
                or (
                    i.applied_on == "0_product_variant"
                    and i.product_id in self.product_variant_ids
                )
            )
            and i.compute_price == "formula"
            and i.base == "pricelist"
        ).mapped("base_pricelist_id")

    def _get_variants_from_pricelist(self, pricelist_ids):
        return pricelist_ids.mapped("item_ids").filtered(
            lambda i: i.product_id in self.product_variant_ids
        )

    def _get_pricelist_variant_items(self, pricelist_id):
        res = self._get_variants_from_pricelist(pricelist_id)
        next_pricelists = self._get_product_subpricelists(pricelist_id)
        res |= self._get_variants_from_pricelist(next_pricelists)
        visited_pricelists = pricelist_id
        while next_pricelists:
            pricelist = next_pricelists[0]
            if pricelist not in visited_pricelists:
                res |= self._get_variants_from_pricelist(pricelist)
                next_pricelists |= self._get_product_subpricelists(pricelist)
                next_pricelists -= pricelist
                visited_pricelists |= pricelist
            else:
                next_pricelists -= pricelist
        return res

    def _get_cheapest_info(self, pricelist):
        """Helper method for getting the variant with lowest price."""
        # TODO: Cache this method for getting better performance
        self.ensure_one()
        min_price = 99999999
        product_id = False
        add_qty = 0
        has_distinct_price = False
        # Variants with extra price
        variants_extra_price = self.product_variant_ids.filtered("price_extra")
        variants_without_extra_price = self.product_variant_ids - variants_extra_price
        # Avoid compute prices when pricelist has not item variants defined
        variant_items = self._get_pricelist_variant_items(pricelist)
        if variant_items:
            # Take into account only the variants defined in pricelist and one
            # variant not defined to compute prices defined at template or
            # category level. Maybe there is any definition on template that
            # has cheaper price.
            variants = variant_items.mapped("product_id")
            products = variants + (self.product_variant_ids - variants)[:1]
        else:
            products = variants_without_extra_price[:1]
        products |= variants_extra_price
        for product in list(self) + list(products):
            for qty in [1, 99999999]:
                product_price = product.with_context(
                    quantity=qty, pricelist=pricelist.id
                )._get_contextual_price()
                if product_price != min_price and (
                    min_price != 99999999 or product._name == "product.template"
                ):
                    # Mark if there are different prices iterating over
                    # variants and comparing qty 1 and maximum qty
                    has_distinct_price = True
                if product_price < min_price and product._name != "product.template":
                    min_price = product_price
                    add_qty = qty
                    product_id = product.id
        return product_id, add_qty, has_distinct_price

    def _get_first_possible_combination(
        self, parent_combination=None, necessary_values=None
    ):
        """Get the cheaper product combination for the website view."""
        res = super()._get_first_possible_combination(
            parent_combination=parent_combination, necessary_values=necessary_values
        )
        if self.env.context.get("website_id") and self.product_variant_count > 1:
            # It only makes sense to change the default one when there are
            # more than one variants and we know the pricelist
            pricelist = (
                self.env["website"]
                .browse(self.env.context.get("website_id"))
                .get_current_pricelist()
            )
            product_id = self._get_cheapest_info(pricelist)[0]
            product = self.env["product.product"].browse(product_id)
            # Rebuild the combination in the expected order
            res = self.env["product.template.attribute.value"]
            for line in product.valid_product_template_attribute_line_ids:
                value = product.product_template_attribute_value_ids.filtered(
                    lambda x: x in line.product_template_value_ids
                )
                if not value:
                    value = line.product_template_value_ids[:1]
                res += value
        return res

    _original_get_combination_info = ProductTemplateSale._get_combination_info

    def _new_get_combination_info(self, only_template=False, pricelist=False, **kwargs):
        combination_info = self._original_get_combination_info(
            only_template=only_template, pricelist=pricelist, **kwargs
        )
        if only_template and self.env.context.get("website_id"):
            current_website = self.env["website"].get_current_website()
            if not pricelist:
                pricelist = current_website.get_current_pricelist()
            product_id, add_qty, has_distinct_price = self._get_cheapest_info(
                pricelist or current_website.get_current_pricelist()
            )
            combination_info["has_distinct_price"] = has_distinct_price
            if has_distinct_price:
                combination = self._get_combination_info(
                    product_id=product_id, add_qty=add_qty, pricelist=pricelist
                )
                combination_info["minimal_price"] = combination.get("price")
        return combination_info

    # Monkey patch original method from module sale, as website_sale makes
    # modifications to price
    ProductTemplateSale._get_combination_info = _new_get_combination_info

    def _search_render_results_prices(self, mapping, combination_info):
        price, list_price = super()._search_render_results_prices(
            mapping, combination_info
        )
        if (
            combination_info.get("has_distinct_price")
            and not combination_info["prevent_zero_price_sale"]
        ):
            price = Markup("<span>{}</span> ".format(_("From"))) + price
        return price, list_price
