"""Unit tests for pdf_generator.parsers."""

import unittest

from pdf_generator.parsers import (
    parse_policy_submitted_email,
    parse_graph_points,
    parse_summary_data,
    parse_data_to_html,
    ParseError,
)


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

SAMPLE_EMAIL = """\
Insured: John Doe
Policy #: NL-123456
Insurance Product: F & G - Everlast IUL
Beneficiary: Jane Doe
Face Amount: $500,000
Monthly Premium: $350.00
Monthly Draft: March 15, 2026
"""

SAMPLE_VALUES_TABLE = """\
Display Information

Initial Policy Information

Initial Face Amount\tModal Premium
$500,000\t$350.00
Minimum Premium (MMP)\tMEC Premium
$4,200.00\t$12,000.00

Values

Policy Year\tAge\tPremium Outlay\tAccumulated Value
1\t30\t$4,200.00\t$3,800.00
2\t31\t$4,200.00\t$8,100.00
3\t32\t$4,200.00\t$12,900.00
4\t33\t$4,200.00\t$18,200.00
5\t34\t$4,200.00\t$24,000.00
10\t39\t$4,200.00\t$55,000.00
20\t49\t$4,200.00\t$150,000.00
30\t59\t$4,200.00\t$320,000.00
40\t69\t$4,200.00\t$580,000.00
"""


# ---------------------------------------------------------------------------
# parse_policy_submitted_email tests
# ---------------------------------------------------------------------------

class TestParsePolicySubmittedEmail(unittest.TestCase):

    def test_valid_full_email(self):
        result = parse_policy_submitted_email(SAMPLE_EMAIL)
        self.assertIsNotNone(result)
        self.assertEqual(result["client_name"], "John Doe")
        self.assertEqual(result["policy_number"], "NL-123456")
        self.assertEqual(result["policy_type"], "F & G - Everlast IUL")
        self.assertEqual(result["carrier"], "F & G")
        self.assertEqual(result["beneficiary"], "Jane Doe")
        self.assertEqual(result["death_benefit"], "$500,000")
        self.assertIn("$350", result["monthly_premium"])
        self.assertEqual(result["effective_date"], "March 15, 2026")
        # Annual premium = 350 * 12 = 4200
        self.assertEqual(result["annual_premium"], "$4,200.00")

    def test_partial_email(self):
        text = "Insured: Alice Smith\nFace Amount: 250000"
        result = parse_policy_submitted_email(text)
        self.assertIsNotNone(result)
        self.assertEqual(result["client_name"], "Alice Smith")
        self.assertEqual(result["death_benefit"], "$250000")
        # Missing fields default to "—"
        self.assertEqual(result["beneficiary"], "—")
        self.assertEqual(result["annual_premium"], "—")

    def test_empty_input(self):
        self.assertIsNone(parse_policy_submitted_email(""))
        self.assertIsNone(parse_policy_submitted_email("   "))

    def test_garbage_input(self):
        self.assertIsNone(parse_policy_submitted_email("just some random text here"))

    def test_carrier_without_dash(self):
        text = "Insured: Bob\nInsurance Product: National Life\nFace Amount: $100,000"
        result = parse_policy_submitted_email(text)
        self.assertIsNotNone(result)
        self.assertEqual(result["carrier"], "National Life")


# ---------------------------------------------------------------------------
# parse_graph_points tests
# ---------------------------------------------------------------------------

class TestParseGraphPoints(unittest.TestCase):

    def test_valid_values_table(self):
        points = parse_graph_points(SAMPLE_VALUES_TABLE)
        self.assertIsInstance(points, list)
        self.assertGreater(len(points), 0)
        # Should pick standard horizons: 5, 10, 20, 30, 40
        years = [p["year"] for p in points]
        self.assertIn(5, years)
        self.assertIn(10, years)
        self.assertIn(40, years)
        # Check structure
        for p in points:
            self.assertIn("year", p)
            self.assertIn("premium_paid", p)
            self.assertIn("cash_value", p)

    def test_cumulative_premiums(self):
        points = parse_graph_points(SAMPLE_VALUES_TABLE)
        # Year 5: 5 * $4200 = $21,000 cumulative
        year5 = next(p for p in points if p["year"] == 5)
        self.assertAlmostEqual(year5["premium_paid"], 21000.0, places=0)
        self.assertAlmostEqual(year5["cash_value"], 24000.0, places=0)

    def test_empty_input(self):
        self.assertEqual(parse_graph_points(""), [])
        self.assertEqual(parse_graph_points("no values table here"), [])

    def test_no_matching_headers(self):
        text = "Year\tAge\tSomething\n1\t30\t$100"
        self.assertEqual(parse_graph_points(text), [])


# ---------------------------------------------------------------------------
# parse_summary_data tests
# ---------------------------------------------------------------------------

class TestParseSummaryData(unittest.TestCase):

    def test_valid_data(self):
        result = parse_summary_data(SAMPLE_VALUES_TABLE)
        self.assertIsNotNone(result)
        self.assertEqual(result["start_age"], 30)
        self.assertEqual(result["end_age"], 69)
        self.assertEqual(result["annual_premium"], 4200.0)
        self.assertEqual(result["last_year"], 40)
        self.assertAlmostEqual(result["last_cash"], 580000.0, places=0)
        # Total premiums = 9 rows * $4200 = $37,800
        self.assertAlmostEqual(result["total_premiums"], 37800.0, places=0)

    def test_breakeven_detection(self):
        result = parse_summary_data(SAMPLE_VALUES_TABLE)
        self.assertIsNotNone(result)
        # Cash value exceeds cumulative premiums at year 3
        # Year 1: cum=4200, cv=3800 (no)
        # Year 2: cum=8400, cv=8100 (no)
        # Year 3: cum=12600, cv=12900 (yes!)
        self.assertEqual(result["breakeven_year"], 3)
        self.assertEqual(result["breakeven_age"], 32)

    def test_empty_input(self):
        self.assertIsNone(parse_summary_data(""))
        self.assertIsNone(parse_summary_data("no data here"))

    def test_missing_age_column(self):
        # Without Age column, parse_summary_data should return None
        text = "Policy Year\tPremium Outlay\tAccumulated Value\n1\t$100\t$90"
        self.assertIsNone(parse_summary_data(text))


# ---------------------------------------------------------------------------
# parse_data_to_html tests
# ---------------------------------------------------------------------------

class TestParseDataToHtml(unittest.TestCase):

    def test_valid_data(self):
        html = parse_data_to_html(SAMPLE_VALUES_TABLE)
        self.assertIn("data-table", html)
        self.assertIn("<th>Policy Year</th>", html)
        self.assertIn("<th>Age</th>", html)
        # Check that data rows are present
        self.assertIn("$4,200.00", html)
        self.assertIn("$24,000.00", html)

    def test_initial_policy_info(self):
        html = parse_data_to_html(SAMPLE_VALUES_TABLE)
        self.assertIn("Initial Policy Information", html)
        self.assertIn("DEATH BENEFIT COVERAGE", html)
        self.assertIn("$500,000", html)

    def test_empty_input_raises(self):
        with self.assertRaises(ParseError):
            parse_data_to_html("")

    def test_whitespace_only_raises(self):
        with self.assertRaises(ParseError):
            parse_data_to_html("   \n   ")

    def test_stops_at_apitemplate_docs(self):
        text = SAMPLE_VALUES_TABLE + "\nAPITemplate.io\nShould not appear"
        html = parse_data_to_html(text)
        self.assertNotIn("Should not appear", html)


if __name__ == "__main__":
    unittest.main()
