"""Dialogue de ponderation — Configuration du calcul des notes.

Templates PEI (4/3/2/1 criteres, bandes IB) et DP (standard, simple, personnalise).
L'utilisateur ne voit JAMAIS le JSON. Tout est visuel.
"""
from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from common.calc_engine import CalcEngine
from common.database import db
from common.session import session
from larccommon.design_system import ds
from larccommon.theme import theme_manager
from larccommon.safe_slot import safe_slot


class WeightDialog(QDialog):
    """Dialogue de configuration du calcul des notes."""

    _BOUNDARY_LABELS = {1: "1 (tres faible)", 2: "2 (faible)", 3: "3 (satisfaisant)",
                        4: "4 (bon)", 5: "5 (tres bon)", 6: "6 (excellent)", 7: "7 (exceptionnel)"}

    def __init__(self, termsubject_id: int, subject_label: str = '', parent=None):
        super().__init__(parent)
        self._termsubject_id = termsubject_id
        self._subject_label = subject_label or f"Matiere #{termsubject_id}"

        self.setWindowTitle(f"Ponderation — {self._subject_label}")
        self.setMinimumWidth(ds.sidebar_width * 2 + ds.space_lg)
        self.setModal(True)

        self._formula = CalcEngine.get_formula(termsubject_id)
        self._is_pei = self._formula.get("type") == "PEI"
        self._built = False

        # Charger le poids et les infos depuis la DB locale
        self._subject_weight = 1.0
        self._term_label = ''
        conn = db.local_conn
        if conn is not None:
            row = conn.execute(
                "SELECT cts.subject_weight, t.label FROM larcauth_classroom_termsubject cts "
                "JOIN larcauth_term t ON t.id = cts.fk_term_id WHERE cts.id = ?",
                (str(termsubject_id),)
            ).fetchone()
            if row:
                self._subject_weight = float(row[0]) if row[0] is not None else 1.0
                self._term_label = str(row[1]) if row[1] else ''

        self._setup_ui()
        self._load_current()
        self._built = True

    # ── UI ─────────────────────────────────────────────────────

    def _setup_ui(self):
        p = theme_manager.palette
        s = theme_manager.font_size
        root = QVBoxLayout(self)
        root.setContentsMargins(ds.space_m3, ds.space_m3, ds.space_m3, ds.space_m3)
        root.setSpacing(ds.space_md)

        # ── Header: Matiere, Trimestre, Coefficient ──
        info_panel = QFrame()
        info_panel.setStyleSheet(
            f"QFrame {{ background: {p.surface}; color: {p.text_strong}; "
            f"border: 1px solid {p.outline_variant}; border-radius: {ds.radius_md}px; }}")
        info_panel.setAttribute(Qt.WA_StyledBackground, True)
        info_layout = QHBoxLayout(info_panel)
        info_layout.setContentsMargins(ds.space_m3, ds.space_sm, ds.space_m3, ds.space_sm)
        info_layout.setSpacing(ds.space_md)

        # Nom matiere
        mat_col = QVBoxLayout()
        mat_col.setSpacing(ds.space_xxs)
        mat_lbl = QLabel('Matiere')
        mat_lbl.setStyleSheet(f"font-size: {s(11)}px; color: {p.text_soft}; font-weight: bold;")
        mat_col.addWidget(mat_lbl)
        mat_val = QLabel(self._subject_label)
        mat_val.setStyleSheet(f"font-size: {s(14)}px; color: {p.text_strong}; font-weight: bold;")
        mat_col.addWidget(mat_val)
        info_layout.addLayout(mat_col)

        # Trimestre
        term_col = QVBoxLayout()
        term_col.setSpacing(ds.space_xxs)
        term_lbl = QLabel('Trimestre')
        term_lbl.setStyleSheet(f"font-size: {s(11)}px; color: {p.text_soft}; font-weight: bold;")
        term_col.addWidget(term_lbl)
        term_val = QLabel(self._term_label or '—')
        term_val.setStyleSheet(f"font-size: {s(14)}px; color: {p.text_strong};")
        term_col.addWidget(term_val)
        info_layout.addLayout(term_col)

        info_layout.addStretch()

        # Coefficient
        coef_col = QVBoxLayout()
        coef_col.setSpacing(ds.space_xxs)
        coef_lbl = QLabel('Coefficient')
        coef_lbl.setStyleSheet(f"font-size: {s(11)}px; color: {p.text_soft}; font-weight: bold;")
        coef_col.addWidget(coef_lbl)
        coef_row = QHBoxLayout()
        coef_row.setSpacing(ds.space_xxs)
        self._weight_spin = QDoubleSpinBox()
        self._weight_spin.setRange(0.1, 10.0)
        self._weight_spin.setDecimals(2)
        self._weight_spin.setSingleStep(0.5)
        self._weight_spin.setValue(self._subject_weight)
        self._weight_spin.setFixedWidth(ds.sidebar_width // 3)
        self._weight_spin.setStyleSheet(
            f"QDoubleSpinBox {{ font-size: {s(14)}px; color: {p.text_strong}; font-weight: bold; "
            f"border: 1px solid {p.primary}; border-radius: {ds.radius_xs}px; "
            f"padding: {ds.space_xxs}px; }}")
        coef_row.addWidget(self._weight_spin)
        coef_hint = QLabel('(1.0 = defaut)')
        coef_hint.setStyleSheet(f"font-size: {s(11)}px; color: {p.text_soft};")
        coef_row.addWidget(coef_hint)
        coef_col.addLayout(coef_row)
        info_layout.addLayout(coef_col)

        root.addWidget(info_panel)

        # Template selector
        tmpl_row = QHBoxLayout()
        tmpl_lbl = QLabel("Template :")
        tmpl_lbl.setStyleSheet(f"font-weight: bold; color: {p.text_strong}; font-size: {s(13)}px;")
        tmpl_row.addWidget(tmpl_lbl)

        self._template_combo = QComboBox()
        self._template_combo.currentIndexChanged.connect(self._on_template_changed)
        if self._is_pei:
            self._template_combo.addItem("PEI Standard (4 criteres)", "4c")
            self._template_combo.addItem("PEI 3 criteres", "3c")
            self._template_combo.addItem("PEI 2 criteres", "2c")
            self._template_combo.addItem("PEI 1 critere", "1c")
            self._template_combo.addItem("Personnalise", "custom")
        else:
            self._template_combo.addItem("DP Standard IB", "standard")
            self._template_combo.addItem("DP Moyenne simple", "simple")
            self._template_combo.addItem("Personnalise", "custom")
        tmpl_row.addWidget(self._template_combo, 1)
        root.addLayout(tmpl_row)

        # ── Scroll area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.viewport().setStyleSheet("background: transparent;")
        sc_content = QWidget()
        sc_content.setStyleSheet("background: transparent;")
        sc_layout = QVBoxLayout(sc_content)
        sc_layout.setContentsMargins(0, 0, 0, 0)
        sc_layout.setSpacing(ds.space_md)

        if self._is_pei:
            sc_layout.addWidget(self._build_criteria_section())
            sc_layout.addWidget(self._build_weights_section())
            sc_layout.addWidget(self._build_conversion_section())
        else:
            sc_layout.addWidget(self._build_dp_section())

        sc_layout.addStretch()
        scroll.setWidget(sc_content)
        root.addWidget(scroll, 1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        apply_all = QPushButton("Appliquer par defaut a toutes")
        apply_all.setStyleSheet(
            f"QPushButton {{ color: {p.primary}; font-size: {theme_manager.font_size(12)}px; "
            f"border: 1px solid {p.outline_variant}; border-radius: {ds.radius_lg}px; "
            f"padding: {ds.space_xs}px {ds.space_m3}px; }}")
        apply_all.clicked.connect(self._on_apply_all)
        btn_row.addWidget(apply_all)

        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        box.accepted.connect(self._on_save)
        box.rejected.connect(self.reject)
        btn_row.addWidget(box)
        root.addLayout(btn_row)

    # ── PEI: Critères ──────────────────────────────────────────

    def _build_criteria_section(self) -> QGroupBox:
        p = theme_manager.palette
        gb = QGroupBox("Criteres a inclure dans la moyenne")
        gb.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {p.text_strong}; "
                         f"font-size: {theme_manager.font_size(13)}px; padding-top: {ds.space_md}px; }}")

        layout = QHBoxLayout(gb)
        layout.setSpacing(ds.space_md)

        self._crit_checks: dict[str, QCheckBox] = {}
        for letter in ("A", "B", "C", "D"):
            cb = QCheckBox(f"Critere {letter}")
            cb.setStyleSheet(f"font-size: {theme_manager.font_size(13)}px; color: {p.text_strong};")
            layout.addWidget(cb)
            self._crit_checks[letter] = cb

        return gb

    # ── PEI: Poids F/S ─────────────────────────────────────────

    def _build_weights_section(self) -> QGroupBox:
        p = theme_manager.palette
        gb = QGroupBox("Poids des evaluations")
        gb.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {p.text_strong}; "
                         f"font-size: {theme_manager.font_size(13)}px; padding-top: {ds.space_md}px; }}")

        layout = QHBoxLayout(gb)
        layout.setSpacing(ds.space_md)

        # Formative slider
        f_col = QVBoxLayout()
        f_lbl = QLabel("Formatives")
        f_lbl.setStyleSheet(f"color: {p.text_strong}; font-size: {theme_manager.font_size(12)}px;")
        f_col.addWidget(f_lbl)

        f_row = QHBoxLayout()
        self._f_slider = QSlider(Qt.Horizontal)
        self._f_slider.setRange(0, 100)
        self._f_slider.setValue(40)
        self._f_slider.setStyleSheet(
            f"QSlider::groove:horizontal {{ height: 6px; background: {p.outline_variant}; "
            f"border-radius: 3px; }} "
            f"QSlider::handle:horizontal {{ background: {p.primary}; width: 14px; height: 14px; "
            f"margin: -4px 0; border-radius: 7px; }}")
        self._f_slider.valueChanged.connect(self._on_weight_changed)
        f_row.addWidget(self._f_slider)

        self._f_pct = QLabel("40%")
        self._f_pct.setFixedWidth(ds.space_lg + ds.space_xs)
        self._f_pct.setStyleSheet(f"color: {p.primary}; font-weight: bold; font-size: {theme_manager.font_size(14)}px;")
        f_row.addWidget(self._f_pct)
        f_col.addLayout(f_row)

        layout.addLayout(f_col)

        # Sommative slider
        s_col = QVBoxLayout()
        s_lbl = QLabel("Sommatives")
        s_lbl.setStyleSheet(f"color: {p.text_strong}; font-size: {theme_manager.font_size(12)}px;")
        s_col.addWidget(s_lbl)

        s_row = QHBoxLayout()
        self._s_slider = QSlider(Qt.Horizontal)
        self._s_slider.setRange(0, 100)
        self._s_slider.setValue(60)
        self._s_slider.setStyleSheet(self._f_slider.styleSheet())
        self._s_slider.valueChanged.connect(self._on_weight_changed)
        s_row.addWidget(self._s_slider)

        self._s_pct = QLabel("60%")
        self._s_pct.setFixedWidth(ds.space_lg + ds.space_xs)
        self._s_pct.setStyleSheet(f"color: {p.primary}; font-weight: bold; font-size: {theme_manager.font_size(14)}px;")
        s_row.addWidget(self._s_pct)
        s_col.addLayout(s_row)

        layout.addLayout(s_col)
        return gb

    # ── PEI: Conversion ────────────────────────────────────────

    def _build_conversion_section(self) -> QGroupBox:
        p = theme_manager.palette
        gb = QGroupBox("Conversion somme → Note/7")
        gb.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {p.text_strong}; "
                         f"font-size: {theme_manager.font_size(13)}px; padding-top: {ds.space_md}px; }}")

        layout = QVBoxLayout(gb)
        layout.setSpacing(ds.space_xs)

        self._conv_combo = QComboBox()
        self._conv_combo.addItem("Bandes IB (par defaut)", "boundaries")
        self._conv_combo.addItem("Lineaire (proportionnel)", "linear")
        self._conv_combo.currentIndexChanged.connect(self._on_conversion_changed)
        layout.addWidget(self._conv_combo)

        # Tableau des bandes
        self._boundaries_table = QTableWidget(7, 2)
        self._boundaries_table.setHorizontalHeaderLabels(["Note", "Seuil min → max"])
        self._boundaries_table.horizontalHeader().setStretchLastSection(True)
        self._boundaries_table.verticalHeader().setVisible(False)
        self._boundaries_table.setFixedHeight(ds.window_height // 3)
        self._boundaries_table.setStyleSheet(
            f"QTableWidget {{ gridline-color: {p.outline_variant}; font-size: {theme_manager.font_size(12)}px; }}"
            f"QTableWidget::item {{ color: {p.text_strong}; padding: {ds.space_xxs}px; }}")
        layout.addWidget(self._boundaries_table)

        return gb

    # ── DP Section ─────────────────────────────────────────────

    def _build_dp_section(self) -> QGroupBox:
        p = theme_manager.palette
        gb = QGroupBox("Coefficients de calcul")
        gb.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {p.text_strong}; "
                         f"font-size: {theme_manager.font_size(13)}px; padding-top: {ds.space_md}px; }}")

        form = QFormLayout(gb)
        form.setSpacing(ds.space_sm)

        info = QLabel("Moy = EI x coeff + moy(F/20) x coeff + moy(S/20) x coeff")
        info.setStyleSheet(f"color: {p.text_soft}; font-size: {theme_manager.font_size(11)}px; font-style: italic;")
        form.addRow(info)

        self._dp_ei = QDoubleSpinBox()
        self._dp_ei.setRange(-5.0, 5.0)
        self._dp_ei.setDecimals(3)
        self._dp_ei.setSingleStep(0.1)
        self._dp_ei.setStyleSheet(ds.flat_input_qss())
        form.addRow("Coefficient Evaluation Interne :", self._dp_ei)

        self._dp_f = QDoubleSpinBox()
        self._dp_f.setRange(-5.0, 5.0)
        self._dp_f.setDecimals(3)
        self._dp_f.setSingleStep(0.1)
        self._dp_f.setStyleSheet(ds.flat_input_qss())
        form.addRow("Coefficient Formatives :", self._dp_f)

        self._dp_s = QDoubleSpinBox()
        self._dp_s.setRange(-5.0, 5.0)
        self._dp_s.setDecimals(3)
        self._dp_s.setSingleStep(0.1)
        self._dp_s.setStyleSheet(ds.flat_input_qss())
        form.addRow("Coefficient Sommatives :", self._dp_s)

        return gb

    # ── Load / Save ────────────────────────────────────────────

    def _load_current(self):
        if self._is_pei:
            self._load_pei()
        else:
            self._load_dp()
        self._update_preview()

    def _load_pei(self):
        criteria = self._formula.get("criteria", ["A", "B", "C", "D"])
        for letter, cb in self._crit_checks.items():
            cb.setChecked(letter in criteria)

        wf = int(self._formula.get("formative_weight", 0.4) * 100)
        ws = int(self._formula.get("summative_weight", 0.6) * 100)
        self._f_slider.setValue(wf)
        self._s_slider.setValue(ws)

        conv = self._formula.get("conversion", {})
        method = conv.get("method", "boundaries")
        idx = 0 if method == "boundaries" else 1
        self._conv_combo.setCurrentIndex(idx)

        self._fill_boundaries(conv.get("boundaries", []))
        self._boundaries_table.setVisible(method == "boundaries")

        # Connecter events apres load
        for cb in self._crit_checks.values():
            cb.toggled.connect(self._on_criteria_changed)

    def _load_dp(self):
        conv = self._formula.get("conversion", {})
        method = conv.get("method", "simple_avg")
        if method == "simple_avg":
            self._template_combo.setCurrentIndex(1)  # simple
        else:
            self._template_combo.setCurrentIndex(0)  # standard

    def _fill_boundaries(self, boundaries: list[dict]):
        self._boundaries_table.setRowCount(len(boundaries) if boundaries else 7)
        for i in range(7):
            if i < len(boundaries):
                b = boundaries[i]
                self._boundaries_table.setItem(i, 0, QTableWidgetItem(str(b["note"])))
                self._boundaries_table.setItem(i, 1, QTableWidgetItem(f"{b['min']} → {b['max']}"))
            else:
                self._boundaries_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self._boundaries_table.setItem(i, 1, QTableWidgetItem("0 → 0"))

    # ── Handlers ───────────────────────────────────────────────

    @safe_slot("WeightDialog._on_template_changed")
    def _on_template_changed(self, idx: int):
        if not self._built or idx < 0:
            return
        key = self._template_combo.currentData()
        if key == "custom":
            return

        if self._is_pei:
            templates = CalcEngine.get_templates_pei()
            tmpl = templates.get(key)
            if tmpl:
                self._formula = tmpl
                self._formula["type"] = "PEI"
        else:
            templates = CalcEngine.get_templates_dp()
            tmpl = templates.get(key)
            if tmpl:
                self._formula = tmpl
                self._formula["type"] = "DP"

        # Reload UI
        if self._is_pei:
            criteria = self._formula.get("criteria", ["A", "B", "C", "D"])
            for letter, cb in self._crit_checks.items():
                cb.blockSignals(True)
                cb.setChecked(letter in criteria)
                cb.blockSignals(False)
            self._f_slider.blockSignals(True)
            self._s_slider.blockSignals(True)
            self._f_slider.setValue(int(self._formula.get("formative_weight", 0.4) * 100))
            self._s_slider.setValue(int(self._formula.get("summative_weight", 0.6) * 100))
            self._f_slider.blockSignals(False)
            self._s_slider.blockSignals(False)
            self._f_pct.setText(f"{int(self._formula.get('formative_weight', 0.4) * 100)}%")
            self._s_pct.setText(f"{int(self._formula.get('summative_weight', 0.6) * 100)}%")

            conv = self._formula.get("conversion", {})
            boundaries = conv.get("boundaries", [])
            self._fill_boundaries(boundaries)
            self._boundaries_table.setVisible(conv.get("method", "boundaries") == "boundaries")
            self._conv_combo.setCurrentIndex(0 if conv.get("method") == "boundaries" else 1)
        else:
            conv = self._formula.get("conversion", {})
            method = conv.get("method", "simple_avg")
            if method != "simple_avg":
                self._dp_ei.setValue(conv.get("ei_coefficient", 0.125))
                self._dp_f.setValue(conv.get("formative_coefficient", 1.125))
                self._dp_s.setValue(conv.get("summative_coefficient", 0.75))

    @safe_slot("WeightDialog._on_criteria_changed")
    def _on_criteria_changed(self):
        if not self._built:
            return
        criteria = [l for l, cb in self._crit_checks.items() if cb.isChecked()]
        if criteria:
            self._formula["criteria"] = criteria
            # Recalculer bandes
            from common.calc_engine import _recalc_boundaries
            boundaries = _recalc_boundaries(len(criteria))
            self._formula.setdefault("conversion", {})["boundaries"] = boundaries
            self._fill_boundaries(boundaries)

    @safe_slot("WeightDialog._on_weight_changed")
    def _on_weight_changed(self, _value: int = 0):
        if not self._built:
            return
        self._f_pct.setText(f"{self._f_slider.value()}%")
        self._s_pct.setText(f"{self._s_slider.value()}%")
        self._formula["formative_weight"] = self._f_slider.value() / 100
        self._formula["summative_weight"] = self._s_slider.value() / 100

    @safe_slot("WeightDialog._on_conversion_changed")
    def _on_conversion_changed(self, idx: int):
        if not self._built:
            return
        method = self._conv_combo.currentData()
        self._boundaries_table.setVisible(method == "boundaries")
        self._formula.setdefault("conversion", {})["method"] = method

    def _on_save(self):
        # Lire les donnees du formulaire
        if self._is_pei:
            criteria = [l for l, cb in self._crit_checks.items() if cb.isChecked()]
            self._formula["criteria"] = criteria
            self._formula["formative_weight"] = self._f_slider.value() / 100
            self._formula["summative_weight"] = self._s_slider.value() / 100
            # Lire les boundaries modifiees
            conv = self._formula.setdefault("conversion", {})
            if conv.get("method") == "boundaries":
                boundaries = []
                for i in range(self._boundaries_table.rowCount()):
                    note_item = self._boundaries_table.item(i, 0)
                    range_item = self._boundaries_table.item(i, 1)
                    if note_item and range_item:
                        parts = range_item.text().replace(" ", "").split("→")
                        if len(parts) == 2:
                            try:
                                boundaries.append({
                                    "min": int(parts[0]), "max": int(parts[1]),
                                    "note": int(note_item.text()),
                                })
                            except ValueError:
                                pass
                if boundaries:
                    conv["boundaries"] = boundaries
        else:
            conv = self._formula.setdefault("conversion", {})
            method = self._template_combo.currentData()
            if method == "simple":
                self._formula["conversion"] = {"method": "simple_avg"}
            else:
                conv["method"] = "formula"
                conv["ei_coefficient"] = self._dp_ei.value()
                conv["formative_coefficient"] = self._dp_f.value()
                conv["summative_coefficient"] = self._dp_s.value()

        CalcEngine.save_formula(self._termsubject_id, self._formula)
        # Sauvegarder le coefficient
        conn = db.local_conn
        if conn is not None:
            conn.execute(
                "UPDATE larcauth_classroom_termsubject SET subject_weight = ? WHERE id = ?",
                (self._weight_spin.value(), str(self._termsubject_id)))
            conn.commit()
        self.accept()

    def _on_apply_all(self):
        """Applique la formule courante et le coefficient a toutes les matieres du prof."""
        conn = db.local_conn
        if conn is None or not session.user_id:
            return
        CalcEngine.save_formula(self._termsubject_id, self._formula)
        json_str = json.dumps(self._formula, ensure_ascii=False)
        conn.execute("""
            UPDATE larcauth_classroom_termsubject
            SET calc_formula = ?, subject_weight = ?
            WHERE fk_teacher_id = ? AND fk_term_id = ?
        """, (json_str, self._weight_spin.value(), session.user_id, session.active_term_id))
        conn.commit()

    def _update_preview(self):
        pass
