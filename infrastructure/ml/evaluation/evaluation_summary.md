# Controlled synthetic experiment

No live attack detection or production accuracy is established.

{
  "provenance": "synthetic-controlled",
  "production_ready": false,
  "model_version": "iforest-a51ad3e496475a8d",
  "evaluation_date": "2026-10-23T08:19:27.042306+00:00",
  "training_windows": 360,
  "evaluation_windows": 180,
  "ml": {
    "confusion_matrix": [
      [
        56,
        4
      ],
      [
        66,
        54
      ]
    ],
    "precision": 0.9310344827586207,
    "recall": 0.45,
    "f1": 0.6067415730337079,
    "false_positive_rate": 0.06666666666666667,
    "windows": 180,
    "class_distribution": {
      "normal": 60,
      "controlled_scenario": 120
    }
  },
  "rules": {
    "confusion_matrix": [
      [
        60,
        0
      ],
      [
        96,
        24
      ]
    ],
    "precision": 1.0,
    "recall": 0.2,
    "f1": 0.3333333333333333,
    "false_positive_rate": 0.0,
    "windows": 180,
    "class_distribution": {
      "normal": 60,
      "controlled_scenario": 120
    }
  },
  "rule_configuration": {
    "version": 1,
    "window_seconds": 300,
    "threshold": 0.5,
    "minimum_requests": 20,
    "baseline_windows": 12
  },
  "detection_latency_seconds": null,
  "latency_note": "Offline evaluation; live latency not measured. Finalization waits 120 seconds after window end.",
  "comparison_note": "Same labeled minutes; Step 6 error-rate uses its actual 300-second history, ML uses 60 seconds."
}
