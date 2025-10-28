import os, tempfile, subprocess, sys
from flask import Flask, render_template_string, request, send_file, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this")

HTML = """
<!doctype html><meta name=viewport content="width=device-width, initial-scale=1">
<title>FamilySearch → GEDCOM</title>
<h2>Exportar árbol desde FamilySearch a GEDCOM</h2>
<form method="post">
  <label>Usuario FamilySearch</label><br>
  <input name="username" required><br><br>
  <label>Contraseña</label><br>
  <input name="password" type="password" required><br><br>
  <label>ID persona inicial (ej. KWHC-XYZ)</label><br>
  <input name="person_id"><br><br>
  <label>Ancestros</label>
  <input name="gens_up" type="number" min="1" value="8" style="width:5em;">
  &nbsp; <label>Descendientes</label>
  <input name="gens_down" type="number" min="0" value="2" style="width:5em;"><br><br>
  <label><input type="checkbox" name="include_sources" checked> Incluir fuentes/citas</label><br><br>
  <button type="submit">Generar GEDCOM</button>
</form>
{% with m=get_flashed_messages() %}{% if m %}<p style="color:#c00">{{m[0]}}</p>{% endif %}{% endwith %}
"""

def run_getmyancestors(username, password, person_id, gens_up, gens_down, include_sources):
    fd, out_path = tempfile.mkstemp(prefix="fs_", suffix=".ged")
    os.close(fd)
    cmd = [sys.executable, "-m", "getmyancestors.getmyancestors",
           "-u", username, "-p", password,
           "-o", out_path,
           "-a", str(gens_up), "-d", str(gens_down)]
    if person_id:
        cmd += ["-i", person_id]
    if not include_sources:
        cmd += ["--no-sources"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        try: os.remove(out_path)
        except: pass
        msg = (p.stderr or p.stdout or "Error desconocido").strip()
        raise RuntimeError(msg)
    return out_path

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        u = request.form.get("username","").strip()
        pw = request.form.get("password","").strip()
        pid = request.form.get("person_id","").strip()
        try:
            a = int(request.form.get("gens_up","8") or 8)
            d = int(request.form.get("gens_down","2") or 2)
        except:
            flash("Generaciones inválidas.")
            return redirect(url_for("index"))
        inc = request.form.get("include_sources") == "on"
        if not u or not pw:
            flash("Usuario y contraseña son obligatorios.")
            return redirect(url_for("index"))
        try:
            out_path = run_getmyancestors(u, pw, pid, a, d, inc)
            return send_file(out_path, as_attachment=True, download_name="familysearch_tree.ged")
        except Exception as e:
            flash(f"Fallo: {e}")
            return redirect(url_for("index"))
    return render_template_string(HTML)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
