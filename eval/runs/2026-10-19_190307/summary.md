# Evaluation Run 2026-10-19_190307

## Run Status

- **Error rate:** 0.0% (0/35)
- **Partial:** No. All 35 test set samples were selected.
- **Interrupted:** No. All 35 selected samples ran.
- **Incomplete:** No. No samples errored.

## Run Details

- **run_id:** 2026-10-19_190307
- **date:** 2026-10-19T19:03:07
- **rubric_version:** 1.6
- **test_set_version:** 2
- **test_set_hash:** dc07b494d8f7
- **source_text_hash:** d1137ca2ce83
- **model:** claude-haiku-4-5-20251001
- **thinking:** None
- **effort:** None
- **prompt_version:** v2
- **prompt_hash:** a24b2d79f726
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
| Cards scored in Stage 2 | 201 |
| Card count pass rate | 70.0% (21/30) |
| Source match rate | 99.5% (200/201) |
| Total tokens (input / output) | 76799 / 10876 |
| Total cost | $0.1312 |
| Average cost per generation | $0.0037 |
| Average latency per generation | 3.72s |

## By Category

| Category | Samples | Error rate | False rejection | False acceptance | Card count pass | Source match | Avg cost | Avg latency |
|---|---|---|---|---|---|---|---|---|
| already_list_like | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 100.0% (5/5) | 100.0% (22/22) | $0.0033 | 2.96s |
| code_content | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 20.0% (1/5) | 96.3% (26/27) | $0.0039 | 3.74s |
| dense_textbook_prose | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 80.0% (4/5) | 100.0% (39/39) | $0.0044 | 4.62s |
| sloppy_bullets | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 40.0% (2/5) | 100.0% (54/54) | $0.0049 | 5.71s |
| table_data | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 80.0% (4/5) | 100.0% (48/48) | $0.0045 | 4.39s |
| too_short | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 100.0% (5/5) | 100.0% (11/11) | $0.0028 | 2.62s |
| unusable_input | 5 | 0.0% (0/5) | n/a (0/0) | 0.0% (0/5) | n/a (0/0) | n/a (0/0) | $0.0024 | 2.03s |

## By Sample

| Sample | Category | Expected | Outcome | Cards (expected) | Sources matching |
|---|---|---|---|---|---|
| sample_001 | dense_textbook_prose | accept | accept | 9 (9–11) | 9/9 |
| sample_002 | dense_textbook_prose | accept | accept | 11 (10–12) | 11/11 |
| sample_003 | dense_textbook_prose | accept | accept | 7 (7–8) | 7/7 |
| sample_004 | dense_textbook_prose | accept | accept | 5 (6–7) | 5/5 |
| sample_005 | dense_textbook_prose | accept | accept | 7 (7–9) | 7/7 |
| sample_006 | sloppy_bullets | accept | accept | 12 (14–16) | 12/12 |
| sample_007 | sloppy_bullets | accept | accept | 9 (8–10) | 9/9 |
| sample_008 | sloppy_bullets | accept | accept | 9 (8–10) | 9/9 |
| sample_009 | sloppy_bullets | accept | accept | 10 (11–13) | 10/10 |
| sample_010 | sloppy_bullets | accept | accept | 14 (12–13) | 14/14 |
| sample_011 | table_data | accept | accept | 10 (10–10) | 10/10 |
| sample_012 | table_data | accept | accept | 10 (9–10) | 10/10 |
| sample_013 | table_data | accept | accept | 8 (8–8) | 8/8 |
| sample_014 | table_data | accept | accept | 15 (15–15) | 15/15 |
| sample_015 | table_data | accept | accept | 5 (9–10) | 5/5 |
| sample_016 | code_content | accept | accept | 7 (8–9) | 6/7 |
| sample_017 | code_content | accept | accept | 4 (5–6) | 4/4 |
| sample_018 | code_content | accept | accept | 4 (5–7) | 4/4 |
| sample_019 | code_content | accept | accept | 5 (5–7) | 5/5 |
| sample_020 | code_content | accept | accept | 7 (8–10) | 7/7 |
| sample_021 | too_short | accept | accept | 2 (2–2) | 2/2 |
| sample_022 | too_short | accept | accept | 3 (3–3) | 3/3 |
| sample_023 | too_short | accept | accept | 3 (2–3) | 3/3 |
| sample_024 | too_short | accept | accept | 1 (1–1) | 1/1 |
| sample_025 | too_short | accept | accept | 2 (2–2) | 2/2 |
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
