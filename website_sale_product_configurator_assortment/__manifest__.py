{
    "name": "Website Sale Product Configurator Assortment",
    "version": "16.0.1.0.0",
    "category": "Website/Website",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/e-commerce",
    "license": "AGPL-3",
    "summary": "Añadir las restrinciones de los surtidos en los productos opcionales",
    "depends": [
        "website_sale_product_configurator",
        "website_sale_product_assortment",
    ],
    "data": ["views/product_configurator_views.xml"],
    "assets": {
        "web.assets_frontend": [
            "website_sale_product_configurator_assortment/static/src/js/"
            "product_configurator_modal.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": True,
}
