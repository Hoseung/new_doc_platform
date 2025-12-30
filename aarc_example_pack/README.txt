AARC Example Pack (aarc-1.1)

This directory contains:
- registry_demo_aarc_1_1.json: example analysis artifact registry snapshot
- artifacts/run_demo_2025-12-31/: example artifacts referenced by the registry

IDs included:
- metric.face.yaw_mae.v1 (metric.json@v1)
- metric.driver.eye_open_ratio.v1 (metric.json@v1)
- tbl.kpi.face.yaw_mae.v1 (table.simple.json@v1)
- tbl.occ_cls.confusion_matrix.v1 (table.simple.json@v1)
- tbl.summary.category_hierarchy.v1 (table.pandoc.json@v1)  [simple Table block JSON, no merges]
- fig.demo.dummy_plot.v1 (figure.binary@v1 + figure.meta.json@v1)

Note on Korean:
Payload strings include Korean text to confirm UTF-8 + Unicode handling.

Float formatting gotcha:
Your resolver default metric formatting policy can use format(value, ".6g") when no explicit format is provided.
