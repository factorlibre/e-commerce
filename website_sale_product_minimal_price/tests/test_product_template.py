from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("post_install", "-at_install")
class TestProductWithNoPrices(HttpCase):
    """With this test we are checking that the minimal price is set
    when the product has not a price defined and the price of
    variants depend on a subpricelist.
    """

    def setUp(self):
        super().setUp()
        ProductAttribute = self.env["product.attribute"]
        ProductAttributeValue = self.env["product.attribute.value"]
        self.category = self.env["product.category"].create({"name": "Test category"})
        self.product_attribute = ProductAttribute.create(
            {"name": "Test", "create_variant": "always"}
        )
        self.product_attribute_value_test_1 = ProductAttributeValue.create(
            {"name": "Test v1", "attribute_id": self.product_attribute.id}
        )
        self.product_attribute_value_test_2 = ProductAttributeValue.create(
            {"name": "Test v2", "attribute_id": self.product_attribute.id}
        )
        self.product_template = self.env["product.template"].create(
            {
                "name": "My product test with no prices",
                "is_published": True,
                "type": "consu",
                "website_sequence": 1,
                "categ_id": self.category.id,
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": self.product_attribute.id,
                            "value_ids": [
                                (4, self.product_attribute_value_test_1.id),
                                (4, self.product_attribute_value_test_2.id),
                            ],
                        },
                    ),
                ],
            }
        )
        self.variant_1 = self.product_template.product_variant_ids[0]
        self.variant_2 = self.product_template.product_variant_ids[1]
        self.pricelist_aux = self.env["product.pricelist"].create(
            {
                "name": "Test pricelist Aux",
                "selectable": True,
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "applied_on": "0_product_variant",
                            "product_id": self.variant_1.id,
                            "compute_price": "fixed",
                            "fixed_price": 10,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "applied_on": "0_product_variant",
                            "product_id": self.variant_2.id,
                            "compute_price": "fixed",
                            "fixed_price": 11,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "applied_on": "1_product",
                            "product_tmpl_id": self.product_template.id,
                            "compute_price": "fixed",
                            "fixed_price": 14,
                        },
                    ),
                ],
            }
        )
        self.pricelist_main = self.env["product.pricelist"].create(
            {
                "name": "Test pricelist Main",
                "selectable": True,
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "applied_on": "2_product_category",
                            "categ_id": self.category.id,
                            "compute_price": "formula",
                            "base": "pricelist",
                            "base_pricelist_id": self.pricelist_aux.id,
                        },
                    )
                ],
            }
        )
        user = self.env.ref("base.user_admin")
        user.property_product_pricelist = self.pricelist_main

    def test_get_cheapest_info_0(self):
        """The variant with the lowest price is returned"""
        self.pricelist_aux.item_ids.filtered(
            lambda i: i.product_id == self.variant_1
        ).min_quantity = 10
        info = self.product_template._get_cheapest_info(self.pricelist_main)[
            self.product_template.id
        ]
        self.assertTrue(info["has_distinct_price"])
        self.assertEqual(info["product_id"], self.variant_1.id)
        self.assertEqual(info["add_qty"], 99999999)

    def test_get_cheapest_info_1(self):
        """Both variants have the same price"""
        self.pricelist_aux.item_ids.filtered(
            lambda i: i.product_id == self.variant_1
        ).fixed_price = 11
        info = self.product_template._get_cheapest_info(self.pricelist_main)[
            self.product_template.id
        ]
        self.assertFalse(info["has_distinct_price"])
        self.assertTrue(info["has_distinct_price_from_tmpl"])
        self.assertIn(info["product_id"], self.product_template.product_variant_ids.ids)
        self.assertEqual(info["add_qty"], 1)
