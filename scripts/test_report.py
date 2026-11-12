import csv
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
import report

BIN = report.ROOT/'cli/out/fairgrant_cli'

class ReviewTests(unittest.TestCase):
    def read(self, content):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'in.csv'; p.write_text(content)
            return report.read_rows(p)

    def test_csv_real_fe_pipeline(self):
        rows,digest=report.read_rows(report.ROOT/'examples/community-grants.csv')
        page,plan,risks=report.build(rows,digest,1000,100,BIN)
        self.assertEqual(plan['awards'],['300','400','300'])
        self.assertEqual(plan['unallocated'],'0')
        self.assertIn('Documentation',page)
        self.assertEqual(risks,[])

    def test_budget_decrease_visible(self):
        rows,digest=report.read_rows(report.ROOT/'examples/budget-risk.csv')
        page,_,risks=report.build(rows,digest,25,1,BIN)
        self.assertEqual(risks,[(25,26,3),(25,26,4)])
        self.assertIn('Budget increase reduces an award',page)
        self.assertIn('Team D: 3 → 2',page)

    def test_html_escaped_and_csv_formula_safe(self):
        rows,digest=self.read('name,weight,cap\n<script>alert(1)</script>,1,10\n')
        page,_,_=report.build(rows,digest,1,1,BIN)
        self.assertNotIn('<script>',page)
        self.assertIn('&lt;script&gt;',page)
        for name in ['=1+1','+SUM(A1)','-1','@SUM(A1)']:
            self.assertTrue(report.safe_cell(name).startswith("'"))

    def test_bad_csv(self):
        for text in ['name,cap,weight\nx,1,1\n','name,weight,cap\n',
                     'name,weight,cap\nx,1,2\nx,2,3\n',
                     'name,weight,cap\nx,1\n','name,weight,cap\nx,1,2,3\n',
                     'name,weight,cap\n,1,2\n','name,weight,cap\nx,-1,2\n',
                     'name,weight,cap\nx\u202e,1,2\n', 'name,weight,cap\nx\x7f,1,2\n',
                     'name,weight,cap\nx,1.5,2\n',
                     'name,weight,cap\n'+''.join(f'x{i},1,1\n' for i in range(17))]:
            with self.subTest(text=text), self.assertRaises(ValueError): self.read(text)

    def test_u128_budget_edges(self):
        rows=[('one',1,report.MAX)]
        for b in [0,report.MAX]:
            _,plan,risks=report.build(rows,'hash',b,report.MAX,BIN)
            self.assertEqual(plan['awards'],[str(b)])
            self.assertEqual(risks,[])
        for s in ['-1','+1','1.0','１２','',str(report.MAX+1),'0'*40]:
            with self.assertRaises(ValueError): report.integer(s)

    def test_export_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'result'
            command=['python3',str(report.ROOT/'scripts/report.py'),str(report.ROOT/'examples/budget-risk.csv'),'--budget','25','--out',str(output)]
            subprocess.run(command,check=True,capture_output=True)
            data=list(csv.DictReader(io.StringIO((output/'allocation.csv').read_text())))
            self.assertEqual([r['award'] for r in data],['7','7','4','3','3','1'])
            original=(output/'audit.json').read_bytes()
            self.assertEqual(subprocess.run(command,capture_output=True).returncode,2)
            self.assertEqual((output/'audit.json').read_bytes(),original)

if __name__ == '__main__': unittest.main()
