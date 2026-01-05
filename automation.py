import csv
import time
import requests
from urllib.parse import urlencode
from config import BASE_URL, REQUEST_TIMEOUT, TIME_DIFF_THRESHOLD, MAX_STRING_SIZE

# =====================================
# PARAMETER TYPE INFERENCE
# =====================================
def infer_type(param):
    p = param.lower()

    if p.endswith("id"):
        return "number"
    if "date" in p or "from" in p or "to" in p:
        return "date"
    if p in ["status", "type", "state"]:
        return "enum"
    if p in ["sort", "order", "order_by"]:
        return "identifier"
    return "string"


# =====================================
# SAFE TYPE-BASED MUTATIONS
# =====================================
def mutate_value(param_type):
    if param_type == "number":
        return "abc"                     # breaks numeric type
    if param_type == "date":
        return "2024-99-99"              # invalid date
    if param_type == "enum":
        return "invalid_enum_value"
    if param_type == "identifier":
        return "invalid_column"
    return "X" * MAX_STRING_SIZE         # oversized string


# =====================================
# VALID BASELINE VALUES
# =====================================
def valid_value(param_type):
    if param_type == "number":
        return "1"
    if param_type == "date":
        return "2024-01-01"
    if param_type == "enum":
        return "active"
    if param_type == "identifier":
        return "id"
    return "test"


# =====================================
# SEND HTTP REQUEST
# =====================================
def send_request(endpoint, params):
    url = BASE_URL + endpoint
    query_string = urlencode(params)
    full_url = f"{url}?{query_string}"

    start = time.time()
    try:
        response = requests.get(full_url, timeout=REQUEST_TIMEOUT)
        elapsed = time.time() - start
        
        return {
            "status": response.status_code,
            "time": elapsed,
            "size": len(response.text), # Count bytes, not lines
            "body": response.text,
            "error": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": 0,
            "time": 0,
            "size": 0,
            "body": "",
            "error": str(e)
        }


# =====================================
# MAIN AUTOMATION LOGIC
# =====================================
def run_automation():
    findings = []

    try:
        with open("apis.csv", newline="") as file:
            reader = csv.DictReader(file)
            
            # Convert reader to list to safely iterate
            rows = list(reader)
            if not rows:
                print("[!] apis.csv is empty.")
                return

            for row in rows:
                endpoint = row["endpoint"]
                # Handle cases where params might be empty
                if not row["params"]:
                    print(f"[!] Skipping {endpoint}: No parameters defined.")
                    continue
                    
                params = row["params"].split("|")

                print(f"\n[+] Testing API: {endpoint}")

                # Infer parameter types
                param_types = {p: infer_type(p) for p in params}

                # -------------------------
                # BASELINE REQUEST
                # -------------------------
                baseline_params = {
                    p: valid_value(param_types[p]) for p in params
                }

                baseline = send_request(endpoint, baseline_params)

                if baseline["error"]:
                    print(f"    [!] Baseline failed: {baseline['error']}")
                    continue

                print(f"    Baseline: {baseline['status']} | Size: {baseline['size']} bytes")

                # -------------------------
                # PARAMETER MUTATION LOOP
                # -------------------------
                for param in params:
                    test_params = baseline_params.copy()
                    test_params[param] = mutate_value(param_types[param])

                    test = send_request(endpoint, test_params)

                    issues = []

                    # 1. Connection Error Check
                    if test["error"]:
                        issues.append(f"Request failed: {test['error']}")
                    
                    else:
                        # 2. Status Code Check (Server Errors)
                        if test["status"] >= 500:
                            issues.append(f"Server Error ({test['status']})")

                        # 3. Time Anomaly Check
                        if abs(test["time"] - baseline["time"]) > TIME_DIFF_THRESHOLD:
                            issues.append(f"Time Anomaly ({test['time']:.2f}s vs {baseline['time']:.2f}s)")

                        # 4. Response Size Anomaly (The Fix)
                        # Detect if size changed by more than 10%
                        size_diff = abs(test["size"] - baseline["size"])
                        if baseline["size"] > 0:
                            percent_diff = (size_diff / baseline["size"]) * 100
                        else:
                            percent_diff = 100 if size_diff > 0 else 0

                        if percent_diff > 10:
                            issues.append(f"Size Anomaly (Changed by {percent_diff:.1f}%)")

                    if issues:
                        print(f"    [!] Issue found in '{param}': {', '.join(issues)}")
                        findings.append({
                            "endpoint": endpoint,
                            "parameter": param,
                            "type": param_types[param],
                            "issues": ", ".join(issues)
                        })

        generate_report(findings)

    except FileNotFoundError:
        print("[!] Error: 'apis.csv' file not found in the same directory.")


# =====================================
# REPORT GENERATION
# =====================================
def generate_report(findings):
    with open("report.txt", "w") as report:
        report.write("SQLi TYPE-BASED AUTOMATION REPORT\n")
        report.write("=" * 40 + "\n\n")

        if not findings:
            report.write("No potential SQL Injection risks detected.\n")
            print("\n[✓] No potential SQL Injection risks detected.")
            return

        for f in findings:
            report.write(
                f"API: {f['endpoint']}\n"
                f"Parameter: {f['parameter']}\n"
                f"Expected Type: {f['type']}\n"
                f"Issues: {f['issues']}\n"
                f"{'-'*30}\n"
            )

    print("\n[!] Potential issues detected. See report.txt")


# =====================================
# ENTRY POINT
# =====================================
if __name__ == "__main__":
    run_automation()