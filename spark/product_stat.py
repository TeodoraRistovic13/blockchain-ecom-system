from pyspark.sql import SparkSession
from pyspark.sql.functions import expr

import os
import json

PRODUCTION = True if ("PRODUCTION" in os.environ) else False
DATABASE_IP = os.environ["DATABASE_IP"] if ("DATABASE_IP" in os.environ) else "localhost"

builder = SparkSession.builder.appName("ProductStatistics")

if (not PRODUCTION):
    builder = builder.master("local[*]") \
        .config(
        "spark.driver.extraClassPath",
        "mysql-connector-j-8.0.33.jar"
    )

spark = builder.getOrCreate()

product_df = spark.read \
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

order_df = spark.read \
    .format ( "jdbc" ) \
    .option ( "driver","com.mysql.cj.jdbc.Driver" ) \
    .option ( "url", f"jdbc:mysql://productsDB/shop" ) \
    .option ( "dbtable", "shop.orders" ) \
    .option ( "user", "root" ) \
    .option ( "password", "root" ) \
    .load ( )


joined_df = product_order_df.join(product_df, product_order_df.productId == product_df.id)

joined_df = joined_df.join(order_df, joined_df.orderId == order_df.id)

statistics_df = joined_df.groupBy("name").agg(
    expr("sum(case when status = 'COMPLETE' then quantity else 0 end)").alias("sold"),
    expr("sum(case when status in ('PENDING', 'CREATED') then quantity else 0 end)").alias("waiting")
)

filtered_statistics_df = statistics_df.filter((statistics_df.sold >= 1) | (statistics_df.waiting >= 1))

statistics = [
    {
        "name": row.name,
        "sold": row.sold,
        "waiting": row.waiting
    }
    for row in filtered_statistics_df.collect()
]

with open('/data/product_statistics.txt', 'w') as file:
    for stat in statistics:
       file.write(f"{stat['name']}|{stat['sold']}|{stat['waiting']}" + "\n")
       file.flush()

spark.stop()

