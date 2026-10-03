# Evaluation Run 2026-10-02_215610

## Run Status

- **Error rate:** 0.0% (0/35)
- **Partial:** No. All 35 test set samples were selected.
- **Interrupted:** No. All 35 selected samples ran.
- **Incomplete:** No. No samples errored.

## Run Details

- **run_id:** 2026-10-02_215610
- **date:** 2026-10-02T21:56:10
- **rubric_version:** 1.4
- **model:** claude-haiku-4-5-20251001
- **prompt_version:** v1
- **prompt_hash:** f5e88f4d8fd8
- **max_tokens:** 4096
- **request_timeout_seconds:** 60
- **max_retries:** 2
- **gate_approach:** single call
- **anthropic_sdk_version:** 1.9.0

## Errored Samples

None.

## Overall

| Metric | Value |
|---|---|
| Samples run | 35 |
| Error rate | 0.0% (0/35) |
| False rejection rate | 0.0% (0/30) |
| False acceptance rate | 0.0% (0/5) |
| Batches scored in Stage 2 | 30 |
| Cards scored in Stage 2 | 190 |
| Card count pass rate | 53.3% (16/30) |
| Source match rate | 94.7% (180/190) |
| Total tokens (input / output) | 60104 / 10651 |
| Total cost | $0.1134 |
| Average cost per generation | $0.0032 |
| Average latency per generation | 3.07s |

## By Category

| Category | Samples | Error rate | False rejection | False acceptance | Card count pass | Source match | Avg cost | Avg latency |
|---|---|---|---|---|---|---|---|---|
| already_list_like | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 100.0% (5/5) | 100.0% (22/22) | $0.0028 | 2.21s |
| code_content | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 80.0% (4/5) | 91.7% (22/24) | $0.0032 | 3.17s |
| dense_textbook_prose | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 20.0% (1/5) | 100.0% (35/35) | $0.0039 | 4.13s |
| sloppy_bullets | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 20.0% (1/5) | 100.0% (51/51) | $0.0044 | 5.01s |
| table_data | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 20.0% (1/5) | 83.3% (40/48) | $0.0041 | 3.70s |
| too_short | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 80.0% (4/5) | 100.0% (10/10) | $0.0023 | 1.91s |
| unusable_input | 5 | 0.0% (0/5) | n/a (0/0) | 0.0% (0/5) | n/a (0/0) | n/a (0/0) | $0.0020 | 1.38s |

## By Sample

| Sample | Category | Expected | Outcome | Cards (expected) | Sources matching |
|---|---|---|---|---|---|
| sample_001 | dense_textbook_prose | accept | accept | 7 (4–6) | 7/7 |
| sample_002 | dense_textbook_prose | accept | accept | 9 (4–6) | 9/9 |
| sample_003 | dense_textbook_prose | accept | accept | 7 (3–5) | 7/7 |
| sample_004 | dense_textbook_prose | accept | accept | 5 (4–6) | 5/5 |
| sample_005 | dense_textbook_prose | accept | accept | 7 (4–6) | 7/7 |
| sample_006 | sloppy_bullets | accept | accept | 13 (5–7) | 13/13 |
| sample_007 | sloppy_bullets | accept | accept | 9 (4–6) | 9/9 |
| sample_008 | sloppy_bullets | accept | accept | 6 (5–7) | 6/6 |
| sample_009 | sloppy_bullets | accept | accept | 11 (5–7) | 11/11 |
| sample_010 | sloppy_bullets | accept | accept | 12 (5–7) | 12/12 |
| sample_011 | table_data | accept | accept | 10 (5–6) | 10/10 |
| sample_012 | table_data | accept | accept | 9 (5–6) | 9/9 |
| sample_013 | table_data | accept | accept | 8 (4–5) | 0/8 |
| sample_014 | table_data | accept | accept | 15 (5–6) | 15/15 |
| sample_015 | table_data | accept | accept | 6 (5–6) | 6/6 |
| sample_016 | code_content | accept | accept | 6 (3–5) | 6/6 |
| sample_017 | code_content | accept | accept | 4 (2–4) | 4/4 |
| sample_018 | code_content | accept | accept | 4 (3–5) | 2/4 |
| sample_019 | code_content | accept | accept | 5 (3–5) | 5/5 |
| sample_020 | code_content | accept | accept | 5 (3–5) | 5/5 |
| sample_021 | too_short | accept | accept | 2 (1–2) | 2/2 |
| sample_022 | too_short | accept | accept | 3 (1–2) | 3/3 |
| sample_023 | too_short | accept | accept | 2 (1–2) | 2/2 |
| sample_024 | too_short | accept | accept | 1 (1–1) | 1/1 |
| sample_025 | too_short | accept | accept | 2 (1–2) | 2/2 |
| sample_026 | already_list_like | accept | accept | 4 (4–4) | 4/4 |
| sample_027 | already_list_like | accept | accept | 4 (4–4) | 4/4 |
| sample_028 | already_list_like | accept | accept | 5 (5–5) | 5/5 |
| sample_029 | already_list_like | accept | accept | 4 (4–4) | 4/4 |
| sample_030 | already_list_like | accept | accept | 5 (5–5) | 5/5 |
| sample_031 | unusable_input | reject | reject | - | - |
| sample_032 | unusable_input | reject | reject | - | - |
| sample_033 | unusable_input | reject | reject | - | - |
| sample_034 | unusable_input | reject | reject | - | - |
| sample_035 | unusable_input | reject | reject | - | - |
