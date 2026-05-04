# AI Genealogy Validation

This repository contains a simple Python-based automation framework for sending natural-language genealogy questions to an AI-backed genealogy API, collecting structured responses, and saving results to an Excel file.

## What this does

- Reads a list of questions from `questions.json`
- Loads an API token from `tokens/access_token.txt`
- Sends each question to the genealogy API endpoint at `https://ai360.dev.mareana.com/v1/ai-360/genealogy/query`
- Extracts useful fields from the API response such as:
  - `cypher_query`
  - `sql_query`
  - `summary`
  - `classification`
  - `intent`
  - `is_valid`
  - `is_safe`
- Collects the API status and full response payload
- Writes results into `output/genealogy_results.xlsx`

## Why this exists

This project is meant to validate an AI genealogy API workflow by executing a batch of questions and storing both structured metadata and raw responses for analysis. It helps verify that:

- the API endpoint is reachable and returning valid responses
- the AI controller is producing expected query types (Neo4j Cypher, SQL, or neither)
- summaries, classification, and safety metadata are present
- responses can be audited later in a single spreadsheet

## Repository structure

- `run_questions.py` - main script to run requests and save results
- `questions.json` - list of question objects to send to the API
- `tokens/access_token.txt` - API access token used for authorization
- `requirements.txt` - Python dependencies
- `Dockerfile` - optional containerized runtime
- `output/` - target folder for generated Excel results

## How this works

`run_questions.py` performs the following steps:

1. Ensure the `output/` directory exists.
2. Read the bearer-like token from `tokens/access_token.txt`.
3. Load questions from `questions.json`.
4. For each question:
   - build a payload with the question text and execution options
   - send a POST request to the API using `httpx`
   - parse the JSON response
   - extract metadata fields and the full response
   - collect a result row for Excel export
5. Save all rows as `output/genealogy_results.xlsx` using `pandas`

The script uses defensive validation so missing files or API failures are handled more gracefully than a raw script.

## How to use it

### Option 1: Run locally

1. Activate the repository Python environment:

```bash
cd /Users/sharan/Desktop/ai_genealogy_validation
source myvenv/bin/activate
```

2. Install dependencies if not already installed:

```bash
pip install -r requirements.txt
```

3. Add your token to `tokens/access_token.txt`.

4. Update `questions.json` with the questions you want to evaluate.

5. Run the script:

```bash
python run_questions.py
```

6. Open the generated Excel file:

```bash
open output/genealogy_results.xlsx
```

### Option 2: Run with Docker

1. Build the Docker image:

```bash
docker build -t ai-genealogy-validation .
```

2. Run the container with output mounted:

```bash
docker run --rm -v $(pwd)/output:/app/output ai-genealogy-validation
```

> Note: The Docker image expects `tokens/access_token.txt` to be present in the repository when the container is built or copied into the image. If your token is sensitive, prefer the local environment.

## Output format

The generated spreadsheet contains columns in this order:

- `question_id`
- `question`
- `cypher_query`
- `sql_query`
- `summary`
- `classification`
- `intent`
- `is_valid`
- `is_safe`
- `status_code`
- `response`

This layout makes it easy to review both the structured metadata and raw JSON response per question.

## Notes and best practices

- Keep your access token private and do not commit it to source control.
- If the API changes response field names, update `run_questions.py` accordingly.
- Use `questions.json` to add or remove test cases without changing the script.
- If you want to extend the script, a good next step is to add a `question_type` or `dataset` field to `questions.json`.

## Troubleshooting

- `FileNotFoundError` for `tokens/access_token.txt`: ensure the token file exists and contains a valid token.
- `FileNotFoundError` for `questions.json`: make sure `questions.json` is present in the repo root.
- `httpx` errors: verify network access and that the API endpoint is reachable.
- No `output/genealogy_results.xlsx`: check that the script logged `✅ Execution complete` and that the `output/` directory is writable.
