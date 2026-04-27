# Medallion Architecture Design

The medallion architecture for this project follows the Bronze/Silver/Gold pattern within Microsoft Fabric: Bronze stores raw, unmodified Parquet files landed from the synthetic generator; Silver applies cleaning, conformance, and schema enforcement using Great Expectations; Gold presents a star-schema semantic model optimised for Power BI consumption. Detailed table designs, partitioning strategies, and Fabric notebook specifications will be documented here in Phase 4.
