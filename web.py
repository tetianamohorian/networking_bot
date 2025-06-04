from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import csv
import io
from request_manager import DB_PATH

app = Flask(__name__)
app.secret_key = "TUKE_kokotina"

VALID_USERNAME = "admin"
VALID_PASSWORD = "TUKE_kokotina"


action_map = {
    "tutoring": "Doučovanie",
    "skuska": "Skúška",
    "work_1": "Práca 1",
    "work_2": "Práca 2",
    "problemset_1": "Problemset 1",
    "problemset_2": "Problemset 2",
    "problemset_3": "Problemset 3",
    "problemset_4": "Problemset 4",
    "problemset_5": "Problemset 5",
    "problemset_6": "Problemset 6",
    "problemset_7": "Problemset 7",
    "round_1": "Round 1",
    "round_2": "Round 2",
    "round_3": "Round 3",
    "pisomka_1": "Písomka 1",
    "pisomka_2_bozp": "Písomka 2 (BOZP)",
    "mechanicka": "Mechanická súčiastka",
    "elektronicka": "Elektronická schéma",
    "research": "Referát",
    "electroinstalacia": "Elektroinštalácia",
    "pisomka_2": "Písomka 2",
    "pisomka_3": "Písomka 3",
    "pisomka": "Písomná práca",
    "zadanie": "Zadanie",
    "zadanie_1": "Zadanie 1",
    "zadanie_2": "Zadanie 2",
    "zadanie_3": "Zadanie 3",
    "zadanie_4": "Zadanie 4",
    "zadanie_5": "Zadanie 5",
    "zadanie_6": "Zadanie 6",
    "zadanie_7": "Zadanie 7",
    "aktivita_1": "Aktivita 1",
    "aktivita_2": "Aktivita 2",
    "aktivita_3": "Aktivita 3",
    "referat": "Referát",
    "bonusova_uloha": "Bonusová úloha",
    "bonusova_uloha_1": "Bonusová úloha 1",
    "bonusova_uloha_2": "Bonusová úloha 2",
    "test": "Test",
    "projekt": "Projekt"
}


@app.route("/")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    status_filter = request.args.get("status")
    search_name = request.args.get("name")
    search_date = request.args.get("date")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM requests WHERE 1=1"
    params = []

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)

    if search_name:
        query += " AND taken_by LIKE ?"
        params.append(f"%{search_name}%")

    if search_date:
        query += " AND deadline LIKE ?"
        params.append(f"%{search_date}%")

    query += " ORDER BY id"
    cursor.execute(query, params)
    requests_list = cursor.fetchall()
    conn.close()

    return render_template("index.html",
                           requests=requests_list,
                           selected_status=status_filter,
                           search_name=search_name,
                           search_date=search_date,
                           action_map=action_map)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            error = "Nesprávne meno alebo heslo"
    return render_template("login.html", error=error)


@app.route("/export")
def export_csv():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests")
    rows = cursor.fetchall()
    header = [description[0] for description in cursor.description]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerows(rows)

    output.seek(0)
    return send_file(io.BytesIO(output.read().encode("utf-8")),
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name="requests_export.csv")

if __name__ == "__main__":
    app.run(debug=True)
