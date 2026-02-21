#!/usr/bin/env python
import logging
import os
import unittest

import pytest

import pdfplumber
from pdfplumber import table

logging.disable(logging.ERROR)

HERE = os.path.abspath(os.path.dirname(__file__))


class Test(unittest.TestCase):
    @classmethod
    def setup_class(self):
        path = os.path.join(HERE, "pdfs/pdffill-demo.pdf")
        self.pdf = pdfplumber.open(path)

    @classmethod
    def teardown_class(self):
        self.pdf.close()

    def test_orientation_errors(self):
        with pytest.raises(ValueError):
            table.join_edge_group([], "x")

    def test_table_settings_errors(self):
        with pytest.raises(ValueError):
            tf = table.TableFinder(self.pdf.pages[0], tuple())

        with pytest.raises(TypeError):
            tf = table.TableFinder(self.pdf.pages[0], {"strategy": "x"})
            tf.get_edges()

        with pytest.raises(ValueError):
            tf = table.TableFinder(self.pdf.pages[0], {"vertical_strategy": "x"})

        with pytest.raises(ValueError):
            tf = table.TableFinder(
                self.pdf.pages[0],
                {
                    "vertical_strategy": "explicit",
                    "explicit_vertical_lines": [],
                },
            )

        with pytest.raises(ValueError):
            tf = table.TableFinder(self.pdf.pages[0], {"join_tolerance": -1})
            tf.get_edges()

    def test_edges_strict(self):
        path = os.path.join(HERE, "pdfs/issue-140-example.pdf")
        with pdfplumber.open(path) as pdf:
            t = pdf.pages[0].extract_table(
                {
                    "vertical_strategy": "lines_strict",
                    "horizontal_strategy": "lines_strict",
                }
            )

        assert t[-1] == [
            "",
            "0085648100300",
            "CENTRAL KMA",
            "LILYS 55% DARK CHOC BAR",
            "415",
            "$ 0.61",
            "$ 253.15",
            "0.0000",
            "",
        ]

    def test_rows_and_columns(self):
        path = os.path.join(HERE, "pdfs/issue-140-example.pdf")
        with pdfplumber.open(path) as pdf:
            page = pdf.pages[0]
            table = page.find_table()
            row = [page.crop(bbox).extract_text() for bbox in table.rows[0].cells]
            assert row == [
                "Line no",
                "UPC code",
                "Location",
                "Item Description",
                "Item Quantity",
                "Bill Amount",
                "Accrued Amount",
                "Handling Rate",
                "PO number",
            ]
            col = [page.crop(bbox).extract_text() for bbox in table.columns[1].cells]
            assert col == [
                "UPC code",
                "0085648100305",
                "0085648100380",
                "0085648100303",
                "0085648100300",
            ]

    def test_explicit_desc_decimalization(self):
        """
        See issue #290
        """
        tf = table.TableFinder(
            self.pdf.pages[0],
            {
                "vertical_strategy": "explicit",
                "explicit_vertical_lines": [100, 200, 300],
                "horizontal_strategy": "explicit",
                "explicit_horizontal_lines": [100, 200, 300],
            },
        )
        assert tf.tables[0].extract()

    def test_text_tolerance(self):
        path = os.path.join(HERE, "pdfs/senate-expenditures.pdf")
        with pdfplumber.open(path) as pdf:
            bbox = (70.332, 130.986, 420, 509.106)
            cropped = pdf.pages[0].crop(bbox)
            t = cropped.extract_table(
                {
                    "horizontal_strategy": "text",
                    "vertical_strategy": "text",
                    "min_words_vertical": 20,
                }
            )
            t_tol = cropped.extract_table(
                {
                    "horizontal_strategy": "text",
                    "vertical_strategy": "text",
                    "min_words_vertical": 20,
                    "text_x_tolerance": 1,
                }
            )
            t_tol_from_tables = cropped.extract_tables(
                {
                    "horizontal_strategy": "text",
                    "vertical_strategy": "text",
                    "min_words_vertical": 20,
                    "text_x_tolerance": 1,
                }
            )[0]

        assert t[-1] == [
            "DHAW20190070",
            "09/09/2019",
            "CITIBANK-TRAVELCBACARD",
            "08/12/2019",
            "08/14/2019",
        ]
        assert t_tol[-1] == [
            "DHAW20190070",
            "09/09/2019",
            "CITIBANK - TRAVEL CBA CARD",
            "08/12/2019",
            "08/14/2019",
        ]
        assert t_tol[-1] == t_tol_from_tables[-1]

    def test_text_layout(self):
        path = os.path.join(HERE, "pdfs/issue-53-example.pdf")
        with pdfplumber.open(path) as pdf:
            table = pdf.pages[0].extract_table(
                {
                    "text_layout": True,
                }
            )
            assert table[3][0] == "   FY2013   \n   FY2014   "

    def test_text_without_words(self):
        assert table.words_to_edges_h([]) == []
        assert table.words_to_edges_v([]) == []

    def test_order(self):
        """
        See issue #336
        """
        path = os.path.join(HERE, "pdfs/issue-336-example.pdf")
        with pdfplumber.open(path) as pdf:
            tables = pdf.pages[0].extract_tables()
            assert len(tables) == 3
            assert len(tables[0]) == 8
            assert len(tables[1]) == 11
            assert len(tables[2]) == 2

    def test_issue_466_mixed_strategy(self):
        """
        See issue #466
        """
        path = os.path.join(HERE, "pdfs/issue-466-example.pdf")
        with pdfplumber.open(path) as pdf:
            tables = pdf.pages[0].extract_tables(
                {
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "text",
                    "snap_tolerance": 8,
                    "intersection_tolerance": 4,
                }
            )

            # The engine only extracts the tables which have drawn horizontal
            # lines.
            # For the 3 extracted tables, some common properties are expected:
            # - 4 rows
            # - 3 columns
            # - Data in last row contains the string 'last'
            for t in tables:
                assert len(t) == 4
                assert len(t[0]) == 3

                # Verify that all cell contain real data
                for cell in t[3]:
                    assert "last" in cell

    def test_discussion_539_null_value(self):
        """
        See discussion #539
        """
        path = os.path.join(HERE, "pdfs/nics-background-checks-2015-11.pdf")
        with pdfplumber.open(path) as pdf:
            page = pdf.pages[0]
            table_settings = {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "explicit_vertical_lines": [],
                "explicit_horizontal_lines": [],
                "snap_tolerance": 3,
                "join_tolerance": 3,
                "edge_min_length": 3,
                "min_words_vertical": 3,
                "min_words_horizontal": 1,
                "text_keep_blank_chars": False,
                "text_tolerance": 3,
                "intersection_tolerance": 3,
            }
            assert page.extract_table(table_settings)
            assert page.extract_tables(table_settings)

    def test_table_curves(self):
        # See https://github.com/jsvine/pdfplumber/discussions/808
        path = os.path.join(HERE, "pdfs/table-curves-example.pdf")
        with pdfplumber.open(path) as pdf:
            page = pdf.pages[0]
            assert len(page.curves)
            tables = page.extract_tables()
            assert len(tables) == 1
            t = tables[0]
            assert t[-2][-2] == "Uncommon"

            assert len(page.extract_tables({"vertical_strategy": "lines_strict"})) == 0


