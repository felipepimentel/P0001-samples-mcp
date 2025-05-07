import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Complex Models")

# Sample data store
users = [
    {
        "id": 1,
        "name": "Alice",
        "email": "alice@example.com",
        "role": "admin",
        "active": True,
    },
    {
        "id": 2,
        "name": "Bob",
        "email": "bob@example.com",
        "role": "user",
        "active": True,
    },
    {
        "id": 3,
        "name": "Charlie",
        "email": "charlie@example.com",
        "role": "user",
        "active": False,
    },
]

products = [
    {
        "id": 101,
        "name": "Laptop",
        "price": 999.99,
        "category": "electronics",
        "stock": 45,
    },
    {
        "id": 102,
        "name": "Headphones",
        "price": 149.99,
        "category": "electronics",
        "stock": 120,
    },
    {"id": 103, "name": "Coffee Mug", "price": 12.99, "category": "home", "stock": 200},
    {"id": 104, "name": "Notebook", "price": 4.99, "category": "office", "stock": 350},
    {"id": 105, "name": "Plant Pot", "price": 24.99, "category": "home", "stock": 0},
]


# Define enums for valid values
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class ProductCategory(str, Enum):
    ELECTRONICS = "electronics"
    HOME = "home"
    OFFICE = "office"
    CLOTHING = "clothing"


# Define dataclasses for our models
@dataclass
class User:
    id: int
    name: str
    email: str
    role: UserRole
    active: bool = True

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
        }


@dataclass
class Product:
    id: int
    name: str
    price: float
    category: ProductCategory
    stock: int = 0

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "category": self.category,
            "stock": self.stock,
            "in_stock": self.in_stock,
        }


# Helper functions to convert between dict and our models
def dict_to_user(user_dict: Dict) -> User:
    return User(
        id=user_dict["id"],
        name=user_dict["name"],
        email=user_dict["email"],
        role=UserRole(user_dict["role"]),
        active=user_dict.get("active", True),
    )


def dict_to_product(product_dict: Dict) -> Product:
    return Product(
        id=product_dict["id"],
        name=product_dict["name"],
        price=product_dict["price"],
        category=ProductCategory(product_dict["category"]),
        stock=product_dict.get("stock", 0),
    )


# MCP Tools
@mcp.tool()
def get_users() -> str:
    """Get all users in the system"""
    user_objects = [dict_to_user(user) for user in users]
    return json.dumps([user.to_dict() for user in user_objects], indent=2)


@mcp.tool()
def get_user(user_id: int) -> str:
    """
    Get details for a specific user

    Args:
        user_id: The ID of the user to retrieve
    """
    for user_dict in users:
        if user_dict["id"] == user_id:
            user = dict_to_user(user_dict)
            return json.dumps(user.to_dict(), indent=2)

    return json.dumps({"error": f"User with ID {user_id} not found"})


@mcp.tool()
def get_products(in_stock_only: bool = False) -> str:
    """
    Get all products, optionally filtering for in-stock items only

    Args:
        in_stock_only: If true, only return products with stock > 0
    """
    product_objects = [dict_to_product(product) for product in products]

    if in_stock_only:
        product_objects = [p for p in product_objects if p.in_stock]

    return json.dumps([product.to_dict() for product in product_objects], indent=2)


@mcp.tool()
def get_products_by_category(category: ProductCategory) -> str:
    """
    Get all products in a specific category

    Args:
        category: The product category to filter by
    """
    filtered_products = []
    for product_dict in products:
        if product_dict["category"] == category:
            product = dict_to_product(product_dict)
            filtered_products.append(product.to_dict())

    if not filtered_products:
        return json.dumps({"message": f"No products found in category: {category}"})

    return json.dumps(filtered_products, indent=2)


@mcp.tool()
def get_product_statistics() -> str:
    """Get statistics about products"""
    product_objects = [dict_to_product(product) for product in products]

    total_products = len(product_objects)
    in_stock_count = sum(1 for p in product_objects if p.in_stock)
    total_stock = sum(p.stock for p in product_objects)
    avg_price = (
        sum(p.price for p in product_objects) / total_products
        if total_products > 0
        else 0
    )

    # Count products by category
    categories = {}
    for p in product_objects:
        if p.category not in categories:
            categories[p.category] = 0
        categories[p.category] += 1

    stats = {
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_count": total_products - in_stock_count,
        "total_stock": total_stock,
        "average_price": round(avg_price, 2),
        "products_by_category": categories,
    }

    return json.dumps(stats, indent=2)


# Complex resource that combines multiple data sources
@mcp.resource("inventory://summary")
def get_inventory_summary() -> str:
    """Get a summary of the inventory system including users and products"""
    user_objects = [dict_to_user(user) for user in users]
    product_objects = [dict_to_product(product) for product in products]

    active_users = sum(1 for u in user_objects if u.active)
    admin_count = sum(1 for u in user_objects if u.role == UserRole.ADMIN)

    in_stock_products = sum(1 for p in product_objects if p.in_stock)
    total_stock = sum(p.stock for p in product_objects)

    # Group products by category
    products_by_category = {}
    for p in product_objects:
        if p.category not in products_by_category:
            products_by_category[p.category] = []
        products_by_category[p.category].append(p.name)

    summary = {
        "users": {
            "total": len(user_objects),
            "active": active_users,
            "inactive": len(user_objects) - active_users,
            "admins": admin_count,
        },
        "products": {
            "total": len(product_objects),
            "in_stock": in_stock_products,
            "out_of_stock": len(product_objects) - in_stock_products,
            "total_stock": total_stock,
            "categories": {
                category: {"count": len(products), "items": products}
                for category, products in products_by_category.items()
            },
        },
    }

    return json.dumps(summary, indent=2)
