
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timezone

import qrcode
import io
import base64

from flask import Flask, request, redirect, url_for, render_template_string
from web3 import Web3

ROOT = Path(__file__).resolve().parent
DB = ROOT / "pharma.db"
DEPLOYMENT_FILE = ROOT / "deployment.json"
RPC_URL = "http://127.0.0.1:8545"

app = Flask(__name__)

BASE_STYLES = """
<style>
  :root {
    color-scheme: light;
    --ink: #16313b;
    --muted: #667d84;
    --line: #dce9e8;
    --surface: #ffffff;
    --canvas: #f2f8f7;
    --teal: #087f76;
    --teal-dark: #06675f;
    --mint: #dff4ef;
    --blue: #edf5fb;
    --amber: #fff5df;
    --red: #fff0ed;
    --shadow: 0 18px 48px rgba(22, 49, 59, .08);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background:
      radial-gradient(ellipse at 85% 0%, rgba(196, 234, 224, .42), transparent 34rem),
      var(--canvas);
    color: var(--ink);
    font: 15px/1.6 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  a { color: var(--teal); text-decoration: none; }
  a:hover { color: var(--teal-dark); }
  .topbar {
    border-bottom: 1px solid rgba(220, 233, 232, .8);
    background: rgba(255, 255, 255, .86);
    backdrop-filter: blur(14px);
  }
  .nav, .page { width: min(1120px, calc(100% - 40px)); margin: 0 auto; }
  .nav { min-height: 76px; display: flex; align-items: center; justify-content: space-between; gap: 20px; }
  .brand { display: inline-flex; align-items: center; gap: 12px; color: var(--ink); font-size: 17px; font-weight: 800; letter-spacing: -.04em; }
  .brand-mark {
    width: 40px; height: 40px; display: grid; place-items: center; border-radius: 14px;
    color: white; background: linear-gradient(145deg, #16a394, #087269); box-shadow: 0 8px 18px rgba(8, 127, 118, .2);
    font-size: 21px;
  }
  .brand small { display: block; color: var(--muted); font-size: 10px; font-weight: 700; letter-spacing: .11em; text-transform: uppercase; }
  .nav-link { color: var(--muted); font-size: 13px; font-weight: 700; }
  .page { padding: 42px 0 72px; }
  .eyebrow { color: var(--teal); font-size: 11px; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
  h1, h2, h3, p { margin-top: 0; }
  h1 { margin-bottom: 12px; font-size: clamp(32px, 5vw, 48px); line-height: 1.08; letter-spacing: -.055em; }
  h2 { margin-bottom: 18px; font-size: 20px; letter-spacing: -.03em; }
  h3 { margin-bottom: 7px; font-size: 17px; letter-spacing: -.02em; }
  .lede { max-width: 620px; margin: 0; color: var(--muted); font-size: 16px; }
  .hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 28px; margin-bottom: 30px; }
  .hero-copy { max-width: 700px; }
  .card { border: 1px solid var(--line); border-radius: 20px; background: var(--surface); box-shadow: var(--shadow); }
  .card-pad { padding: 26px; }
  .button {
    display: inline-flex; align-items: center; justify-content: center; gap: 9px; min-height: 46px;
    padding: 0 19px; border: 0; border-radius: 12px; background: var(--teal); color: white;
    font: inherit; font-weight: 750; cursor: pointer; transition: transform .16s ease, background .16s ease, box-shadow .16s ease;
    box-shadow: 0 8px 18px rgba(8, 127, 118, .18);
  }
  .button:hover { color: white; background: var(--teal-dark); transform: translateY(-1px); box-shadow: 0 11px 22px rgba(8, 127, 118, .22); }
  .button-secondary { color: var(--teal); background: var(--mint); box-shadow: none; }
  .button-secondary:hover { color: var(--teal-dark); background: #d0eee7; box-shadow: none; }
  .metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 24px; }
  .metric { padding: 19px 22px; border: 1px solid var(--line); border-radius: 16px; background: rgba(255,255,255,.8); }
  .metric-value { display: block; margin-bottom: 3px; font-size: 24px; font-weight: 800; letter-spacing: -.04em; }
  .metric-label { color: var(--muted); font-size: 12px; font-weight: 700; }
  .section-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
  .section-heading h2 { margin: 0; }
  .batch-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }
  .batch-card { padding: 22px; transition: transform .18s ease, box-shadow .18s ease; }
  .batch-card:hover { transform: translateY(-3px); box-shadow: 0 22px 50px rgba(22, 49, 59, .12); }
  .batch-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; margin-bottom: 20px; }
  .batch-icon { display: grid; place-items: center; width: 42px; height: 42px; border-radius: 14px; background: var(--mint); font-size: 20px; }
  .batch-number { display: block; color: var(--muted); font-size: 12px; }
  .text-link { font-size: 13px; font-weight: 800; }
  .status-pill { display: inline-flex; align-items: center; gap: 7px; width: fit-content; padding: 6px 10px; border-radius: 99px; background: var(--mint); color: var(--teal-dark); font-size: 11px; font-weight: 800; }
  .status-pill::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
  .status-warning { color: #986709; background: var(--amber); }
  .status-error { color: #a44638; background: var(--red); }
  .empty-state { padding: 48px 24px; text-align: center; }
  .empty-icon { display: grid; place-items: center; width: 58px; height: 58px; margin: 0 auto 16px; border-radius: 18px; background: var(--mint); font-size: 26px; }
  .empty-state p { margin-bottom: 20px; color: var(--muted); }
  .form-card { max-width: 680px; margin: 0 auto; }
  .form-intro { padding: 28px 30px 0; }
  .form-body { padding: 24px 30px 30px; }
  .field { margin-bottom: 19px; }
  label { display: block; margin-bottom: 7px; color: var(--ink); font-size: 13px; font-weight: 750; }
  .field-hint { display: block; margin-top: 6px; color: var(--muted); font-size: 12px; }
  input, select {
    width: 100%; min-height: 48px; padding: 0 14px; border: 1px solid #cfdfde; border-radius: 11px;
    outline: none; background: #fbfdfd; color: var(--ink); font: inherit; transition: border .16s ease, box-shadow .16s ease;
  }
  input:focus, select:focus { border-color: var(--teal); box-shadow: 0 0 0 4px rgba(8, 127, 118, .11); }
  .form-actions { display: flex; align-items: center; gap: 16px; margin-top: 25px; }
  .back-link { font-size: 13px; font-weight: 750; }
  .medicine-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 22px; margin-bottom: 28px; }
  .medicine-meta { display: flex; flex-wrap: wrap; gap: 9px; margin-top: 20px; }
  .meta-chip { padding: 8px 12px; border: 1px solid var(--line); border-radius: 10px; background: white; color: var(--muted); font-size: 12px; }
  .meta-chip strong { color: var(--ink); }
  .detail-grid { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(300px, 1fr); gap: 18px; margin-bottom: 18px; }
  .qr-card { text-align: center; }
  .qr-frame { display: inline-grid; place-items: center; width: 100%; margin: 6px 0 12px; padding: 10px; border: 1px solid var(--line); border-radius: 16px; background: white; }
  .qr-frame img { display: block; width: min(100%, 720px); height: auto; }
  .muted { color: var(--muted); }
  .small-copy { margin: 0; color: var(--muted); font-size: 12px; }
  .audit-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 0; border-bottom: 1px solid #edf2f1; }
  .audit-row:last-child { border-bottom: 0; }
  .audit-label { color: var(--muted); font-size: 13px; }
  .event-list { display: grid; gap: 12px; }
  .event-card { position: relative; padding: 19px 20px 18px 24px; border: 1px solid var(--line); border-radius: 15px; background: white; }
  .event-card::before { content: ""; position: absolute; top: 21px; bottom: 21px; left: 0; width: 3px; border-radius: 0 4px 4px 0; background: #13a190; }
  .event-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 15px; }
  .event-location { margin: 3px 0 8px; color: var(--muted); }
  .event-time { color: var(--muted); font-size: 12px; }
  .hash { display: block; overflow-wrap: anywhere; margin-top: 8px; color: #75898e; font: 11px/1.5 ui-monospace, SFMono-Regular, Consolas, monospace; }
  .notice { padding: 15px 17px; border-radius: 13px; background: var(--blue); color: #45647a; font-size: 13px; }
  .notice-error { background: var(--amber); color: #75540c; }
  .page-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 22px; }
  .footer-note { margin-top: 42px; color: #91a3a6; text-align: center; font-size: 11px; }
  @media (max-width: 700px) {
    .nav, .page { width: min(100% - 28px, 560px); }
    .page { padding-top: 30px; }
    .hero, .medicine-head { align-items: flex-start; flex-direction: column; }
    .hero .button { width: 100%; }
    .metrics { grid-template-columns: 1fr; gap: 9px; }
    .metric { display: flex; align-items: center; justify-content: space-between; padding: 14px 17px; }
    .metric-value { margin: 0; }
    .detail-grid { grid-template-columns: 1fr; }
    .card-pad { padding: 21px; }
    .form-intro { padding: 24px 22px 0; }
    .form-body { padding: 20px 22px 24px; }
    .form-actions { align-items: stretch; flex-direction: column; }
    .form-actions .button { width: 100%; }
    .form-actions .back-link { text-align: center; }
    .event-top { flex-direction: column; }
  }
</style>
"""


