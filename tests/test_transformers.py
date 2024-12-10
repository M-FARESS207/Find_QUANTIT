from find_quantity.models import Product, Sale


def get_sale_of_product(product: Product, sales: list[Sale]) -> Sale:
    for s in sales:
        if s.product == product:
            return s
