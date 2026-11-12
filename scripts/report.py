#!/usr/bin/env python3
"""CSV allocation review. All allocation decisions come from compiled Fe, never Python."""
import argparse
import csv
import hashlib
import html
import io
import json
from pathlib import Path
import subprocess
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
MAX = 2**128 - 1

def integer(value, maximum=MAX):
    if not value or not value.isascii() or not value.isdecimal() or len(value) > 39:
        raise ValueError('Amounts must be unsigned ASCII decimal integers (atomic units).')
    n = int(value)
    if n > maximum:
        raise ValueError('Amount exceeds its Fe integer range.')
    return n

def read_rows(path):
    data = Path(path).read_bytes()
    if len(data) > 32768:
        raise ValueError('CSV exceeds 32 KiB.')
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig')))
    if reader.fieldnames != ['name', 'weight', 'cap']:
        raise ValueError('CSV header must be exactly name,weight,cap in that order.')
    rows = []
    for r in reader:
        if None in r or any(v is None for v in r.values()):
            raise ValueError('Each row must contain exactly three fields.')
        name = r['name'].strip()
        if not name or len(name) > 120 or any(unicodedata.category(c) in ("Cc", "Cf") for c in name):
            raise ValueError('Name must have 1..120 characters without control characters.')
        if any(x[0] == name for x in rows):
            raise ValueError('Duplicate names are ambiguous; use unique recipient labels.')
        rows.append((name, integer(r['weight'], 2**64-1), integer(r['cap'])))
    if not 1 <= len(rows) <= 16:
        raise ValueError('Expected 1..16 recipients. Do not split larger groups into chunks.')
    return rows, hashlib.sha256(data).hexdigest()

def allocate(binary, budget, rows):
    command = [str(binary), str(budget)]
    for _, w, cap in rows:
        command += [str(w), str(cap)]
    p = subprocess.run(command, capture_output=True, text=True, timeout=10, check=True)
    result = json.loads(p.stdout)
    if len(result['awards']) != len(rows):
        raise ValueError('Unexpected Fe output length.')
    return result

def build(rows, digest, budget, delta, binary):
    budgets = sorted(set([max(0, budget-delta), budget, min(MAX, budget+delta)]))
    plans = {b: allocate(binary, b, rows) for b in budgets}
    decreases = [(lo, hi, i) for lo, hi in zip(budgets, budgets[1:]) for i in range(len(rows))
                 if int(plans[hi]['awards'][i]) < int(plans[lo]['awards'][i])]
    # No JavaScript, remote assets, tracking, or user input interpreted as markup.
    esc = html.escape
    body = ''
    for i, (name, weight, cap) in enumerate(rows):
        p = plans[budget]
        reason = 'ineligible (zero weight)' if not weight else 'zero capacity' if not cap else 'cap binding' if p['capped'][i] else 'largest-remainder +1' if p['rounded_up'][i] else 'proportional floor'
        cells = ''.join('<td>'+esc(plans[b]['awards'][i])+'</td>' for b in budgets)
        body += f'<tr><td>{i+1}</td><th scope="row">{esc(name)}</th><td>{weight}</td><td>{cap}</td>{cells}<td>{reason}</td></tr>'
    warnings = ''.join(f'<li>{esc(rows[i][0])}: {plans[lo]["awards"][i]} → {plans[hi]["awards"][i]} when budget increases {lo} → {hi}.</li>' for lo, hi, i in decreases)
    alert = '<div class="warning"><strong>Budget increase reduces an award</strong><ul>'+warnings+'</ul></div>' if warnings else '<p>No decrease in the sampled budgets. This does not prove budget monotonicity for other values.</p>'
    header = ''.join(f'<th scope="col">Budget {b}{" (selected)" if b==budget else ""}</th>' for b in budgets)
    footer = ''.join(f'<td>{plans[b]["unallocated"]}</td>' for b in budgets)
    report = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>FairGrant allocation review</title>
