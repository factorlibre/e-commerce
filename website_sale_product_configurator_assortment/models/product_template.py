from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1,
        pricelist=False,
        parent_combination=False,
        only_template=False,
    ):
        res = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            pricelist=pricelist,
            parent_combination=parent_combination,
            only_template=only_template,
        )
        if not res["product_id"]:
            return res

        product_res_id = res["product_id"]
        product = self.env["product.product"].browse(int(product_res_id))
        product_template = self.env["product.template"]
        assortments_dict = product_template.get_product_assortment_restriction_info(
            self.env["product.product"].search([]).ids
        )
        if assortments_dict:
            assortment = assortments_dict.get(
                product_res_id, next(iter(assortments_dict.values()))
            )
            all_product_ids = assortment[0]["all_product_ids"].ids

            allowed_optional_product_ids = product.optional_product_ids.filtered(
                lambda p: any(
                    variant.id in all_product_ids for variant in p.product_variant_ids
                )
            ).ids
            assortment_restriction = (
                assortment[0]["website_availability"] == "no_show"
                if assortment
                else False
            )

            res["allowed_optional_product_ids"] = allowed_optional_product_ids
            res["assortment_restriction"] = assortment_restriction
        else:
            res["allowed_optional_product_ids"] = []
            res["assortment_restriction"] = False
        return res
