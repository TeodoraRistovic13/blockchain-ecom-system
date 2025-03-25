from pyspark.sql import SparkSession
from pyspark.sql.functions import expr

from pyspark.sql.functions import sum, when
import pyspark.sql.functions as F

import os
import json

PRODUCTION = True if ("PRODUCTION" in os.environ) else False
DATABASE_IP = os.environ["DATABASE_IP"] if ("DATABASE_IP" in os.environ) else "localhost"

builder = SparkSession.builder.appName("CategoryStatistics")

if (not PRODUCTION):
    builder = builder.master("local[*]") \
        .config(
        "spark.driver.extraClassPath",
        "mysql-connector-j-8.0.33.jar"
    )

spark = builder.getOrCreate()

products_df = spark.read \
    .format ( "jdbc" ) \
    .option ( "driver","com.mysql.cj.jdbc.Driver" ) \
    .option ( "url", f"jdbc:mysql://productsDB/shop" ) \
    .option ( "dbtable", "shop.products" ) \
    .option ( "user", "root" ) \
    .option ( "password", "root" ) \
    .load ( )

product_order_df = spark.read \
    .format ( "jdbc" ) \
    .option ( "driver","com.mysql.cj.jdbc.Driver" ) \
    .option ( "url", f"jdbc:mysql://productsDB/shop" ) \
    .option ( "dbtable", "shop.productorder" ) \
    .option ( "user", "root" ) \
    .option ( "password", "root" ) \
    .load ( )

orders_df = spark.read \
    .format ( "jdbc" ) \
    .option ( "driver","com.mysql.cj.jdbc.Driver" ) \
    .option ( "url", f"jdbc:mysql://productsDB/shop" ) \
    .option ( "dbtable", "shop.orders" ) \
    .option ( "user", "root" ) \
    .option ( "password", "root" ) \
    .load ( )

categories_df = spark.read \
    .format ( "jdbc" ) \
    .option ( "driver","com.mysql.cj.jdbc.Driver" ) \
    .option ( "url", f"jdbc:mysql://productsDB/shop" ) \
    .option ( "dbtable", "shop.categories" ) \
    .option ( "user", "root" ) \
    .option ( "password", "root" ) \
    .load ( )

product_category_df = spark.read \
    .format ( "jdbc" ) \
    .option ( "driver","com.mysql.cj.jdbc.Driver" ) \
    .option ( "url", f"jdbc:mysql://productsDB/shop" ) \
    .option ( "dbtable", "shop.productcategory" ) \
    .option ( "user", "root" ) \
    .option ( "password", "root" ) \
    .load ( )

categories_df.createOrReplaceTempView("categories")
products_df.createOrReplaceTempView("products")
product_category_df.createOrReplaceTempView("product_category")
product_order_df.createOrReplaceTempView("product_order")
orders_df.createOrReplaceTempView("orders")

category_statistics_df = spark.sql(
    "SELECT c.name AS category_name,"+
    "CASE "+
    "WHEN uc.total_quantity IS NULL THEN 0 "+
    "ELSE uc.total_quantity "+
    "END AS total_quantity "+
    "FROM categories c "+
    "LEFT JOIN "
    "( SELECT pc.categoryId, SUM(po.quantity) AS total_quantity "+
        "FROM product_category pc "+
        "JOIN products p ON pc.productId = p.id "+
        "JOIN product_order po ON p.id = po.productId "+
        "JOIN orders o ON po.orderId = o.id "+
        "WHERE o.status = 'COMPLETE' "+
        "GROUP BY pc.categoryId ) " +
        "uc ON c.id = uc.categoryId "+
        "GROUP BY c.name, uc.total_quantity "+
        "ORDER BY total_quantity DESC, category_name ASC;"
    )

statistics = [ row.category_name for row in category_statistics_df.collect()]

with open('/data/category_statistics.txt', 'w') as file:
    for cat in statistics:
       file.write(f"{cat}" + "\n")
       file.flush()

spark.stop()

