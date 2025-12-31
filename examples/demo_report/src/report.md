# Face Pose Estimation Analysis Report

This report summarizes the performance evaluation of the face pose estimation model
on the internal IR dataset (ds_demo_front_ir_v0).

## Executive Summary

<!-- BEGIN metric.face.yaw_mae.v1 -->
The overall yaw estimation accuracy is summarized below.
<!-- END metric.face.yaw_mae.v1 -->

## Detailed Results

### Yaw Estimation by Angle Range

<!-- BEGIN tbl.kpi.face.yaw_mae.v1 -->
Mean Absolute Error (MAE) of face yaw estimation across different yaw angle ranges.
<!-- END tbl.kpi.face.yaw_mae.v1 -->

<!-- BEGIN tbl.kpi.face.yaw_mae.v1.annotation -->
**Interpretation:**
- Performance degrades at extreme yaw angles (beyond +/-45 degrees)
- This is expected due to increased self-occlusion
- Consider applying yaw-dependent confidence weighting in downstream applications
<!-- END tbl.kpi.face.yaw_mae.v1.annotation -->

### Eye Openness Detection

<!-- BEGIN metric.driver.eye_open_ratio.v1 -->
Eye openness ratio metric for drowsiness detection.
<!-- END metric.driver.eye_open_ratio.v1 -->

### Sample Distribution

<!-- BEGIN tbl.summary.category_hierarchy.v1 -->
Category distribution in the evaluation dataset.
<!-- END tbl.summary.category_hierarchy.v1 -->

### Visualization

<!-- BEGIN fig.demo.dummy_plot.v1 -->
Performance visualization across test conditions.
<!-- END fig.demo.dummy_plot.v1 -->

## Methodology

The evaluation was conducted using the standard face pose evaluation pipeline.
All metrics were computed on held-out test data that was not used during model training.

## Appendix

### Occlusion Classification

<!-- BEGIN tbl.occ_cls.confusion_matrix.v1 -->
Confusion matrix for occlusion classification.
<!-- END tbl.occ_cls.confusion_matrix.v1 -->
