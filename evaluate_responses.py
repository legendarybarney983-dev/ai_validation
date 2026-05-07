import json
import os
import sys
import pandas as pd

from openai import OpenAI


# =========================================================
# CONFIG
# =========================================================

RESPONSES_FILE = "output/responses.json"
GROUND_TRUTH_FILE = "ground_truth.json"
EXCEL_FILE = "output/genealogy_results.xlsx"

MODEL_NAME = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"

client = OpenAI(
    base_url="http://172.16.90.32:8001/v1",
    api_key="dummy"
)


# =========================================================
# LOAD JSON FILE
# =========================================================

def load_json_file(filepath):

    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"File not found: {filepath}"
        )

    try:
        with open(filepath, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError(
                f"{filepath} must contain a JSON array"
            )

        return data

    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in {filepath}: {e}"
        )


# =========================================================
# VALIDATE IDS
# =========================================================

def validate_ids(responses, ground_truths):

    response_ids = {r["id"] for r in responses}
    gt_ids = {g["id"] for g in ground_truths}

    missing_in_gt = response_ids - gt_ids
    missing_in_response = gt_ids - response_ids

    if missing_in_gt:
        raise ValueError(
            f"IDs missing in ground_truth.json: "
            f"{missing_in_gt}"
        )

    if missing_in_response:
        raise ValueError(
            f"IDs missing in responses.json: "
            f"{missing_in_response}"
        )


# =========================================================
# BUILD LOOKUP
# =========================================================

def build_lookup(data, value_key):

    lookup = {}

    for item in data:

        if "id" not in item:
            raise ValueError(
                f"Missing 'id' field in JSON item: {item}"
            )

        if value_key not in item:
            raise ValueError(
                f"Missing '{value_key}' field "
                f"in JSON item: {item}"
            )

        lookup[item["id"]] = item[value_key]

    return lookup


# =========================================================
# CALL LLM
# =========================================================

def evaluate_queries(ground_truth, response):

    prompt = f"""
You are evaluating Cypher query generation.

GROUND TRUTH QUERY:
{ground_truth}

GENERATED QUERY:
{response}

Definitions:

TP:
Generated query is logically equivalent to the ground truth query.

FP:
Generated query returns incorrect or unrelated information.

FN:
Generated query misses the intended logic of the ground truth query.

TN:
Not applicable in most Cypher evaluations.

Compare the logical meaning of both queries.
Allow small syntactic differences.

Return ONLY valid JSON.

Format:
{{
    "classification": "TP"
}}

Possible values:
TP
FP
FN
TN
"""

    try:

        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        content = (
            completion
            .choices[0]
            .message
            .content
            .strip()
        )

        # Extract JSON safely
        start = content.find("{")
        end = content.rfind("}") + 1

        if start == -1 or end == 0:
            raise ValueError(
                "No JSON object found in model response"
            )

        json_text = content[start:end]

        parsed = json.loads(json_text)

        if "classification" not in parsed:
            raise ValueError(
                "Missing 'classification' key"
            )

        classification = (
            parsed["classification"]
            .strip()
            .upper()
        )

        if classification not in [
            "TP",
            "FP",
            "FN",
            "TN"
        ]:
            raise ValueError(
                f"Invalid classification: "
                f"{classification}"
            )

        return {
            "classification": classification
        }

    except Exception as e:

        print(f"⚠ Evaluation failed: {e}")

        return {
            "classification": "FP"
        }


# =========================================================
# CALCULATE METRICS
# =========================================================

def calculate_metrics(tp, fp, fn, tn):

    total = tp + fp + fn + tn

    accuracy = (
        (tp + tn) / total
        if total > 0 else 0
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0 else 0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0 else 0
    )

    f1 = (
        (2 * precision * recall) /
        (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    return {
        "Accuracy": round(accuracy * 100, 2),
        "Precision": round(precision * 100, 2),
        "Recall": round(recall * 100, 2),
        "F1 Score": round(f1 * 100, 2)
    }


# =========================================================
# MAIN
# =========================================================

def run():

    try:

        # -----------------------------------------
        # Load files
        # -----------------------------------------

        responses = load_json_file(
            RESPONSES_FILE
        )

        ground_truths = load_json_file(
            GROUND_TRUTH_FILE
        )

        # -----------------------------------------
        # Validate IDs
        # -----------------------------------------

        validate_ids(
            responses,
            ground_truths
        )

        # -----------------------------------------
        # Build lookup dictionaries
        # -----------------------------------------

        response_lookup = build_lookup(
            responses,
            "response"
        )

        gt_lookup = build_lookup(
            ground_truths,
            "ground_truth"
        )

        evaluation_rows = []

        total_tp = 0
        total_fp = 0
        total_fn = 0
        total_tn = 0

        # -----------------------------------------
        # Evaluate
        # -----------------------------------------

        for query_id in response_lookup:

            print(f"▶ Evaluating {query_id}")

            gt_query = gt_lookup[query_id]
            response_query = response_lookup[query_id]

            result = evaluate_queries(
                gt_query,
                response_query
            )

            classification = result[
                "classification"
            ]

            tp = 1 if classification == "TP" else 0
            fp = 1 if classification == "FP" else 0
            fn = 1 if classification == "FN" else 0
            tn = 1 if classification == "TN" else 0

            total_tp += tp
            total_fp += fp
            total_fn += fn
            total_tn += tn

            evaluation_rows.append({
                "id": query_id,
                "classification": classification,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn
            })

        # -----------------------------------------
        # Create DataFrames
        # -----------------------------------------

        evaluation_df = pd.DataFrame(
            evaluation_rows
        )

        metrics = calculate_metrics(
            total_tp,
            total_fp,
            total_fn,
            total_tn
        )

        metrics_df = pd.DataFrame([
            {
                "Metric": key,
                "Value": value
            }
            for key, value in metrics.items()
        ])

        confusion_df = pd.DataFrame([
            {
                "TP": total_tp,
                "FP": total_fp,
                "FN": total_fn,
                "TN": total_tn
            }
        ])

        # -----------------------------------------
        # Save to Excel
        # -----------------------------------------

        if not os.path.exists(EXCEL_FILE):
            raise FileNotFoundError(
                f"Excel file not found: "
                f"{EXCEL_FILE}"
            )

        with pd.ExcelWriter(
            EXCEL_FILE,
            engine="openpyxl",
            mode="a",
            if_sheet_exists="replace"
        ) as writer:

            evaluation_df.to_excel(
                writer,
                sheet_name="Evaluation",
                index=False
            )

            confusion_df.to_excel(
                writer,
                sheet_name="Confusion_Matrix",
                index=False
            )

            metrics_df.to_excel(
                writer,
                sheet_name="Metrics",
                index=False
            )

        # -----------------------------------------
        # Print Summary
        # -----------------------------------------

        print("\n✅ Evaluation Complete")

        print("\nConfusion Matrix")
        print(confusion_df)

        print("\nMetrics")
        print(metrics_df)

    except FileNotFoundError as e:

        print(f"\n❌ File Error: {e}")
        sys.exit(1)

    except ValueError as e:

        print(f"\n❌ Validation Error: {e}")
        sys.exit(1)

    except Exception as e:

        print(f"\n❌ Unexpected Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()