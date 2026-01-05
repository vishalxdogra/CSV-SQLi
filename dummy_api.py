from flask import Flask, request, Response
import time

app = Flask(__name__)

@app.route("/api/export/users", methods=["GET"])
def users():
    user_id = request.args.get("id")
    sort = request.args.get("sort")

    # 🔴 HIGH RISK: unsafe ORDER BY simulation
    if sort and sort == "invalid_column":
        return Response("SQL ERROR: column does not exist", status=500)

    # 🔴 HIGH RISK: unsafe WHERE simulation
    if user_id and not user_id.isdigit():
        return Response("SQL ERROR: invalid input syntax", status=500)

    csv = "id,name\n1,Alice\n2,Bob\n"
    return Response(csv, mimetype="text/csv")


@app.route("/api/export/orders", methods=["GET"])
def orders():
    order_id = request.args.get("order_id")

    # 🔴 HIGH RISK: numeric SQL failure
    if order_id and not order_id.isdigit():
        return Response("Internal Server Error", status=500)

    csv = "order_id,total\n101,500\n102,300\n"
    return Response(csv, mimetype="text/csv")


@app.route("/api/export/sales", methods=["GET"])
def sales():
    order_by = request.args.get("order_by")

    # 🔴 HIGH RISK: ORDER BY crash
    if order_by == "invalid_column":
        time.sleep(4)  # simulate DB delay
        return Response("Internal Server Error", status=500)

    csv = "region,sales\nUS,1000\nEU,800\n"
    return Response(csv, mimetype="text/csv")


@app.route("/api/export/employees", methods=["GET"])
def employees():
    emp_id = request.args.get("employee_id")

    if emp_id and not emp_id.isdigit():
        return Response("SQL ERROR", status=500)

    csv = "id,name\n1,John\n2,Jane\n"
    return Response(csv, mimetype="text/csv")


@app.route("/api/export/payments", methods=["GET"])
def payments():
    acc = request.args.get("account_id")

    if acc and not acc.isdigit():
        return Response("Internal Server Error", status=500)

    csv = "account,amount\n10,200\n11,500\n"
    return Response(csv, mimetype="text/csv")


@app.route("/api/export/logs", methods=["GET"])
def logs():
    level = request.args.get("level")

    # 🔴 HIGH RISK: filter bypass
    if level == "invalid_enum_value":
        csv = "level,message\nINFO,All logs exposed\n"
        return Response(csv, mimetype="text/csv")

    csv = "level,message\nINFO,Normal log\n"
    return Response(csv, mimetype="text/csv")


if __name__ == "__main__":
    app.run(port=9090)