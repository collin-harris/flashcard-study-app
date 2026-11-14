# Evaluation Run 2026-10-23_195650

## Run Status

- **Error rate:** 0.0% (0/35)
- **Partial:** No. All 35 test set samples were selected.
- **Interrupted:** No. All 35 selected samples ran.
- **Incomplete:** No. No samples errored.

## Run Details

- **run_id:** 2026-10-23_195650
- **date:** 2026-10-23T19:56:50
- **rubric_version:** 1.6
- **test_set_version:** 2
- **test_set_hash:** dc07b494d8f7
- **source_text_hash:** d1137ca2ce83
- **model:** claude-sonnet-5-5
- **thinking:** {'type': 'between_tools'}
- **effort:** high
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
| Cards scored in Stage 2 | 251 |
| Card count pass rate | 66.7% (20/30) |
| Source match rate | 100.0% (251/251) |
| Total tokens (input / output) | 97906 / 17665 |
| Total cost | $0.3725 |
| Average cost per generation | $0.0106 |
| Average latency per generation | 3.84s |

## By Category

| Category | Samples | Error rate | False rejection | False acceptance | Card count pass | Source match | Avg cost | Avg latency |
|---|---|---|---|---|---|---|---|---|
| already_list_like | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 100.0% (5/5) | 100.0% (22/22) | $0.0085 | 2.56s |
| code_content | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 60.0% (3/5) | 100.0% (40/40) | $0.0125 | 4.92s |
| dense_textbook_prose | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 40.0% (2/5) | 100.0% (54/54) | $0.0137 | 5.47s |
| sloppy_bullets | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 60.0% (3/5) | 100.0% (64/64) | $0.0133 | 5.20s |
| table_data | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 80.0% (4/5) | 100.0% (57/57) | $0.0128 | 4.37s |
| too_short | 5 | 0.0% (0/5) | 0.0% (0/5) | n/a (0/0) | 60.0% (3/5) | 100.0% (14/14) | $0.0074 | 2.40s |
| unusable_input | 5 | 0.0% (0/5) | n/a (0/0) | 0.0% (0/5) | n/a (0/0) | n/a (0/0) | $0.0063 | 1.93s |

## By Sample

| Sample | Category | Expected | Outcome | Cards (expected) | Sources matching |
|---|---|---|---|---|---|
| sample_001 | dense_textbook_prose | accept | accept | 10 (9–11) | 10/10 |
| sample_002 | dense_textbook_prose | accept | accept | 13 (10–12) | 13/13 |
| sample_003 | dense_textbook_prose | accept | accept | 8 (7–8) | 8/8 |
| sample_004 | dense_textbook_prose | accept | accept | 9 (6–7) | 9/9 |
| sample_005 | dense_textbook_prose | accept | accept | 14 (7–9) | 14/14 |
| sample_006 | sloppy_bullets | accept | accept | 15 (14–16) | 15/15 |
| sample_007 | sloppy_bullets | accept | accept | 11 (8–10) | 11/11 |
| sample_008 | sloppy_bullets | accept | accept | 10 (8–10) | 10/10 |
| sample_009 | sloppy_bullets | accept | accept | 12 (11–13) | 12/12 |
| sample_010 | sloppy_bullets | accept | accept | 16 (12–13) | 16/16 |
| sample_011 | table_data | accept | accept | 10 (10–10) | 10/10 |
| sample_012 | table_data | accept | accept | 14 (9–10) | 14/14 |
| sample_013 | table_data | accept | accept | 8 (8–8) | 8/8 |
| sample_014 | table_data | accept | accept | 15 (15–15) | 15/15 |
| sample_015 | table_data | accept | accept | 10 (9–10) | 10/10 |
| sample_016 | code_content | accept | accept | 9 (8–9) | 9/9 |
| sample_017 | code_content | accept | accept | 6 (5–6) | 6/6 |
| sample_018 | code_content | accept | accept | 6 (5–7) | 6/6 |
| sample_019 | code_content | accept | accept | 8 (5–7) | 8/8 |
| sample_020 | code_content | accept | accept | 11 (8–10) | 11/11 |
| sample_021 | too_short | accept | accept | 4 (2–2) | 4/4 |
| sample_022 | too_short | accept | accept | 3 (3–3) | 3/3 |
| sample_023 | too_short | accept | accept | 3 (2–3) | 3/3 |
| sample_024 | too_short | accept | accept | 1 (1–1) | 1/1 |
| sample_025 | too_short | accept | accept | 3 (2–2) | 3/3 |
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
