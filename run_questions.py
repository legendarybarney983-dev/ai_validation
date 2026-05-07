import json
import time
import httpx
import pandas as pd
import os
import sys
import warnings

API_URL = "https://ai360.dev.mareana.com/v1/ai-360/genealogy/query"


def load_token():
    token_file = "tokens/access_token.txt"

    if not os.path.exists(token_file):
        raise FileNotFoundError(f"Token file not found: {token_file}")

    with open(token_file) as f:
        token = f.read().strip()

    if not token:
        raise ValueError("Token file is empty")

    return token


def load_questions():
    questions_file = "questions.json"

    if not os.path.exists(questions_file):
        raise FileNotFoundError(
            f"Questions file not found: {questions_file}"
        )

    with open(questions_file) as f:
        return json.load(f)


def ensure_output_dir():
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)


def save_responses_json(results):
    """
    Create responses.json in required format:
    [
        {
            "id": "GQ-01",
            "response": "MATCH ..."
        }
    ]
    """

    responses = []

    for r in results:
        responses.append({
            "id": r["question_id"],
            "response": r["cypher_query"]
        })

    with open("output/responses.json", "w") as f:
        json.dump(responses, f, indent=4)

    print("✅ responses.json created")


def run():

    try:
        ensure_output_dir()

        token = load_token()

        headers = {
            "Content-Type": "application/json",
            "x-access-token": token
        }

        results = []

        questions = load_questions()

        for q in questions:

            payload = {
                "question": q["question"],
                "max_retries": 2,
                "session_id": f"session_{int(time.time())}",
                "user_id": "sharan",
                "use_memory": True,
                "execute_query": True,
                "generate_summary": True
            }

            print(f"▶ Running {q['id']}")

            try:

                response = httpx.post(
                    API_URL,
                    json=payload,
                    headers=headers,
                    timeout=300
                )

                if response.status_code >= 400:
                    print(
                        f"  ⚠️ API returned status "
                        f"{response.status_code}"
                    )

                response_json = (
                    response.json()
                    if response.text
                    else None
                )

                # Default values
                cypher_query = None
                sql_query = None
                summary = None
                classification = None
                intent = None
                is_valid = None
                is_safe = None

                # Extract fields
                if (
                    response_json and
                    isinstance(response_json, dict)
                ):

                    cypher_query = response_json.get("query")
                    sql_query = response_json.get("sql_query")
                    summary = response_json.get("summary")
                    classification = response_json.get(
                        "classification"
                    )
                    intent = response_json.get("intent")
                    is_valid = response_json.get("is_valid")
                    is_safe = response_json.get("is_safe")

                # Store results
                results.append({
                    "question_id": q["id"],
                    "question": q["question"],
                    "cypher_query": cypher_query,
                    "sql_query": sql_query,
                    "summary": summary,
                    "classification": classification,
                    "intent": intent,
                    "is_valid": is_valid,
                    "is_safe": is_safe,
                    "status_code": response.status_code,
                    "response": response_json
                })

                print(f"  ✓ Status {response.status_code}")

            except httpx.RequestError as e:

                print(f"  ✗ Request failed: {e}")

                results.append({
                    "question_id": q["id"],
                    "question": q["question"],
                    "cypher_query": None,
                    "sql_query": None,
                    "summary": None,
                    "classification": None,
                    "intent": None,
                    "is_valid": None,
                    "is_safe": None,
                    "status_code": None,
                    "response": {"error": str(e)}
                })

            time.sleep(1)

        # =========================
        # SAVE EXCEL
        # =========================

        pd.DataFrame(results).to_excel(
            "output/genealogy_results.xlsx",
            index=False
        )

        print("✅ genealogy_results.xlsx created")

        # =========================
        # SAVE responses.json
        # =========================

        save_responses_json(results)

        print("✅ Execution complete")

        return results

    except FileNotFoundError as e:

        print(f"❌ File error: {e}", file=sys.stderr)
        sys.exit(1)

    except ValueError as e:

        print(
            f"❌ Configuration error: {e}",
            file=sys.stderr
        )
        sys.exit(1)

    except Exception as e:

        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()