class TestExtendEdges(unittest.TestCase):
    """Tests for extend_h_edges, extend_v_edges, and extend_edges."""

    def _h_edge(self, x0, x1, top):
        return {
            "x0": x0,
            "x1": x1,
            "top": top,
            "bottom": top,
            "width": x1 - x0,
            "height": 0,
            "orientation": "h",
        }

    def _v_edge(self, x0, top, bottom):
        return {
            "x0": x0,
            "x1": x0,
            "top": top,
            "bottom": bottom,
            "width": 0,
            "height": bottom - top,
            "orientation": "v",
        }

    def test_extend_h_edges_basic(self):
        # Horizontal edge that doesn't reach the vertical edges
        h = [self._h_edge(20, 80, 50)]
        v = [self._v_edge(10, 0, 100), self._v_edge(90, 0, 100)]
        result = table.extend_h_edges(h, v, y_tolerance=1, x_tolerance=1)
        assert len(result) == 1
        assert result[0]["x0"] == 10
        assert result[0]["x1"] == 90
        assert result[0]["width"] == 80

    def test_extend_v_edges_basic(self):
        # Vertical edge that doesn't reach the horizontal edges
        v = [self._v_edge(50, 20, 80)]
        h = [self._h_edge(0, 100, 10), self._h_edge(0, 100, 90)]
        result = table.extend_v_edges(v, h, x_tolerance=1, y_tolerance=1)
        assert len(result) == 1
        assert result[0]["top"] == 10
        assert result[0]["bottom"] == 90
        assert result[0]["height"] == 80

    def test_no_shrinkage(self):
        # Edge already extends beyond perpendicular edges — should not shrink
        h = [self._h_edge(5, 95, 50)]
        v = [self._v_edge(10, 0, 100), self._v_edge(90, 0, 100)]
        result = table.extend_h_edges(h, v, y_tolerance=1, x_tolerance=1)
        assert result[0]["x0"] == 5
        assert result[0]["x1"] == 95

    def test_noop_when_already_intersecting(self):
        # Edges already span the full range — no change expected
        h = [self._h_edge(10, 90, 50)]
        v = [self._v_edge(10, 0, 100), self._v_edge(90, 0, 100)]
        result = table.extend_h_edges(h, v, y_tolerance=1, x_tolerance=1)
        assert result[0]["x0"] == 10
        assert result[0]["x1"] == 90

    def test_single_perpendicular_edge(self):
        # Only one vertical edge — should still extend toward it
        h = [self._h_edge(20, 80, 50)]
        v = [self._v_edge(10, 0, 100)]
        result = table.extend_h_edges(h, v, y_tolerance=1, x_tolerance=1)
        assert result[0]["x0"] == 10
        assert result[0]["x1"] == 80

    def test_only_overlapping_edges_considered(self):
        # Vertical edge outside y-range should be ignored
        h = [self._h_edge(20, 80, 50)]
        v_in = self._v_edge(10, 0, 100)  # overlaps y=50
        v_out = self._v_edge(5, 200, 300)  # does not overlap y=50
        result = table.extend_h_edges(h, [v_in, v_out], y_tolerance=1, x_tolerance=1)
        assert result[0]["x0"] == 10
        assert result[0]["x1"] == 80

    def test_extend_edges_combined(self):
        # Full round-trip through extend_edges
        # v_edges span y=0-100, h_edges at y=10 and y=90 — all overlap
        edges = [
            self._h_edge(20, 80, 10),
            self._h_edge(20, 80, 90),
            self._v_edge(10, 0, 100),
            self._v_edge(90, 0, 100),
        ]
        result = table.extend_edges(edges, x_tolerance=1, y_tolerance=1)
        h_results = [e for e in result if e["orientation"] == "h"]
        v_results = [e for e in result if e["orientation"] == "v"]
        assert len(h_results) == 2
        assert len(v_results) == 2
        for h in h_results:
            assert h["x0"] == 10
            assert h["x1"] == 90
        for v in v_results:
            assert v["top"] == 0
            assert v["bottom"] == 100

    def test_extend_edges_empty(self):
        assert table.extend_edges([], x_tolerance=1, y_tolerance=1) == []

    def test_extends_only_to_nearest(self):
        # Two v_edges outside h_edge reach on the right; should extend
        # only to the nearest one
        h = [self._h_edge(20, 80, 50)]
        v = [
            self._v_edge(10, 0, 100),  # left, unreachable
            self._v_edge(90, 0, 100),  # right, unreachable (nearest)
            self._v_edge(200, 0, 100),  # right, unreachable (farther)
        ]
        result = table.extend_h_edges(h, v, y_tolerance=1, x_tolerance=1)
        assert result[0]["x0"] == 10
        assert result[0]["x1"] == 90  # nearest right, not 200
