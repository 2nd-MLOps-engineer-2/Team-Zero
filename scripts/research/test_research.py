"""Small regression checks for units, absent values, and non-destructive DDL extraction."""
import re
import unittest

from collect import ROOT, number
from enrich_official import require_checked
from load_mysql import qi


class ResearchChecks(unittest.TestCase):
    def test_exact_numbers_and_missing(self):
        self.assertEqual(number('1,234,567원'), '1234567')
        self.assertEqual(number('(17,127,003)'), '-17127003')
        self.assertEqual(number('45.98%'), '45.98')
        self.assertEqual(number('0'), '0')
        for value in ['-', 'N/A', '', None, 'NaN', 'Infinity', '1조 8,158억']:
            self.assertIsNone(number(value))

    def test_ddl_preserves_semicolon_in_comment(self):
        folder = ROOT / 'data/03_C_integration_20261014/03_model/ddl'
        statements = []
        for filename in ['02_silver.sql', '03_gold.sql']:
            statements.extend(re.findall(r'CREATE TABLE `\w+` \(.*?;(?=\r?\n|$)',
                              (folder / filename).read_text(encoding='utf-8-sig'), flags=re.S))
        self.assertEqual(len(statements), 19)
        self.assertTrue(all(s.rstrip().endswith("';") for s in statements))
        self.assertTrue(all('DROP TABLE' not in s for s in statements))

    def test_sql_identifiers(self):
        self.assertEqual(qi('tz_teamzero_research_20261016'), '`tz_teamzero_research_20261016`')
        for name in ['tz; DROP DATABASE mysql', 'a.b', '', '`root`']:
            with self.assertRaises(ValueError):
                qi(name)

    def test_changed_curated_source_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Official source changed'):
            require_checked(b'changed source', '0' * 64)


if __name__ == '__main__':
    unittest.main()
