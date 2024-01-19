from odoo import models
from odoo.osv import expression


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def _get_applicable_rules_domain(self, products, date, **kwargs):
        domain = super()._get_applicable_rules_domain(products, date, **kwargs)
        if self.env.context.get("based_on_pricelist"):
            domain = expression.AND(
                [
                    domain,
                    [("compute_price", "=", "formula"), ("base", "=", "pricelist")],
                ]
            )
        if self.env.context.get("has_min_qty"):
            domain = expression.AND([domain, [("min_quantity", "!=", 0)]])
        return domain
