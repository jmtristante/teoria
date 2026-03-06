from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("modulo3_demo").getOrCreate()

data = [
    (1, "ACME", 1200.5),
    (2, "Globex", 980.1),
    (3, "Initech", 1430.0),
]

df = spark.createDataFrame(data, ["id", "cliente", "importe"])
df = df.withColumn("importe_con_iva", df.importe * 1.21)

df.show()

spark.stop()