def connect_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    with connect_db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                batch TEXT UNIQUE NOT NULL,
                manufacturer TEXT NOT NULL,
                expiry TEXT NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                location TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL
            )
        """)

        # Migrate existing databases without deleting old records.
        columns = {
            row["name"]
            for row in con.execute("PRAGMA table_info(events)").fetchall()
        }

        for name, sql_type in [
            ("tx_hash", "TEXT"),
            ("chain_hash", "TEXT"),
            ("block_number", "INTEGER"),
        ]:
            if name not in columns:
                con.execute(
                    f"ALTER TABLE events ADD COLUMN {name} {sql_type}"
                )


def blockchain():
    if not DEPLOYMENT_FILE.exists():
        raise RuntimeError(
            "deployment.json is missing. Compile and deploy the contract first."
        )

    deployment = json.loads(
        DEPLOYMENT_FILE.read_text(encoding="utf-8")
    )

    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 5}))

    if not w3.is_connected():
        raise RuntimeError(
            "Ganache is not running. Start it on port 8545."
        )

    configured_chain_id = deployment.get("chain_id")
    if configured_chain_id is not None and configured_chain_id != w3.eth.chain_id:
        raise RuntimeError(
            "The deployed contract belongs to a different blockchain network. "
            "Run python deploy.py to deploy it to the active Ganache network."
        )

    address = Web3.to_checksum_address(deployment["address"])
    if not w3.eth.get_code(address):
        raise RuntimeError(
            f"No contract was found at {address} on chain {w3.eth.chain_id}. "
            "Ganache may have been reset; run python deploy.py to deploy again."
        )

    contract = w3.eth.contract(
        address=address,
        abi=deployment["abi"],
    )

    account = Web3.to_checksum_address(deployment["deployer"])
    owner = Web3.to_checksum_address(contract.functions.owner().call())
    if owner != account:
        raise RuntimeError(
            "The configured deployer does not own the deployed contract. "
            "Run python deploy.py to deploy a contract for this network."
        )

    return w3, contract, account


def ensure_batch_registered(batch_id, w3, contract, account):
    with connect_db() as con:
        medicine = con.execute(
            "SELECT name, batch, manufacturer, expiry FROM medicines WHERE id = ?",
            (batch_id,),
        ).fetchone()

    if medicine is None:
        raise RuntimeError(f"Medicine batch {batch_id} was not found locally.")

    onchain = contract.functions.getBatch(batch_id).call()
    expected = (
        medicine["name"],
        medicine["batch"],
        medicine["manufacturer"],
        medicine["expiry"],
    )

    if onchain[4]:
        if tuple(onchain[:4]) != expected:
            raise RuntimeError(
                f"Blockchain batch ID {batch_id} is already registered "
                "with different medicine details."
            )
        return

    tx_hash = contract.functions.registerBatch(
        batch_id, *expected
    ).transact({"from": account})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status != 1:
        raise RuntimeError("Batch registration transaction failed.")

    registered = contract.functions.getBatch(batch_id).call()
    if not registered[4] or tuple(registered[:4]) != expected:
        raise RuntimeError(
            f"Blockchain registration could not be verified for batch {batch_id}."
        )






def generate_qr_code(data):
    import qrcode
    import base64
    from io import BytesIO
    from qrcode.constants import ERROR_CORRECT_L

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_L,
        box_size=18,
        border=4,
    )

    qr.add_data(data, optimize=0)

    try:
        qr.make(fit=True)
    except ValueError as exc:
        raise ValueError(
            "The complete traceability record exceeds the capacity of one "
            "standard QR code at error correction level L. No information "
            f"was removed ({len(data.encode('utf-8'))} UTF-8 bytes; "
            "maximum byte-mode capacity is 2,953 bytes). Use multiple QR "
            "codes or a smaller record."
        ) from exc

    # Convert the generated QR image into Base64 text for HTML.
    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return base64.b64encode(buffer.getvalue()).decode("ascii")


def local_hash(data):
    text = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def add_event(batch_id, status, location):
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with connect_db() as con:
        previous = con.execute("""
            SELECT event_hash FROM events
            WHERE batch_id = ?
            ORDER BY id DESC LIMIT 1
        """, (batch_id,)).fetchone()

        previous_hash = previous["event_hash"] if previous else "GENESIS"

    data = {
        "batch_id": batch_id,
        "status": status,
        "location": location,
        "timestamp": timestamp,
        "previous_hash": previous_hash,
    }

    # Restore a locally known batch if the current contract has lost its registration.
    w3, contract, account = blockchain()
    ensure_batch_registered(batch_id, w3, contract, account)

    # Submit a real transaction to the deployed smart contract.
    tx_hash = contract.functions.recordEvent(
        batch_id, status, location
    ).transact({"from": account})

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status != 1:
        raise RuntimeError("The blockchain event transaction failed.")

    count = contract.functions.getEventCount(batch_id).call()

    onchain_event = contract.functions.getEvent(
        batch_id, count - 1
    ).call()

    chain_hash = Web3.to_hex(onchain_event[5])
    event_hash = local_hash(data)

    with connect_db() as con:
        con.execute("""
            INSERT INTO events
            (batch_id, status, location, timestamp,
             previous_hash, event_hash, tx_hash,
             chain_hash, block_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id, status, location, timestamp,
            previous_hash, event_hash, tx_hash.hex(),
            chain_hash, receipt.blockNumber
        ))