<style>body{{font:16px system-ui;margin:2rem auto;max-width:1100px;padding:0 1rem;color:#172c37;background:#f5faf8}}h1{{font-size:2.5rem}}table{{border-collapse:collapse;width:100%;background:white}}td,th{{padding:.7rem;text-align:left;border-bottom:1px solid #cad8d2}}.scroll{{overflow:auto}}.warning{{padding:1rem;background:#fff0ce;border:2px solid #9c6300}}code{{overflow-wrap:anywhere}}small{{display:block;margin:1rem 0}}a{{color:#075345}}</style>
<h1>FairGrant</h1><p>Allocation review · Fe-powered · no payments</p><h2>Decision before distribution</h2><p>Selected budget: <strong>{budget}</strong> atomic units. Recipient order is the tie-break rule; approve and freeze it before calculating. Weights and caps are policy inputs, not verified identities or contributions.</p>{alert}
<div class="scroll"><table><thead><tr><th>Order</th><th>Name</th><th>Weight</th><th>Cap</th>{header}<th>Selected-budget reason</th></tr></thead><tbody>{body}<tr><th colspan="4">Unallocated</th>{footer}<td>Do not distribute automatically</td></tr></tbody></table></div>
<h2>Reviewer checklist</h2><ul><li>Confirm unit, eligibility, weights and caps with the participants.</li><li>Confirm input order was fixed before seeing tie outcomes.</li><li>Review budget sensitivity before changing an approved budget.</li><li>Import CSV amount columns as TEXT: spreadsheets may silently round integers longer than 15 digits. This HTML and audit.json preserve exact decimal values. Exports contain labels only, not payment addresses.</li></ul>
<p>Hamilton rounding is not budget-monotone. This calculator is not for cumulative vesting, splitting large recipient groups, or automated payouts. Caps marked binding refer to the ideal allocation stage, not an award that merely rounds to its cap.</p>
<small>Input CSV SHA-256: <code>{digest}</code><br>Every displayed scenario was computed by the compiled Fe executable. No external resources are loaded. Inputs and outputs remain local unless you share these files. Keep real recipient details private.</small></html>'''
    return report, plans[budget], decreases

def safe_cell(value):
    # Guard spreadsheet formula injection in user-supplied names.
    return "'"+value if value.startswith(('=', '+', '-', '@')) else value

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--budget', required=True, type=integer)
    parser.add_argument('--delta', default=1, type=integer, help='Compare selected budget minus/plus this amount; not an exhaustive range')
    parser.add_argument('--out', type=Path, default=Path('review'))
    parser.add_argument('--binary', type=Path, default=ROOT/'cli/out/fairgrant_cli')
    args = parser.parse_args()
    try:
        rows, digest = read_rows(args.csv)
        report, plan, decreases = build(rows, digest, args.budget, args.delta, args.binary.resolve())
        if args.out.exists():
            raise ValueError('Output directory already exists; choose a new --out to preserve prior reviews.')
        args.out.mkdir(parents=True)
        (args.out/'index.html').write_text(report, encoding='utf-8')
        with (args.out/'allocation.csv').open('w',newline='',encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['order','name','weight','cap','award','capped','rounded_up'])
            for i,(name,w,c) in enumerate(rows):
                writer.writerow([i+1,safe_cell(name),w,c,plan['awards'][i],plan['capped'][i],plan['rounded_up'][i]])
        (args.out/'audit.json').write_text(json.dumps({'input_sha256':digest,'budget':str(args.budget),'delta':str(args.delta),'result':plan,'sampled_decreases':decreases},indent=2)+'\n')
        print(f'Review: {args.out}/index.html; CSV: {args.out}/allocation.csv; sampled decreases: {len(decreases)}')
    except (ValueError, OSError, subprocess.SubprocessError) as e:
        parser.exit(2, f'Cannot create review: {e}\n')

if __name__ == '__main__':
    main()
