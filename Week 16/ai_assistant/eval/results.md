# Evaluation results (`/research` agentic loop)

Models: `gemini-3.5-flash-lite`; MAX_ITERATIONS=8; 8/8 queries recorded (2 are failure injections).

- **Task completion rate:** 8/8
- **Tool-call correctness:** 8/8 queries with all valid calls + expected tool used
- **Mean trajectory length:** 4.6 iterations
- **Total tokens:** 41858 (mean 5232 per query)

| id | model | injected failure | completed | tools ok | iterations | tokens | tool path |
|---|---|---|---|---|---|---|---|
| compare_12_14 | gemini-3.5-flash-lite | - | yes | yes | 7 | 10491 | list_available_weeks > search_course_materials > record_note > search_course_materials > search_course_materials > record_note > submit_answer |
| dataset_w14 | gemini-3.5-flash-lite | - | yes | yes | 3 | 3391 | search_course_materials > record_note > submit_answer |
| dataset_w12 | gemini-3.5-flash-lite | - | yes | yes | 3 | 3217 | search_course_materials > record_note > submit_answer |
| not_in_corpus | gemini-3.5-flash-lite | - | yes | yes | 7 | 10026 | search_course_materials > search_course_materials > list_available_weeks > search_course_materials > search_course_materials > search_course_materials > submit_answer |
| missing_week | gemini-3.5-flash-lite | - | yes | yes | 3 | 2921 | list_available_weeks > search_course_materials > submit_answer |
| vague | gemini-3.5-flash-lite | - | yes | yes | 2 | 1495 | list_available_weeks > ask_user |
| inject_search_down | gemini-3.5-flash-lite | search_unavailable | yes | yes | 6 | 5177 | search_course_materials > search_course_materials > list_available_weeks > search_course_materials > search_course_materials > submit_answer |
| inject_malformed | gemini-3.5-flash-lite | malformed_search | yes | yes | 6 | 5140 | search_course_materials > search_course_materials > list_available_weeks > search_course_materials > search_course_materials > submit_answer |

## Failure log

No failed cases.

## Final answers (truncated)

- **compare_12_14** (answered): - **Week 12** covers an end-to-end Named Entity Recognition (NER) pipeline for customer support ticket analysis, which includes text preprocessing, feature engineering, evaluation, error analysis, and
- **dataset_w14** (answered): The Week 14 assignment uses the Bitext Customer Support LLM Chatbot Training Dataset (HuggingFace: bitext/Bitext-customer-support-llm-chatbot-training-dataset), which contains 26,872 real-phrasing cus
- **dataset_w12** (answered): In Week 12, the dataset used is the WNUT-17 Emerging Entities Dataset, and the task is Named Entity Recognition (NER) (specifically, an end-to-end Named Entity Recognition pipeline for customer suppor
- **not_in_corpus** (answered): The course materials do not contain any references or information regarding Kubernetes operators.
- **missing_week** (answered): There is no Week 99 in the course materials. The available weeks are Weeks 7, 8, 9, 10, 11, 12, 14, and 15.
- **vague** (needs_clarification): Could you please specify which topic, week, or question you would like to know about?
- **inject_search_down** (answered): I could not verify which dataset the Week 14 assignment uses because the search backend encountered an error.
- **inject_malformed** (answered): I could not verify the dataset used for the Week 14 assignment because the search tool returned errors/corrupted output for Week 14 queries.