def verify_local_chain(batch_id):
    with connect_db() as con:
        rows = con.execute("""
            SELECT status, location, timestamp,
                   previous_hash, event_hash
            FROM events WHERE batch_id = ?
            ORDER BY id
        """, (batch_id,)).fetchall()

    expected_previous = "GENESIS"

    for row in rows:
        data = {
            "batch_id": batch_id,
            "status": row["status"],
            "location": row["location"],
            "timestamp": row["timestamp"],
            "previous_hash": row["previous_hash"],
        }

        if row["previous_hash"] != expected_previous:
            return False

        if local_hash(data) != row["event_hash"]:
            return False

        expected_previous = row["event_hash"]

    return bool(rows)


def get_chain_status(batch_id):
    w3, contract, _ = blockchain()

    batch = contract.functions.getBatch(batch_id).call()
    count = contract.functions.getEventCount(batch_id).call()

    if not batch[4]:
        return {
            "connected": True,
            "registered": False,
            "count": 0,
            "events": [],
            "chain_id": w3.eth.chain_id,
        }

    chain_events = []

    for i in range(count):
        event = contract.functions.getEvent(batch_id, i).call()

        chain_events.append({
            "status": event[0],
            "location": event[1],
            "timestamp": datetime.fromtimestamp(
                event[2], timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "recorded_by": event[3],
            "previous_hash": Web3.to_hex(event[4]),
            "event_hash": Web3.to_hex(event[5]),
        })

    return {
        "connected": True,
        "registered": True,
        "count": count,
        "events": chain_events,
        "chain_id": w3.eth.chain_id,
    }


@app.route("/")
def home():
    with connect_db() as con:
        medicines = con.execute("""
            SELECT * FROM medicines ORDER BY id DESC
        """).fetchall()

    try:
        w3, _, _ = blockchain()
        chain_status = f"Connected · Chain ID {w3.eth.chain_id}"
    except Exception as error:
        chain_status = f"Unavailable: {error}"

    return render_template_string(BASE_STYLES + """
    <header class="topbar">
      <nav class="nav">
        <a class="brand" href="/"><span class="brand-mark">✚</span><span>PharmaTrace<small>Supply chain assurance</small></span></a>
        <a class="nav-link" href="/register">Register medicine&nbsp; →</a>
      </nav>
    </header>
    <main class="page">
      <section class="hero">
        <div class="hero-copy">
          <span class="eyebrow">Trusted medicine, verified journey</span>
          <h1>Pharmaceutical<br>traceability dashboard</h1>
          <p class="lede">Follow every batch from the manufacturing unit to the point of care, with records secured on blockchain.</p>
        </div>
        <a class="button" href="/register"><span>＋</span> Register medicine</a>
      </section>
      <section class="metrics" aria-label="Dashboard overview">
        <div class="metric"><span class="metric-label">Tracked batches</span><span class="metric-value">{{ medicines|length }}</span></div>
        <div class="metric"><span class="metric-label">Ledger network</span><span class="metric-value" style="font-size:16px">Ganache</span></div>
        <div class="metric">
          <span class="metric-label">Blockchain status</span>
          <span class="status-pill {{ 'status-error' if not chain_status.startswith('Connected') else '' }}">{{ 'Connected' if chain_status.startswith('Connected') else 'Unavailable' }}</span>
        </div>
      </section>
      <section>
        <div class="section-heading"><h2>Medicine batches</h2><span class="muted">{{ medicines|length }} total</span></div>
        {% if medicines %}
          <div class="batch-grid">
          {% for m in medicines %}
            <article class="card batch-card">
              <div class="batch-top">
                <span class="batch-icon">▤</span>
                <span class="status-pill">Traceable</span>
              </div>
              <h3>{{ m['name'] }}</h3>
              <span class="batch-number">Batch {{ m['batch'] }}</span>
              <a class="text-link" href="/medicine/{{ m['id'] }}">View full traceability&nbsp; →</a>
            </article>
          {% endfor %}
          </div>
        {% else %}
          <div class="card empty-state">
            <span class="empty-icon">✚</span>
            <h3>Your traceability workspace is ready</h3>
            <p>Register your first medicine batch to begin tracking its supply-chain journey.</p>
            <a class="button" href="/register">Register first batch&nbsp; →</a>
          </div>
        {% endif %}
      </section>
      <p class="footer-note">PharmaTrace · Transparent records for a safer supply chain</p>
    </main>
    """, medicines=medicines, chain_status=chain_status)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        batch = request.form.get("batch", "").strip()
        manufacturer = request.form.get("manufacturer", "").strip()
        expiry = request.form.get("expiry", "").strip()

        if not all([name, batch, manufacturer, expiry]):
            return "All fields are required.", 400

        try:
            # Reserve a local ID so it can also identify the on-chain batch.
            with connect_db() as con:
                cur = con.execute("""
                    INSERT INTO medicines (name, batch, manufacturer, expiry)
                    VALUES (?, ?, ?, ?)
                """, (name, batch, manufacturer, expiry))
                medicine_id = cur.lastrowid

            w3, contract, account = blockchain()

            tx_hash = contract.functions.registerBatch(
                medicine_id, name, batch, manufacturer, expiry
            ).transact({"from": account})

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status != 1:
                raise RuntimeError("Batch registration transaction failed.")

            add_event(
                medicine_id,
                "Manufactured",
                "Manufacturing Unit"
            )

        except sqlite3.IntegrityError:
            return "That batch number already exists. Use a unique batch number.", 400
        except Exception as error:
            # Do not leave a failed registration in SQLite.
            with connect_db() as con:
                con.execute(
                    "DELETE FROM medicines WHERE id = ?",
                    (locals().get("medicine_id", -1),)
                )
            return f"Registration failed: {error}", 500

        return redirect(url_for("medicine", medicine_id=medicine_id))

    return render_template_string(BASE_STYLES + """
    <header class="topbar">
      <nav class="nav">
        <a class="brand" href="/"><span class="brand-mark">✚</span><span>PharmaTrace<small>Supply chain assurance</small></span></a>
        <a class="nav-link" href="/">←&nbsp; Dashboard</a>
      </nav>
    </header>
    <main class="page">
      <section class="card form-card">
        <div class="form-intro">
          <span class="eyebrow">New record</span>
          <h1 style="font-size:36px;margin-top:9px">Register medicine</h1>
          <p class="lede" style="font-size:14px">Add the batch details to create its permanent traceability record.</p>
        </div>
        <form class="form-body" method="post">
          <div class="field">
            <label for="name">Medicine name</label>
            <input id="name" name="name" placeholder="e.g. Amoxicillin 500 mg" required>
          </div>
          <div class="field">
            <label for="batch">Batch number</label>
            <input id="batch" name="batch" placeholder="Enter a unique batch number" required>
            <span class="field-hint">Each batch number must be unique.</span>
          </div>
          <div class="field">
            <label for="manufacturer">Manufacturer</label>
            <input id="manufacturer" name="manufacturer" placeholder="Company or facility name" required>
          </div>
          <div class="field">
            <label for="expiry">Expiry date</label>
            <input id="expiry" type="date" name="expiry" required>
          </div>
          <div class="notice">The batch is registered on the blockchain and an initial manufacturing event is recorded.</div>
          <div class="form-actions">
            <button class="button" type="submit">Register on blockchain&nbsp; →</button>
            <a class="back-link" href="/">Cancel and return to dashboard</a>
          </div>
        </form>
      </section>
    </main>
    """)




def get_record_value(record, *field_names, default="Not available"):                        #QR CODE TEXT 
    """Read a field from a dictionary or a SQLite row safely."""
    try:
        available_fields = record.keys()
    except (AttributeError, TypeError):
        available_fields = []

    for field in field_names:
        if field in available_fields:
            value = record[field]
            if value is not None and str(value).strip():
                return str(value)

    if isinstance(record, dict):
        for field in field_names:
            value = record.get(field)
            if value is not None and str(value).strip():
                return str(value)

    return default



def build_traceability_text(medicine, events, chain_id=None):
    """Build a compact, lossless plain-text snapshot of all traceability data."""

    def clean(value):
        return json.dumps(str(value), ensure_ascii=True)[1:-1].replace(
            "|", "\\u007c"
        )

    def field(record, *names):
        return clean(get_record_value(record, *names))

    lines = [
        "PHARMACEUTICAL TRACEABILITY v1",
        "M|name|batch|manufacturer|expiry",
        "M|" + "|".join([
            field(medicine, "name", "medicine_name"),
            field(medicine, "batch_number", "batch_no", "batch", "batch_id"),
            field(medicine, "manufacturer"),
            field(medicine, "expiry_date", "expiry"),
        ]),
        "C|network|chain_id|total_events",
        "C|Local Ganache|"
        + (clean(chain_id) if chain_id is not None else "Not available")
        + f"|{len(events)}",
        "E|status|location|timestamp|previous_hash|event_hash|"
        "transaction_hash|block_number|recorded_by",
        'R|previous_hash "=" means the preceding event event_hash',
    ]

    for index, event in enumerate(events):
        previous_hash = get_record_value(event, "previous_hash")
        if index > 0 and previous_hash == get_record_value(
            events[index - 1], "event_hash"
        ):
            previous_hash = "="

        lines.append("E|" + "|".join([
            field(event, "status", "event_type", "event"),
            field(event, "location"),
            field(event, "timestamp"),
            clean(previous_hash),
            field(event, "event_hash"),
            field(event, "tx_hash", "transaction_hash"),
            field(event, "block_number"),
            field(event, "recorded_by"),
        ]))

    lines.append("N|Snapshot only; QR scanning does not prove medicine authenticity.")
    return "\n".join(lines)





@app.route("/medicine/<int:medicine_id>")
def medicine(medicine_id):
    with connect_db() as con:
        item = con.execute(
            "SELECT * FROM medicines WHERE id = ?",
            (medicine_id,)
        ).fetchone()

        if item is None:
            return "Medicine not found.", 404

        events = con.execute("""
            SELECT * FROM events WHERE batch_id = ?
            ORDER BY id
        """, (medicine_id,)).fetchall()
    
    try:
        chain = get_chain_status(medicine_id)
        chain_error = None
    except Exception as error:
        chain = None
        chain_error = str(error)

    chain_id = chain["chain_id"] if chain else None
    if chain_id is None and DEPLOYMENT_FILE.exists():
        try:
            deployment = json.loads(
                DEPLOYMENT_FILE.read_text(encoding="utf-8")
            )
            chain_id = deployment.get("chain_id")
        except (OSError, json.JSONDecodeError):
            chain_id = None

    chain_events = {
        event["event_hash"].lower(): event
        for event in chain["events"]
    } if chain else {}
    qr_events = []
    for event in events:
        qr_event = dict(event)
        chain_hash = qr_event.get("chain_hash")
        if chain_hash:
            chain_event = chain_events.get(str(chain_hash).lower())
            if chain_event:
                qr_event["recorded_by"] = chain_event["recorded_by"]
        qr_events.append(qr_event)

    qr_text = build_traceability_text(item, qr_events, chain_id=chain_id)
    qr_image = None
    qr_error = None
    try:
        qr_image = generate_qr_code(qr_text)
    except ValueError as error:
        qr_error = str(error)
    local_ok = verify_local_chain(medicine_id)

    return render_template_string(BASE_STYLES + """
    <header class="topbar">
      <nav class="nav">
        <a class="brand" href="/"><span class="brand-mark">✚</span><span>PharmaTrace<small>Supply chain assurance</small></span></a>
        <a class="nav-link" href="/">←&nbsp; All batches</a>
      </nav>
    </header>
    <main class="page">
      <section class="medicine-head">
        <div>
          <span class="eyebrow">Batch traceability record</span>
          <h1 style="margin-top:8px">{{ item['name'] }}</h1>
          <div class="medicine-meta">
            <span class="meta-chip"><strong>Batch</strong>&nbsp; {{ item['batch'] }}</span>
            <span class="meta-chip"><strong>Manufacturer</strong>&nbsp; {{ item['manufacturer'] }}</span>
            <span class="meta-chip"><strong>Expiry</strong>&nbsp; {{ item['expiry'] }}</span>
          </div>
        </div>
        <a class="button button-secondary" href="/medicine/{{ item['id'] }}/add-event">＋ Add supply-chain event</a>
      </section>

      <section class="detail-grid">
        <article class="card card-pad qr-card">
          <span class="eyebrow">Portable record</span>
          <h2 style="margin-top:8px">Scan for traceability</h2>
          {% if qr_image %}
            <div class="qr-frame">
              <img src="data:image/png;base64,{{ qr_image }}" alt="QR code containing the medicine traceability record as plain text">
            </div>
          {% else %}
            <p class="notice notice-error">{{ qr_error }}</p>
          {% endif %}
          <p class="small-copy">This code contains a plain-text snapshot, not a website link. Scanning alone does not prove medicine authenticity.</p>
        </article>

        <article class="card card-pad">
          <span class="eyebrow">Record integrity</span>
          <h2 style="margin-top:8px">Verification status</h2>
          <div class="audit-row">
            <span class="audit-label">Local SQLite audit</span>
            <span class="status-pill {{ '' if local_ok else 'status-error' }}">{{ 'VALID' if local_ok else 'FAILED / NO EVENTS' }}</span>
          </div>
          {% if chain %}
            <div class="audit-row">
              <span class="audit-label">Blockchain network</span>
              <span class="status-pill">Connected</span>
            </div>
            <div class="audit-row"><span class="audit-label">Network chain ID</span><strong>{{ chain['chain_id'] }}</strong></div>
            <div class="audit-row"><span class="audit-label">Batch registered on-chain</span><strong>{{ chain['registered'] }}</strong></div>
            <div class="audit-row"><span class="audit-label">On-chain event count</span><strong>{{ chain['count'] }}</strong></div>
          {% else %}
            <div class="notice notice-error" style="margin-top:16px">Blockchain unavailable: {{ chain_error }}</div>
          {% endif %}
        </article>
      </section>

      {% if chain and chain['events'] %}
        <section style="margin-bottom:26px">
          <div class="section-heading"><h2>Blockchain event history</h2><span class="muted">{{ chain['events']|length }} events</span></div>
          <div class="event-list">
          {% for e in chain['events'] %}
            <article class="event-card">
              <div class="event-top">
                <div><h3>{{ e['status'] }}</h3><p class="event-location">{{ e['location'] }}</p></div>
                <span class="status-pill">On-chain</span>
              </div>
              <span class="event-time">{{ e['timestamp'] }}</span>
              <span class="hash">Previous hash: {{ e['previous_hash'] }}</span>
              <span class="hash">Event hash: {{ e['event_hash'] }}</span>
              <span class="hash">Recorded by: {{ e['recorded_by'] }}</span>
            </article>
          {% endfor %}
          </div>
        </section>
      {% endif %}

      <section>
        <div class="section-heading"><h2>SQLite event history</h2><span class="muted">{{ events|length }} events</span></div>
        {% if events %}
          <div class="event-list">
          {% for e in events %}
            <article class="event-card">
              <div class="event-top">
                <div><h3>{{ e['status'] }}</h3><p class="event-location">{{ e['location'] }}</p></div>
                <span class="status-pill">Recorded</span>
              </div>
              <span class="event-time">{{ e['timestamp'] }}</span>
              <span class="hash">Transaction: {{ e['tx_hash'] or 'Not recorded' }}</span>
              <span class="hash">Block: {{ e['block_number'] or 'Not recorded' }}</span>
            </article>
          {% endfor %}
          </div>
        {% else %}
          <div class="card empty-state"><p>No local events have been recorded for this batch.</p></div>
        {% endif %}
      </section>
      <div class="page-actions">
        <a class="button" href="/medicine/{{ item['id'] }}/add-event">＋ Add supply-chain event</a>
        <a class="button button-secondary" href="/">← Back to dashboard</a>
      </div>
    </main>
    """, item=item, events=events, local_ok=local_ok,
         chain=chain, chain_error=chain_error, qr_image=qr_image,
         qr_error=qr_error)


@app.route("/medicine/<int:medicine_id>/add-event",
           methods=["GET", "POST"])
def add_supply_event(medicine_id):
    with connect_db() as con:
        item = con.execute(
            "SELECT id FROM medicines WHERE id = ?",
            (medicine_id,)
        ).fetchone()

    if item is None:
        return "Medicine not found.", 404

    if request.method == "POST":
        status = request.form.get("status", "").strip()
        location = request.form.get("location", "").strip()

        if not status or not location:
            return "Both fields are required.", 400

        try:
            add_event(medicine_id, status, location)
        except Exception as error:
            return f"Blockchain transaction failed: {error}", 500

        return redirect(url_for("medicine", medicine_id=medicine_id))

    return render_template_string(BASE_STYLES + """
    <header class="topbar">
      <nav class="nav">
        <a class="brand" href="/"><span class="brand-mark">✚</span><span>PharmaTrace<small>Supply chain assurance</small></span></a>
        <a class="nav-link" href="/medicine/{{ medicine_id }}">←&nbsp; Batch record</a>
      </nav>
    </header>
    <main class="page">
      <section class="card form-card">
        <div class="form-intro">
          <span class="eyebrow">Batch movement</span>
          <h1 style="font-size:36px;margin-top:9px">Add supply-chain event</h1>
          <p class="lede" style="font-size:14px">Record the next verified step in this medicine's journey.</p>
        </div>
        <form class="form-body" method="post">
          <div class="field">
            <label for="status">Event status</label>
            <select id="status" name="status" required>
              <option>Dispatched to Distributor</option>
              <option>Received by Distributor</option>
              <option>Dispatched to Pharmacy</option>
              <option>Received by Pharmacy</option>
              <option>Delivered to Customer</option>
              <option>Quality Inspection Passed</option>
            </select>
          </div>
          <div class="field">
            <label for="location">Location</label>
            <input id="location" name="location" placeholder="City, facility, or distribution point" required>
          </div>
          <div class="notice">This event will be written to the blockchain and added to the batch's audit history.</div>
          <div class="form-actions">
            <button class="button" type="submit">Record blockchain transaction&nbsp; →</button>
            <a class="back-link" href="/medicine/{{ medicine_id }}">Return to batch record</a>
          </div>
        </form>
      </section>
    </main>
    """, medicine_id=medicine_id)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
