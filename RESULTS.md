# 📊 Results

This repo has two kinds of results.

## 1. Sample output data - `results.json`

Supplied sample detector output. Each record is one batch: timestamp, number
of normal and defect detections, the normal percentage, and the GOOD/FAIL
status. See the README for how batches are scored (counts are per-frame
detections summed over 30 frames, not unique pills).

## 2. Evaluation documented in the project report

> The numbers in this section are as reported in Chapter 6 of the project
> report ("Testing" and "Results & Analysis"). The report does not state the
> test set size or a formal evaluation protocol, so treat them as the team's
> reported findings, not an independent benchmark.

**Overall detection accuracy: approximately 94% (as reported).**

Per-condition accuracy, from the report's observation table:

| Test condition | Accuracy (as reported) |
| --- | --- |
| Proper lighting, black background | 95% |
| Low lighting | 86% |
| Excessive lighting / glare | 88% |
| Uneven lighting / shadows | 84% |
| Overlapping pills | 87% |
| Random pill orientation | 92% |

Limitations the report itself documents: lighting variation and shadows
reduce accuracy; closely placed or overlapping pills can be detected as one;
most misclassifications came from lighting variation and overlapping pills.

Chapter 6 of the report also contains detection screenshots, a confusion
matrix figure, and a dashboard screenshot.
