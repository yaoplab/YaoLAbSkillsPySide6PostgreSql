"""
Fiche élève — recherche, consultation et édition des informations élèves.

Architecture :
  - StudentForm       : widget principal (barre recherche + contenu)
  - _StudentSearch    : zone de recherche + résultats
  - _StudentDetail    : onglets Coordonnées / Adresse / Parents + mode édition

Dépendances :
  - LarcSecretaire.common.database  (db.server_conn)
  - LarcSecretaire.common.theme     (theme_manager)
  - LarcSecretaire.common.session   (session)
"""

import json
import os

from larccommon.design_system import ds
from larccommon.icons import icon as md3_icon
from larccommon.l10n import _
from larccommon.safe_slot import safe_slot
from larccommon.widgets.themed_widget import ThemedDialog, ThemedWidget
from LarcSecretaire.common.audit import audit
from LarcSecretaire.common.database import db
from LarcSecretaire.common.logger import log
from LarcSecretaire.common.photos import get_photo_path
from LarcSecretaire.common.session import session
from LarcSecretaire.common.theme import theme_manager
from LarcSecretaire.views.supervisor_panel import _event_color, _event_label
from phibuilder.phi.scale import SpacingToken
from phibuilder.widgets import (
    M3Button,
    M3Card,
    M3ComboBox,
    M3DateEdit,
    M3Dialog,
    M3DialogButtonBox,
    M3Frame,
    M3HeaderView,
    M3Label,
    M3ListWidget,
    M3StackedWidget,
    M3TableWidget,
    M3TextEdit,
    M3TextField,
)
from phibuilder.widgets.button import ButtonVariant
from phibuilder.widgets.card import CardVariant
from PySide6.QtCore import QDate, QEvent, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap, QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QSizePolicy,
    QTableWidgetItem,
    QVBoxLayout,
)

# ──────────────────────────────────────────────
#   Classe utilitaire : cercle avatar initiales
# ──────────────────────────────────────────────


def _make_avatar(last_name: str, first_name: str, size: int = 120) -> QPixmap:
    """Génère un avatar rond avec les initiales (couleurs M3 de la palette active)."""
    initials = (last_name[:1] + first_name[:1]).upper() or "?"
    p = theme_manager.palette
    roles = ["primary", "secondary", "tertiary", "error"]
    # Hash STABLE (pas hash() : randomisé par processus PYTHONHASHSEED)
    seed = sum(ord(c) for c in last_name + first_name)
    bg_role = roles[seed % len(roles)]
    bg = getattr(p, bg_role)
    fg = getattr(p, "on_" + bg_role)
    px = QPixmap(size, size)
    px.fill(Qt.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(bg))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)
    painter.setPen(QColor(fg))
    f = painter.font()
    f.setPixelSize(size // 3)
    f.setBold(True)
    painter.setFont(f)
    painter.drawText(px.rect(), Qt.AlignCenter, initials)
    painter.end()
    return px


# ──────────────────────────────────────────────
#   StudentForm — widget principal
# ──────────────────────────────────────────────


class StudentForm(ThemedWidget):
    """
    Page de gestion des fiches élèves.

    Utilisation :
        form = StudentForm()
        form.search("nom ou classe")   # Recherche programmatique
    """

    def __init__(self):
        super().__init__()
        # Données internes
        self._current_student: dict | None = None  # Élève actuellement affiché
        self._results: list[dict] = []  # Résultats de recherche
        self._dirty: bool = False  # Modifications non sauvegardées

        # UI
        self._init_ui()

    # ──────────── Construction UI ────────────

    def _init_ui(self):
        """Construit l'interface complète."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        layout.setSpacing(ds.space_md)

        # Titre + bouton +
        title_row = QHBoxLayout()
        title = M3Label(_("student_form.title"), style="title_medium")
        title_row.addWidget(title)
        title_row.addStretch()

        self._add_student_btn = M3Button("+", variant=ButtonVariant.TONAL)
        self._add_student_btn.setFixedSize(ds.button_height, ds.button_height)
        self._add_student_btn.clicked.connect(self._open_create_dialog)
        title_row.addWidget(self._add_student_btn)
        layout.addLayout(title_row)

        # Barre de recherche
        search_row = QHBoxLayout()
        self._search_input = M3TextField(placeholder=_("student_form.search_placeholder"))
        self._search_input.returnPressed.connect(self._on_search)
        search_row.addWidget(self._search_input, 1)

        self._search_btn = M3Button(_("student_form.search_button"), variant=ButtonVariant.FILLED)
        self._search_btn.clicked.connect(self._on_search)
        search_row.addWidget(self._search_btn)
        layout.addLayout(search_row)

        # Zone de contenu : résultats (gauche) + détail (droite)
        content = QHBoxLayout()
        content.setSpacing(ds.space_md)

        # ── Panneau résultats (gauche) ──
        self._results_panel = M3Card(variant=CardVariant.ELEVATED, parent=self)
        rp_layout = self._results_panel.content_layout()
        rp_layout.setContentsMargins(ds.space_xs, ds.space_xs, ds.space_xs, ds.space_xs)

        self._results_label = M3Label(_("student_form.results_label").format(count=0), style="label_small")
        self._results_label.setStyleSheet(f"font-weight: bold; color: {ds.p.text_strong};")
        rp_layout.addWidget(self._results_label)

        # Indicateur de recherche (rétroaction pendant la requête)
        self._search_status = M3Label("", style="label_small")
        self._search_status.setStyleSheet(f"color: {ds.p.text_strong};")
        self._search_status.hide()
        rp_layout.addWidget(self._search_status)

        # Tableau des résultats
        self._results_table = M3TableWidget()
        self._results_table.set_headers(
            [_("student_form.table_headers"), _("student_form.table_headers_class"), _("student_form.table_headers_email"), _("student_form.table_headers_id")]
        )
        self._results_table.setColumnHidden(3, True)
        self._results_table.horizontalHeader().setStretchLastSection(True)
        self._results_table.setEditTriggers(M3TableWidget.NoEditTriggers)
        self._results_table.setSelectionBehavior(M3TableWidget.SelectRows)
        self._results_table.setAlternatingRowColors(False)
        self._results_table.itemSelectionChanged.connect(self._on_result_selected)
        self._results_table.verticalHeader().setDefaultSectionSize(ds.table_row_min)
        # Q1 : affordance M3 — curseur main + Entrée ouvre la fiche sélectionnée
        self._results_table.viewport().setCursor(Qt.PointingHandCursor)
        self._results_table.installEventFilter(self)
        rp_layout.addWidget(self._results_table, 1)

        # Q2 : état vide inline (M3) — icône + message, jamais de QMessageBox modal
        # Taille icône via token image (sous-système E) : logo_small = 55 (le plus proche de 48)
        self._empty_state = M3Frame()
        es_layout = QVBoxLayout(self._empty_state)
        es_layout.setSpacing(ds.space_sm)
        es_icon = QLabel()
        es_icon.setPixmap(
            md3_icon(
                "search_off",
                color=ds.p.text_disabled,
                size=theme_manager.image.logo_small,
            ).pixmap(theme_manager.image.logo_small, theme_manager.image.logo_small)
        )
        es_icon.setAlignment(Qt.AlignCenter)
        es_layout.addWidget(es_icon)
        self._empty_state_label = M3Label(_("student_form.search_no_results"), style="body_medium")
        self._empty_state_label.setStyleSheet(f"color: {ds.p.text_disabled};")
        self._empty_state_label.setAlignment(Qt.AlignCenter)
        self._empty_state_label.setWordWrap(True)
        es_layout.addWidget(self._empty_state_label)
        self._empty_state.hide()
        rp_layout.addWidget(self._empty_state, 1)
        content.addWidget(self._results_panel, 1)

        # ── Panneau détail (droite) — photo + infos ──
        self._detail_panel = M3Card(variant=CardVariant.ELEVATED, parent=self)
        dp_layout = self._detail_panel.content_layout()
        dp_layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)
        dp_layout.setSpacing(ds.space_md)

        # Photo + infos en ligne
        info_row = QHBoxLayout()
        info_row.setSpacing(ds.space_sm)

        self._detail_photo = QLabel()
        self._pw, self._ph = ds.sp(SpacingToken.XXXL) + ds.sp(SpacingToken.MD), ds.sp(SpacingToken.XXXL)
        self._detail_photo.setFixedSize(self._pw, self._ph)
        self._detail_photo.setStyleSheet(f"background: {ds.p.primary_container}; border-radius: {ds.radius_sm}px;")
        self._detail_photo.setAlignment(Qt.AlignCenter)
        self._detail_photo.setCursor(Qt.PointingHandCursor)
        # Q4 : info-bulle sur la zone cliquable
        self._detail_photo.setToolTip(_("student_form.open_file"))
        self._detail_photo.installEventFilter(self)
        info_row.addWidget(self._detail_photo)

        text_col = QVBoxLayout()
        text_col.setSpacing(ds.space_xxs)
        # Ligne 1 : PRÉNOM (plus grand) + NOM (majuscules) — même header que le dialogue
        name_row = QHBoxLayout()
        name_row.setSpacing(ds.space_sm)
        self._detail_prenom_label = M3Label("—", style="headline_large")
        self._detail_prenom_label.setStyleSheet(f"font-weight: bold; color: {ds.p.text_strong};")
        name_row.addWidget(self._detail_prenom_label)
        self._detail_nom_label = M3Label("", style="title_large")
        self._detail_nom_label.setStyleSheet(f"font-weight: bold; color: {ds.p.text_strong};")
        name_row.addWidget(self._detail_nom_label)
        name_row.addStretch()
        text_col.addLayout(name_row)

        # Ligne 2 : Classe
        self._detail_classe_label = M3Label("", style="body_medium")
        self._detail_classe_label.setStyleSheet(f"color: {ds.p.text_strong};")
        text_col.addWidget(self._detail_classe_label)

        # Ligne 3 : Id
        self._detail_id_label = M3Label("", style="body_medium")
        self._detail_id_label.setStyleSheet(f"color: {ds.p.text_strong};")
        text_col.addWidget(self._detail_id_label)
        text_col.addStretch()
        info_row.addLayout(text_col, 1)
        dp_layout.addLayout(info_row)

        self._open_btn = M3Button(_("student_form.open_file"), variant=ButtonVariant.FILLED)
        self._open_btn.clicked.connect(self._open_edit_dialog)
        self._open_btn.setMinimumWidth(ds.sp(SpacingToken.XXL) + ds.sp(SpacingToken.XL) + 9)
        dp_layout.addWidget(self._open_btn, 0, Qt.AlignCenter)

        dp_layout.addStretch()

        self._detail_panel.hide()
        content.addWidget(self._detail_panel, 1)

        layout.addLayout(content, 1)

        ds.theme_changed.connect(self._restyle)
        # Application initiale du style (hover M3, couleurs header/état vide) :
        # pattern des vues Larc — _restyle n'est sinon déclenché que par theme_changed.
        self._restyle()

    @safe_slot("Unknown._restyle")
    def _restyle(self):
        if hasattr(self, "_results_table") and self._results_table:
            # Q1 : state layer hover M3 sur les lignes
            self._results_table.setStyleSheet(ds.table_qss() + f"M3TableWidget::item:hover {{ background: {ds.p.surface_variant}; }}")
        if hasattr(self, "_detail_photo") and self._detail_photo:
            self._detail_photo.setStyleSheet(f"background: {ds.p.primary_container}; border-radius: {ds.radius_sm}px;")
        if hasattr(self, "_empty_state_label") and self._empty_state_label:
            self._empty_state_label.setStyleSheet(f"color: {ds.p.text_disabled};")
        if hasattr(self, "_search_status") and self._search_status:
            self._search_status.setStyleSheet(f"color: {ds.p.text_strong};")
        # Header élève : couleurs réactives au thème
        if hasattr(self, "_detail_prenom_label") and self._detail_prenom_label:
            for lbl in (self._detail_prenom_label, self._detail_nom_label):
                lbl.setStyleSheet(f"font-weight: bold; color: {ds.p.text_strong};")
            for lbl in (self._detail_classe_label, self._detail_id_label):
                lbl.setStyleSheet(f"color: {ds.p.text_strong};")

    # ──────────── Recherche ────────────

    @safe_slot("StudentForm.on_search")
    def _on_search(self, checked: bool = False):
        """
        Déclenche la recherche quand l'utilisateur appuie sur Entrée ou clique Rechercher.

        Args:
            checked: Ignoré (requis par le signal clicked(bool) de QPushButton)
        """
        query = self._search_input.text().strip()
        if not query:
            QMessageBox.information(self, _("student_form.search_info_title"), _("student_form.search_info_msg"))
            return
        self.search(query)

    def search(self, query: str):
        """
        Recherche des élèves par nom, prénom, email ou classe.

        Les résultats sont affichés dans le panneau de gauche.
        """
        conn = db.server_conn
        if not conn:
            QMessageBox.warning(self, _("common.dialog.error_title"), _("student_form.error.no_connection"))
            return

        from psycopg2 import errors as pg_errors

        # Q4 : indicateur de chargement pendant la requête
        self._search_status.setText(_("student_form.searching"))
        self._search_status.show()
        QApplication.processEvents()
        try:
            cur = conn.cursor()
            like = f"%{query}%"
            try:
                cur.execute(
                    """
                    SELECT
                        s.aecuser_ptr_id AS id,
                        aec.last_name, aec.first_name,
                        aec.email, aec.emailperso,
                        aec.tel_smartphone_1, aec.tel_maison,
                        c.label AS classroom,
                        aec.date_joined, aec.date_entree, aec.date_of_birth, aec.fk_foyer_id,
                        aec.fk_gender_id, s.s_classroom_id,
                        s.notes, s.notes_json,
                        f.address_line1, f.address_line2, f.postal_code,
                        f.city, f.country,
                        f.phone AS foyer_phone, f.email AS foyer_email
                    FROM larcauth_student s
                    JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id
                    JOIN larcauth_classroom c ON c.id = s.s_classroom_id
                    LEFT JOIN foyer f ON f.id = aec.fk_foyer_id
                    WHERE s.enabled = TRUE
                      AND (aec.last_name ILIKE %s OR aec.first_name ILIKE %s
                        OR aec.email ILIKE %s OR c.label ILIKE %s)
                    ORDER BY aec.last_name, aec.first_name
                    LIMIT 200
                """,
                    (
                        like,
                        like,
                        like,
                        like,
                    ),
                )
            except pg_errors.UndefinedColumn:
                cur.execute(
                    """
                    SELECT
                        s.aecuser_ptr_id AS id,
                        aec.last_name, aec.first_name,
                        aec.email, aec.emailperso,
                        aec.tel_smartphone_1, aec.tel_maison,
                        c.label AS classroom,
                        aec.date_joined, aec.date_entree, aec.date_of_birth, aec.fk_foyer_id,
                        aec.fk_gender_id, s.s_classroom_id,
                        NULL AS notes, NULL AS notes_json,
                        f.address_line1, f.address_line2, f.postal_code,
                        f.city, f.country,
                        f.phone AS foyer_phone, f.email AS foyer_email
                    FROM larcauth_student s
                    JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id
                    JOIN larcauth_classroom c ON c.id = s.s_classroom_id
                    LEFT JOIN foyer f ON f.id = aec.fk_foyer_id
                    WHERE s.enabled = TRUE
                      AND (aec.last_name ILIKE %s OR aec.first_name ILIKE %s
                        OR aec.email ILIKE %s OR c.label ILIKE %s)
                    ORDER BY aec.last_name, aec.first_name
                    LIMIT 200
                """,
                    (
                        like,
                        like,
                        like,
                        like,
                    ),
                )

            cols = [desc[0] for desc in cur.description]
            self._results = [dict(zip(cols, row)) for row in cur.fetchall()]
            self._populate_results()

        except Exception as e:
            log(f"StudentForm.search: {e}")
            QMessageBox.critical(self, _("common.dialog.error_title"), str(e))
        finally:
            self._search_status.hide()

    def _populate_results(self):
        """Remplit le tableau des résultats de recherche."""
        self._results_table.setRowCount(0)
        for r in self._results:
            row = self._results_table.rowCount()
            self._results_table.insertRow(row)
            self._results_table.setItem(row, 0, QTableWidgetItem(f"{r['last_name']} {r['first_name']}"))
            self._results_table.setItem(row, 1, QTableWidgetItem(r.get("classroom", "")))
            self._results_table.setItem(row, 2, QTableWidgetItem(r.get("email", "")))
            self._results_table.setItem(row, 3, QTableWidgetItem(str(r["id"])))

        self._results_table.resizeColumnsToContents()
        count = len(self._results)
        self._results_label.setText(_("student_form.results_label").format(count=count))

        if count == 0:
            # Q2 : état vide inline — pas de popup modal
            self._detail_panel.hide()
            self._results_table.hide()
            self._empty_state.show()
        else:
            self._results_table.show()
            self._empty_state.hide()
            if count == 1:
                # Sélection automatique si un seul résultat
                self._results_table.selectRow(0)

    # ──────────── Affichage du détail ────────────

    @safe_slot("StudentForm.on_result_selected")
    def _on_result_selected(self):
        """Sélection d'un résultat → ouvre la popup d'édition."""
        rows = self._results_table.selectedItems()
        if not rows:
            return
        student_id = int(self._results_table.item(rows[0].row(), 3).text())
        self._open_student_dialog(student_id)

    def _open_student_dialog(self, student_id: int, force_refresh: bool = False):
        """Ouvre la popup d'édition pour un élève."""
        data = None
        if not force_refresh:
            data = next((r for r in self._results if r["id"] == student_id), None)
        conn = db.server_conn
        if not conn:
            return
        from psycopg2 import errors as pg_errors

        try:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT
                        s.aecuser_ptr_id AS id,
                        aec.last_name, aec.first_name, aec.email,
                        aec.emailperso, aec.tel_smartphone_1, aec.tel_maison,
                        c.label AS classroom, aec.date_joined,
                        aec.date_entree,
                        aec.date_of_birth,
                        aec.fk_foyer_id, aec.fk_gender_id,
                        s.s_classroom_id, s.notes, s.notes_json,
                        f.address_line1, f.address_line2, f.postal_code,
                        f.city, f.country, f.phone AS foyer_phone, f.email AS foyer_email
                    FROM larcauth_student s
                    JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id
                    JOIN larcauth_classroom c ON c.id = s.s_classroom_id
                    LEFT JOIN foyer f ON f.id = aec.fk_foyer_id
                    WHERE s.aecuser_ptr_id = %s
                """,
                    (student_id,),
                )
            except pg_errors.UndefinedColumn:
                cur.execute(
                    """
                    SELECT
                        s.aecuser_ptr_id AS id,
                        aec.last_name, aec.first_name, aec.email,
                        aec.emailperso, aec.tel_smartphone_1, aec.tel_maison,
                        c.label AS classroom, aec.date_joined,
                        aec.date_entree,
                        aec.date_of_birth,
                        aec.fk_foyer_id, aec.fk_gender_id,
                        s.s_classroom_id, NULL AS notes, NULL AS notes_json,
                        f.address_line1, f.address_line2, f.postal_code,
                        f.city, f.country, f.phone AS foyer_phone, f.email AS foyer_email
                    FROM larcauth_student s
                    JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id
                    JOIN larcauth_classroom c ON c.id = s.s_classroom_id
                    LEFT JOIN foyer f ON f.id = aec.fk_foyer_id
                    WHERE s.aecuser_ptr_id = %s
                """,
                    (student_id,),
                )
            cols = [desc[0] for desc in cur.description]
            row = cur.fetchone()
            if not row:
                return
            data = dict(zip(cols, row))
        except Exception as e:
            log(f"StudentForm._open_student_dialog: {e}")
            return

        self._current_student = data
        self._update_info_card(data)
        self._detail_panel.show()

    def _update_info_card(self, data: dict):
        """Met à jour la vignette info."""
        sid = data["id"]
        px = QPixmap(get_photo_path(sid))
        if px.isNull():
            px = _make_avatar(data["last_name"], data["first_name"], 160)
        else:
            px = px.scaled(self._pw, self._ph, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._detail_photo.setPixmap(px)
        self._detail_prenom_label.setText(data.get("first_name", "") or "")
        self._detail_nom_label.setText((data.get("last_name", "") or "").upper())
        self._detail_classe_label.setText(_("student_form.class_label").format(label=data.get("classroom", "—")))
        self._detail_id_label.setText(_("student_form.id_label").format(id=sid))

    @safe_slot("StudentForm.open_edit_dialog")
    def _open_edit_dialog(self):
        """Ouvre la popup d'édition pour l'élève courant."""
        if not self._current_student:
            return
        dlg = StudentEditDialog(self._current_student, self)
        if dlg.exec():
            self.search(self._search_input.text().strip())
            self._open_student_dialog(self._current_student["id"], force_refresh=True)

    @safe_slot("StudentForm.open_create_dialog")
    def _open_create_dialog(self):
        dlg = StudentCreateDialog(self)
        dlg.exec()

    def eventFilter(self, obj, event):
        # Garde getattr : l'eventFilter est installé sur _results_table AVANT la
        # création de _detail_photo (pendant _init_ui) → ne jamais y accéder sans garde.
        photo = getattr(self, "_detail_photo", None)
        if photo is not None and obj == photo and event.type() == QEvent.MouseButtonPress:
            self._open_edit_dialog()
            return True
        # Q3 : Entrée/Retour sur la ligne sélectionnée → ouvrir la fiche
        if obj == self._results_table and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if self._results_table.selectedItems():
                    self._open_edit_dialog()
                    return True
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        """Q3 : focus initial sur le champ de recherche (une seule fois)."""
        super().showEvent(event)
        if not getattr(self, "_focus_once", False):
            self._focus_once = True
            self._search_input.setFocus()


# ──────────────────────────────────────────────
#   StudentEditDialog — Modification d'un élève (popup)
# ──────────────────────────────────────────────


class StudentEditDialog(ThemedDialog):
    """Popup d'édition d'élève — grand formulaire comme la création."""

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self._sid = data["id"]
        self._data = self._fetch_fresh_data() or data
        self._dirty: bool = False  # Dossier modifié non sauvegardé → indicateur bouton Enregistrer
        self.setWindowTitle(_("student_form.edit_title").format(l=self._data.get("last_name", "?"), f=self._data.get("first_name", "?")))
        # 987×610 = paire dorée (610 = sidebar + golden_width(sidebar) ; 987 = golden_width(610))
        _min_h = ds.sidebar_width + ds.golden_width(ds.sidebar_width)  # 610
        self.setMinimumSize(ds.golden_width(_min_h), _min_h)  # 987×610
        try:
            self._init_ui()
            self._load_data()
        except Exception as e:
            import traceback

            log(f"StudentEditDialog.__init__: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, _("common.dialog.error_title"), f"{e}")
            # raise : l'appelant n'atteindra jamais dlg.exec() (sinon il réafficherait
            # le dialogue vide/partiellement construit). safe_slot / PySide6 gèrent
            # l'exception proprement (log + traceback) sans casser l'app.
            raise
        # Connexion theme_changed UNIQUEMENT après construction réussie : si la
        # construction échoue (raise ci-dessus), le signal ne garde pas une
        # référence à un dialogue à moitié construit.
        ds.theme_changed.connect(self._restyle)
        # Afficher APRÈS construction : un showMaximized() précoce laisserait
        # une fenêtre vide si _init_ui() levait une exception (traceback invisible).
        self.showMaximized()

    def _fetch_fresh_data(self) -> dict | None:
        conn = db.server_conn
        if not conn:
            return None
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    s.aecuser_ptr_id AS id,
                    aec.last_name, aec.first_name, aec.email,
                    aec.emailperso, aec.tel_smartphone_1, aec.tel_maison,
                    c.label AS classroom, aec.date_joined,
                    aec.date_entree,
                    aec.date_of_birth,
                    aec.fk_foyer_id, aec.fk_gender_id,
                    s.s_classroom_id, s.notes, s.notes_json,
                    f.address_line1, f.address_line2, f.postal_code,
                    f.city, f.country, f.phone AS foyer_phone, f.email AS foyer_email
                FROM larcauth_student s
                JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id
                JOIN larcauth_classroom c ON c.id = s.s_classroom_id
                LEFT JOIN foyer f ON f.id = aec.fk_foyer_id
                WHERE s.aecuser_ptr_id = %s
            """,
                (self._sid,),
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except Exception as e:
            log(f"StudentEditDialog._fetch_fresh_data: {e}")
            return None

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(ds.sp(SpacingToken.SM))
        layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)

        title = M3Label(_("student_form.edit_label"), style="title_small")
        layout.addWidget(title)

        def _lbl(t):
            lbl = M3Label(t, style="body_medium")
            lbl.setStyleSheet(f"font-weight: bold; color: {ds.p.text_strong};")
            lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            return lbl

        # Photo + nom + actions
        photo_row = QHBoxLayout()
        photo_row.setSpacing(ds.sp(SpacingToken.SM))
        self._photo = QLabel()
        self._photo.setFixedSize(ds.sp(SpacingToken.XXXL), ds.sp(SpacingToken.XXXL))
        self._photo.setStyleSheet(f"background: {ds.p.primary_container}; border-radius: {ds.radius_sm}px;")
        self._photo.setAlignment(Qt.AlignCenter)
        photo_row.addWidget(self._photo)

        id_col = QVBoxLayout()
        id_col.setSpacing(ds.space_xxs)
        # Ligne 1 : PRÉNOM (plus grand) + NOM (majuscules)
        name_row = QHBoxLayout()
        name_row.setSpacing(ds.space_sm)
        self._id_prenom = M3Label("", style="headline_large")
        self._id_prenom.setStyleSheet(f"font-weight: bold; color: {ds.p.text_strong};")
        name_row.addWidget(self._id_prenom)
        self._id_nom = M3Label("", style="title_large")
        self._id_nom.setStyleSheet(f"font-weight: bold; color: {ds.p.text_strong};")
        name_row.addWidget(self._id_nom)
        name_row.addStretch()
        id_col.addLayout(name_row)
        # Ligne 2 : Classe
        self._id_classe = M3Label("", style="body_medium")
        self._id_classe.setStyleSheet(f"color: {ds.p.text_strong};")
        id_col.addWidget(self._id_classe)
        # Ligne 3 : Id
        self._id_id = M3Label("", style="body_medium")
        self._id_id.setStyleSheet(f"color: {ds.p.text_strong};")
        id_col.addWidget(self._id_id)
        id_col.addStretch()
        photo_row.addLayout(id_col, 1)

        # Boutons d'action (2 colonnes: PDF/Word | Save/Cancel)
        btn_col = QVBoxLayout()
        btn_col.setSpacing(ds.space_sm)
        btn_col.setAlignment(Qt.AlignTop)

        def _m3_btn(text, variant):
            b = M3Button(text, variant=variant)
            b.setMinimumHeight(ds.button_height)
            return b

        col_pdf = QVBoxLayout()
        col_pdf.setSpacing(ds.space_sm)
        col_pdf.setAlignment(Qt.AlignTop)
        pdf_btn = _m3_btn(_("student_form.pdf"), ButtonVariant.TONAL)
        pdf_btn.clicked.connect(self._export_pdf)
        col_pdf.addWidget(pdf_btn)
        word_btn = _m3_btn(_("student_form.word"), ButtonVariant.TONAL)
        word_btn.clicked.connect(self._export_word)
        col_pdf.addWidget(word_btn)
        photo_row.addLayout(col_pdf)

        self._save_btn = _m3_btn(_("student_form.save"), ButtonVariant.FILLED)
        self._save_btn.clicked.connect(self._save)
        btn_col.addWidget(self._save_btn)
        cancel_btn = _m3_btn(_("student_form.cancel"), ButtonVariant.OUTLINED)
        cancel_btn.clicked.connect(self.reject)
        btn_col.addWidget(cancel_btn)
        btn_col.addStretch()
        photo_row.addLayout(btn_col)

        layout.addLayout(photo_row)
        layout.addSpacing(ds.sp(SpacingToken.SM))

        # Champs — hauteur uniforme via Fibonacci
        _fh = ds.field_height
        self._inp_nom = M3TextField()
        self._inp_nom.setFixedHeight(_fh)
        self._inp_prenom = M3TextField()
        self._inp_prenom.setFixedHeight(_fh)
        self._inp_email = M3TextField()
        self._inp_email.setFixedHeight(_fh)
        self._inp_emailperso = M3TextField()
        self._inp_emailperso.setFixedHeight(_fh)
        self._inp_tel = M3TextField()
        self._inp_tel.setFixedHeight(_fh)
        self._inp_tel2 = M3TextField()
        self._inp_tel2.setFixedHeight(_fh)
        self._inp_date_joined = M3DateEdit()
        self._inp_date_joined.setFixedHeight(_fh)
        self._inp_date_joined.setDisplayFormat("yyyy-MM-dd")
        self._inp_date_joined.setCalendarPopup(True)
        self._inp_date_joined.setSpecialValueText(" ")
        self._inp_date_joined.setDate(QDate())
        self._inp_date = M3DateEdit()
        self._inp_date.setFixedHeight(_fh)
        self._inp_date.setDisplayFormat("yyyy-MM-dd")
        self._inp_date.setCalendarPopup(True)
        self._inp_date.setSpecialValueText(" ")
        self._inp_date.setDate(QDate())
        self._inp_genre = M3ComboBox()
        self._inp_genre.setFixedHeight(_fh)
        self._load_genders()
        self._inp_birthdate = M3DateEdit()
        self._inp_birthdate.setFixedHeight(_fh)
        self._inp_birthdate.setDisplayFormat("yyyy-MM-dd")
        self._inp_birthdate.setCalendarPopup(True)
        self._inp_birthdate.setSpecialValueText(" ")
        self._inp_birthdate.setDate(QDate())
        self._inp_addr1 = M3TextEdit()
        self._inp_addr1.setFixedHeight(ds.sp(SpacingToken.XXXL))
        self._inp_addr1.setPlaceholderText(_("student_form.street_placeholder"))
        self._inp_addr1.setStyleSheet(ds.flat_input_qss())
        self._inp_addr2 = M3TextField()
        self._inp_addr2.setFixedHeight(_fh)
        self._inp_cp = M3TextField()
        self._inp_cp.setFixedHeight(_fh)
        self._inp_ville = M3TextField()
        self._inp_ville.setFixedHeight(_fh)
        self._inp_pays = M3TextField(_("student_form.default_country"))
        self._inp_pays.setFixedHeight(_fh)

        # Flat field styling via ds helper
        for w in (
            self._inp_nom,
            self._inp_prenom,
            self._inp_email,
            self._inp_emailperso,
            self._inp_tel,
            self._inp_tel2,
            self._inp_addr2,
            self._inp_cp,
            self._inp_ville,
            self._inp_pays,
        ):
            w.setStyleSheet(ds.flat_input_qss())
        for w in (self._inp_date_joined, self._inp_date, self._inp_birthdate, self._inp_genre):
            w.setStyleSheet(
                f"border: 1px solid {ds.p.outline}; border-radius: {ds.radius_xs}px; "
                f"padding: {ds.space_md}px; color: {ds.p.text_strong}; background: {ds.p.surface}; "
                f"QDateEdit QLineEdit {{ color: {ds.p.text_strong}; background: {ds.p.surface}; }}"
            )
            w.setFixedWidth(ds.sp(SpacingToken.XXL) + ds.sp(SpacingToken.MD))

        # Sidebar verticale + QStackedWidget (remplace les onglets)
        nav_row = QHBoxLayout()
        nav_row.setSpacing(ds.sp(SpacingToken.SM))
        nav_side = QVBoxLayout()
        nav_side.setSpacing(ds.space_sm)
        nav_side.setContentsMargins(0, 0, ds.sp(SpacingToken.SM), 0)

        self._nav_btns: list[M3Button] = []

        # --- Page 1 : Identité & Contact (redesign M3Cards + Fibonacci) ---
        p1 = M3Frame()
        p1_layout = QVBoxLayout(p1)
        p1_layout.setSpacing(ds.sp(SpacingToken.MD))

        # --- Carte Identité ---
        id_card = M3Card(variant=CardVariant.ELEVATED)
        id_cl = id_card.content_layout()
        id_cl.setSpacing(ds.sp(SpacingToken.SM))
        id_cl.addWidget(M3Label(_("student_form.tab_identity"), style="title_small"))
        id_grid = QGridLayout()
        id_grid.setSpacing(ds.sp(SpacingToken.SM))
        id_grid.setColumnStretch(0, 1)
        id_grid.setColumnStretch(1, 1)
        r = 0
        id_grid.addWidget(_lbl(_("student_form.first_name_label")), r, 0)
        id_grid.addWidget(_lbl(_("student_form.last_name_label")), r, 1)
        r += 1
        id_grid.addWidget(self._inp_prenom, r, 0)
        id_grid.addWidget(self._inp_nom, r, 1)
        r += 1
        id_grid.addWidget(_lbl(_("student_form.gender_label")), r, 0)
        r += 1
        id_grid.addWidget(self._inp_genre, r, 0)
        self._inp_genre.setFixedWidth(ds.sp(SpacingToken.XXL) + ds.sp(SpacingToken.XL))
        id_cl.addLayout(id_grid)
        p1_layout.addWidget(id_card)

        # --- Carte Dates (3 dates empilées) ---
        dt_card = M3Card(variant=CardVariant.ELEVATED)
        dt_cl = dt_card.content_layout()
        dt_cl.setSpacing(ds.sp(SpacingToken.SM))
        dt_cl.addWidget(M3Label("Dates", style="title_small"))
        # 6 colonnes : dates dans les 3 premières, vide à droite
        dt_grid = QGridLayout()
        dt_grid.setSpacing(ds.sp(SpacingToken.SM))
        for i in range(6):
            dt_grid.setColumnStretch(i, 1)
        for row, (lbl, widget) in enumerate(
            [
                (_("student_form.arrival_label"), self._inp_date_joined),
                (_("student_form.entry_date"), self._inp_date),
                (_("student_form.birth_date"), self._inp_birthdate),
            ]
        ):
            dt_grid.addWidget(M3Label(lbl, style="body_medium"), row * 2, 0, 1, 3)
            dt_grid.addWidget(widget, row * 2 + 1, 0, 1, 3)
        dt_cl.addLayout(dt_grid)
        p1_layout.addWidget(dt_card)

        # --- Carte Contact ---
        ct_card = M3Card(variant=CardVariant.ELEVATED)
        ct_cl = ct_card.content_layout()
        ct_cl.setSpacing(ds.sp(SpacingToken.SM))
        ct_cl.addWidget(M3Label("Contact", style="title_small"))
        ct_grid = QGridLayout()
        ct_grid.setSpacing(ds.sp(SpacingToken.SM))
        ct_grid.setColumnStretch(0, 1)
        ct_grid.setColumnStretch(1, 1)
        r = 0
        ct_grid.addWidget(_lbl(_("student_form.email_label")), r, 0)
        ct_grid.addWidget(_lbl(_("student_form.email_personal")), r, 1)
        r += 1
        ct_grid.addWidget(self._inp_email, r, 0)
        ct_grid.addWidget(self._inp_emailperso, r, 1)
        r += 1
        ct_grid.addWidget(_lbl(_("student_form.phone_mobile")), r, 0)
        ct_grid.addWidget(_lbl(_("student_form.phone_fixed")), r, 1)
        r += 1
        ct_grid.addWidget(self._inp_tel, r, 0)
        ct_grid.addWidget(self._inp_tel2, r, 1)
        ct_cl.addLayout(ct_grid)
        p1_layout.addWidget(ct_card)

        p1_layout.addStretch()

        # --- Page 2 : Adresse & Parents (redesign M3Cards + Fibonacci) ---
        p2_page = M3Frame()
        p2_page_layout = QVBoxLayout(p2_page)
        p2_page_layout.setSpacing(ds.sp(SpacingToken.MD))

        # --- Carte Parents ---
        par_card = M3Card(variant=CardVariant.ELEVATED)
        par_cl = par_card.content_layout()
        par_cl.setSpacing(ds.sp(SpacingToken.SM))
        par_cl.addWidget(M3Label(_("student_form.parents_title"), style="title_small"))

        self._parents_table = M3TableWidget()
        self._parents_table.set_headers(
            [
                _("student_form.parents_table_nom"),
                _("student_form.parents_table_nature"),
                _("student_form.parents_table_email"),
                _("student_form.parents_table_phone"),
            ]
        )
        self._parents_table.horizontalHeader().setStretchLastSection(True)
        self._parents_table.setEditTriggers(M3TableWidget.NoEditTriggers)
        self._parents_table.setSelectionBehavior(M3TableWidget.SelectRows)
        self._parents_table.setShowGrid(True)
        hh = self._parents_table.horizontalHeader()
        hh.setFixedHeight(ds.field_height)
        self._parents_table.setStyleSheet(ds.table_qss())
        self._parents_table.verticalHeader().setDefaultSectionSize(ds.table_row_min)
        self._parents_table.setMaximumHeight(ds.sp(SpacingToken.XXXL))
        par_cl.addWidget(self._parents_table)

        parent_tools = QHBoxLayout()
        parent_tools.setSpacing(ds.sp(SpacingToken.SM))
        add_par_btn = M3Button(_("student_form.add_parent"), variant=ButtonVariant.FILLED)
        add_par_btn.clicked.connect(self._add_parent_link)
        parent_tools.addWidget(add_par_btn)
        edit_par_btn = M3Button(_("student_form.edit_nature"), variant=ButtonVariant.TONAL)
        edit_par_btn.clicked.connect(self._edit_parent_nature)
        parent_tools.addWidget(edit_par_btn)
        remove_par_btn = M3Button(_("student_form.remove_parent"), variant=ButtonVariant.OUTLINED)
        remove_par_btn.clicked.connect(self._remove_parent_link)
        parent_tools.addWidget(remove_par_btn)
        copy_btn = M3Button(_("student_form.copy_address"), variant=ButtonVariant.TONAL)
        copy_btn.clicked.connect(self._copy_parent_address)
        parent_tools.addWidget(copy_btn)
        parent_tools.addStretch()
        par_cl.addLayout(parent_tools)
        # Q2 — état vide INLINE (jamais de QMessageBox modal pour zéro résultat)
        self._addr_status = M3Label("", style="body_small")
        self._addr_status.setWordWrap(True)
        self._addr_status.setStyleSheet(f"color: {ds.p.text_disabled};")
        self._addr_status.hide()
        par_cl.addWidget(self._addr_status)
        p2_page_layout.addWidget(par_card)

        # --- Carte Adresse ---
        addr_card = M3Card(variant=CardVariant.ELEVATED)
        addr_cl = addr_card.content_layout()
        addr_cl.setSpacing(ds.sp(SpacingToken.SM))
        addr_cl.addWidget(M3Label(_("student_form.address_title"), style="title_small"))

        addr_cl.addWidget(self._inp_addr1)
        addr_cl.addWidget(self._inp_addr2)
        addr_grid = QGridLayout()
        addr_grid.setSpacing(ds.sp(SpacingToken.SM))
        addr_grid.setColumnStretch(0, 1)
        addr_grid.setColumnStretch(1, 1)
        addr_grid.addWidget(_lbl(_("student_form.zip_label")), 0, 0)
        addr_grid.addWidget(_lbl(_("student_form.city_label")), 0, 1)
        addr_grid.addWidget(self._inp_cp, 1, 0)
        addr_grid.addWidget(self._inp_ville, 1, 1)
        addr_grid.addWidget(_lbl(_("student_form.country_label")), 2, 0)
        addr_grid.addWidget(self._inp_pays, 3, 0, 1, 2)
        addr_cl.addLayout(addr_grid)
        p2_page_layout.addWidget(addr_card)

        p2_page_layout.addStretch()

        # --- Page 3 : Événements ---
        p3 = M3Frame()
        p3_layout = QVBoxLayout(p3)
        p3_layout.setSpacing(ds.sp(SpacingToken.SM))
        evt_label = M3Label(_("student_form.events_title"), style="headline_large")
        p3_layout.addWidget(evt_label)
        self._evt_table = M3TableWidget()
        self._evt_table.set_headers(
            [
                _("student_form.events_table_date"),
                _("student_form.events_table_type"),
                _("student_form.events_table_note"),
                _("student_form.events_table_by"),
                _("student_form.events_table_validated"),
            ]
        )
        hh_evt = self._evt_table.horizontalHeader()
        hh_evt.setSectionResizeMode(0, M3HeaderView.Interactive)
        hh_evt.setSectionResizeMode(1, M3HeaderView.Interactive)
        hh_evt.setSectionResizeMode(2, M3HeaderView.Stretch)
        hh_evt.setSectionResizeMode(3, M3HeaderView.Interactive)
        hh_evt.setSectionResizeMode(4, M3HeaderView.ResizeToContents)
        self._evt_table.setColumnWidth(0, ds.sp(SpacingToken.XXL) + ds.sp(SpacingToken.LG) + 34)
        self._evt_table.setColumnWidth(1, ds.sp(SpacingToken.XXL) + ds.sp(SpacingToken.MD) + 6)
        self._evt_table.setColumnWidth(3, ds.space_xxl)
        self._evt_table.setShowGrid(True)
        self._evt_table.setStyleSheet(ds.table_qss())
        self._evt_table.verticalHeader().setDefaultSectionSize(ds.table_row_min)
        self._evt_table.setEditTriggers(M3TableWidget.NoEditTriggers)
        self._evt_table.setSelectionBehavior(M3TableWidget.SelectRows)
        self._evt_table.setAlternatingRowColors(False)
        p3_layout.addWidget(self._evt_table, 1)

        # Bouton Ajouter événement
        evt_btn_row = QHBoxLayout()
        self._add_event_btn = M3Button(_("student_form.add_event"), variant=ButtonVariant.FILLED)
        self._add_event_btn.clicked.connect(self._on_add_event)
        evt_btn_row.addWidget(self._add_event_btn)
        evt_btn_row.addStretch()
        p3_layout.addLayout(evt_btn_row)

        # --- Page 4 : Dossiers (sections + fichiers) ---
        p4 = M3Frame()
        p4_layout = QVBoxLayout(p4)
        p4_layout.setContentsMargins(0, 0, 0, 0)
        from LarcSecretaire.views.dossier_panel import DossierPanel

        self._dossier_panel = DossierPanel(self._sid)
        # Temps réel : toute mutation d'une entrée (ajout/édition/suppression)
        # marque le dossier comme modifié et active l'indicateur « Enregistrer »,
        # même sans changer d'onglet.
        self._dossier_panel.entries_changed.connect(self._mark_dirty)
        p4_layout.addWidget(self._dossier_panel, 1)

        # --- Page 7 : Notes / Résultats ---
        p7 = M3Frame()
        p7_layout = QVBoxLayout(p7)
        p7_layout.setSpacing(ds.sp(SpacingToken.SM))
        p7_layout.addWidget(M3Label(_("student_form.grades_title"), style="title_small"))

        # Accès aux répertoires drive : relevés + bulletins (intranet + cloud)
        from LarcSecretaire.common.app_config import app_config as _acfg

        drive_row = QHBoxLayout()
        drive_row.setSpacing(ds.space_sm)
        for dkey, dtitle_key in [("releves", "student_form.drive_releves"), ("bulletins", "student_form.drive_bulletins")]:
            dcard = M3Card(variant=CardVariant.ELEVATED)
            dcl = dcard.content_layout()
            dcl.setSpacing(ds.space_sm)
            dcl.addWidget(M3Label(_(dtitle_key), style="title_small"))
            ddir = _acfg.get(f"{dkey}_dir", "")
            durl = _acfg.get(f"{dkey}_cloud_url", "")
            dir_lbl = M3Label(str(ddir), style="label_small")
            dir_lbl.setWordWrap(True)
            dcl.addWidget(dir_lbl)
            btns = QHBoxLayout()
            btns.setSpacing(ds.space_xs)
            b_intra = M3Button(_("student_form.drive_intranet"), variant=ButtonVariant.TONAL)
            b_intra.clicked.connect(lambda _=False, p=ddir: self._open_drive_dir(p))
            btns.addWidget(b_intra)
            b_cloud = M3Button(_("student_form.drive_cloud"), variant=ButtonVariant.FILLED)
            b_cloud.clicked.connect(lambda _=False, u=durl: self._open_drive_cloud(u))
            btns.addWidget(b_cloud)
            btns.addStretch()
            dcl.addLayout(btns)
            drive_row.addWidget(dcard, 1)
        p7_layout.addLayout(drive_row)

        self._grades_table = M3TableWidget()
        self._grades_table.set_headers(
            [
                _("student_form.grades_table_subject"),
                _("student_form.grades_table_grade"),
                _("student_form.grades_table_date"),
                _("student_form.grades_table_comment"),
            ]
        )
        hh_gr = self._grades_table.horizontalHeader()
        for i in range(4):
            hh_gr.setSectionResizeMode(i, M3HeaderView.Stretch)
        self._grades_table.setStyleSheet(ds.table_qss())
        self._grades_table.setEditTriggers(M3TableWidget.NoEditTriggers)
        self._grades_table.setAlternatingRowColors(False)
        p7_layout.addWidget(self._grades_table, 1)

        # --- Page 8 : Photos ---
        p8 = M3Frame()
        p8_layout = QVBoxLayout(p8)
        p8_layout.setSpacing(ds.sp(SpacingToken.MD))
        p8_layout.setAlignment(Qt.AlignCenter)

        # Photo en grand
        self._photo_large = QLabel()
        self._photo_large.setFixedSize(ds.sp(SpacingToken.XXXL) * 2, ds.sp(SpacingToken.XXXL) * 2)
        self._photo_large.setStyleSheet(f"background: {ds.p.primary_container}; border-radius: {ds.radius_sm}px;")
        self._photo_large.setAlignment(Qt.AlignCenter)
        p8_layout.addWidget(self._photo_large, 0, Qt.AlignCenter)

        # Bouton upload
        photo_btn_row = QHBoxLayout()
        photo_btn_row.setAlignment(Qt.AlignCenter)
        self._upload_photo_btn = M3Button(_("student_form.change_photo"), variant=ButtonVariant.FILLED)
        self._upload_photo_btn.clicked.connect(self._on_change_photo)
        photo_btn_row.addWidget(self._upload_photo_btn)
        p8_layout.addLayout(photo_btn_row)
        p8_layout.addStretch()

        # --- Page 5 : Confidentiel (restreint) ---
        p5 = M3Frame()
        p5_layout = QVBoxLayout(p5)
        p5_layout.setSpacing(ds.sp(SpacingToken.SM))
        from LarcSecretaire.common.session import UserRole
        from LarcSecretaire.common.session import session as _ses

        if _ses.role in (UserRole.ADMIN, UserRole.COORD, UserRole.SECR):
            conf_label = M3Label(_("student_form.confidential_notes"), style="headline_large")
            p5_layout.addWidget(conf_label)
            conf_info = M3Label(_("student_form.confidential_desc"), style="body_medium")
            conf_info.setStyleSheet(f"padding-bottom: {ds.sp(SpacingToken.SM)}px;")
            conf_info.setWordWrap(True)
            p5_layout.addWidget(conf_info)
            # Liste de documents confidentiels (description + pièces jointes),
            # HORS des sections du dossier → notes_json["confidentiel"]
            from LarcSecretaire.views.dossier_panel import ConfidentialPanel

            self._conf_panel = ConfidentialPanel(self._sid)
            self._conf_panel.entries_changed.connect(self._mark_dirty)
            p5_layout.addWidget(self._conf_panel, 1)
        else:
            deny = M3Label(_("student_form.confidential_restricted"), style="title_small")
            deny.setStyleSheet(f"padding: {ds.space_xl}px;")
            deny.setAlignment(Qt.AlignCenter)
            deny.setWordWrap(True)
            p5_layout.addWidget(deny)

        # Construire la sidebar + stack — avec NavButton (TONAL + icônes)
        # page_map EXPLICITE : l'ordre d'append des pages (p1,p2,p3,p4,p7,p8,p5)
        # diffère de l'ordre des onglets (p5=Confidentiel avant p7=Notes) → map directe.
        self._nav_stack = M3StackedWidget()
        # Onglet « Chronologie » : vue globale exposée par DossierPanel (Niveau 3),
        # ajoutée juste après « Dossiers » → onglet complet du dialogue.
        self._timeline_page = self._dossier_panel.timeline
        nav_pages = [
            (p1, "badge", _("student_form.tab_identity")),
            (p2_page, "home", _("student_form.tab_address")),
            (p3, "event", _("student_form.tab_events")),
            (p4, "folder", _("student_form.tab_documents")),
            (self._timeline_page, "timeline", _("dossier.timeline.title")),
            (p5, "lock", _("student_form.tab_confidential")),
            (p7, "school", _("student_form.tab_grades")),
            (p8, "photo_camera", _("student_form.tab_photos")),
        ]
        icon_sz = theme_manager.image.icon_btn
        self._dossier_nav_index = 0
        self._timeline_nav_index = 0
        for idx, (page, icon_name, label) in enumerate(nav_pages):
            if page is p4:
                self._dossier_nav_index = idx
            if page is self._timeline_page:
                self._timeline_nav_index = idx
            btn = M3Button(label, variant=ButtonVariant.TONAL)
            btn.setIcon(md3_icon(icon_name, color=theme_manager.palette.text_soft, size=icon_sz))
            btn.setIconSize(QSize(icon_sz, icon_sz))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.setChecked(idx == 0)
            btn.clicked.connect(lambda checked, i=idx: self._on_nav(i))
            nav_side.addWidget(btn)
            self._nav_btns.append(btn)
            self._nav_stack.addWidget(page)

        self._nav_stack.setCurrentIndex(0)
        nav_side.addStretch()
        nav_row.addLayout(nav_side)
        nav_row.addWidget(self._nav_stack, 1)
        layout.addLayout(nav_row, 1)
        layout.addStretch()

        # ── Chronologie : onglet complet + navigation depuis les sections ──
        # Le bouton « Chronologie » du rail Dossiers ouvre l'onglet du dialogue.
        self._dossier_panel.timeline_requested.connect(self._open_timeline_tab)
        # Double-clic dans la timeline → retour onglet Dossiers + édition dans la section.
        self._timeline_page.set_on_edit(self._edit_from_timeline)

    @safe_slot("Unknown._restyle")
    def _restyle(self):
        if hasattr(self, "_parents_table") and self._parents_table:
            self._parents_table.setStyleSheet(ds.table_qss())
        if hasattr(self, "_evt_table") and self._evt_table:
            self._evt_table.setStyleSheet(ds.table_qss())
        if hasattr(self, "_grades_table") and self._grades_table:
            self._grades_table.setStyleSheet(ds.table_qss())
        if hasattr(self, "_photo") and self._photo:
            self._photo.setStyleSheet(f"background: {ds.p.primary_container}; border-radius: {ds.radius_sm}px;")
        if hasattr(self, "_photo_large") and self._photo_large:
            self._photo_large.setStyleSheet(f"background: {ds.p.primary_container}; border-radius: {ds.radius_sm}px;")
        for w in self._inp_fields():
            w.setStyleSheet(ds.flat_input_qss())
        for w in self._date_fields():
            w.setStyleSheet(
                f"border: 1px solid {ds.p.outline}; border-radius: {ds.radius_xs}px; "
                f"padding: {ds.space_md}px; color: {ds.p.text_strong}; background: {ds.p.surface}; "
                f"QDateEdit QLineEdit {{ color: {ds.p.text_strong}; background: {ds.p.surface}; }}"
            )
            w.setFixedWidth(ds.sp(SpacingToken.XXL) + ds.sp(SpacingToken.MD))
        # Header élève : couleurs réactives au thème
        for lbl in (self._id_prenom, self._id_nom):
            lbl.setStyleSheet(f"font-weight: bold; color: {ds.p.text_strong};")
        for lbl in (self._id_classe, self._id_id):
            lbl.setStyleSheet(f"color: {ds.p.text_strong};")
        if hasattr(self, "_addr_status") and self._addr_status:
            self._addr_status.setStyleSheet(f"color: {ds.p.text_disabled};")
        if hasattr(self, "_inp_genre") and self._inp_genre:
            self._inp_genre.setStyleSheet(
                f"border: 1px solid {ds.p.outline}; border-radius: {ds.radius_xs}px; "
                f"padding: {ds.space_md}px; min-width: {ds.window_width * 3 // 20}px; "
                f"color: {ds.p.text_strong};"
            )
            self._inp_genre.setFixedWidth(ds.sp(SpacingToken.XXL) + ds.sp(SpacingToken.MD))
        # Ré-appliquer l'indicateur dirty (libellé du bouton Enregistrer) après
        # un changement de thème : sans effet de couleur, mais cohérent.
        if hasattr(self, "_save_btn") and self._save_btn:
            self._update_save_indicator()

    def _inp_fields(self):
        fields = []
        for attr in [
            "_inp_nom",
            "_inp_prenom",
            "_inp_email",
            "_inp_emailperso",
            "_inp_tel",
            "_inp_tel2",
            "_inp_addr2",
            "_inp_cp",
            "_inp_ville",
            "_inp_pays",
        ]:
            if hasattr(self, attr):
                fields.append(getattr(self, attr))
        return fields

    def _date_fields(self):
        fields = []
        for attr in ["_inp_date_joined", "_inp_date", "_inp_birthdate"]:
            if hasattr(self, attr):
                fields.append(getattr(self, attr))
        return fields

    @safe_slot("StudentEditDialog.on_nav")
    def _on_nav(self, index: int):
        self._nav_stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_btns):
            btn.setChecked(i == index)
        # Rafraîchir la chronologie à chaque affichage de son onglet
        if index == getattr(self, "_timeline_nav_index", None):
            self._dossier_panel.refresh_timeline()

    @safe_slot("Unknown._open_timeline_tab")
    def _open_timeline_tab(self):
        """Bouton « Chronologie » du rail Dossiers → ouvre l'onglet chronologie."""
        self._on_nav(self._timeline_nav_index)

    def _edit_from_timeline(self, entry: dict):
        """Double-clic dans la chronologie → retour onglet Dossiers + édition dans la section."""
        self._on_nav(self._dossier_nav_index)
        self._dossier_panel.edit_from_timeline(entry)

    # ── Indicateur « dossier modifié » ──

    @safe_slot("Unknown._mark_dirty")
    def _mark_dirty(self):
        """Une entrée du dossier a été ajoutée/modifiée/supprimée → dossier modifié.

        Connecté à DossierPanel.entries_changed : le dossier se met à jour en
        temps réel, même sans changer d'onglet. L'indicateur ne bascule qu'une
        fois (pas de rafraîchissement inutile à chaque signal).
        """
        if not self._dirty:
            self._dirty = True
            self._update_save_indicator()

    def _update_save_indicator(self):
        """Affiche/masque l'indicateur « modifications non enregistrées ».

        Texte seul (aucun QSS dur) : le libellé du bouton Enregistrer change,
        les couleurs restent celles du variant FILLED actif (thème réactif).
        """
        if not hasattr(self, "_save_btn") or self._save_btn is None:
            return
        if self._dirty:
            self._save_btn.setText(_("student_form.save_changes"))
        else:
            self._save_btn.setText(_("student_form.save"))

    def _get_class_language(self, classroom_id: int) -> int | None:
        conn = db.server_conn
        if not conn:
            return None
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT l.fk_language_id
                FROM larcauth_classroom c
                JOIN larcauth_level l ON l.id = c.fk_level_id
                WHERE c.id = %s
            """,
                (classroom_id,),
            )
            row = cur.fetchone()
            return row[0] if row else None
        except Exception as e:
            log(f"StudentEditDialog._get_class_language: {e}")
            return None

    def _load_genders(self, lang_id: int | None = None, include_gid: int | None = None):
        self._inp_genre.clear()
        self._inp_genre.addItem(_("student_form.gender_not_specified"), 0)
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            if lang_id:
                cur.execute("SELECT id, label FROM larcauth_gender WHERE fk_language_id = %s ORDER BY id", (lang_id,))
            else:
                cur.execute("SELECT id, label FROM larcauth_gender ORDER BY id")
            loaded = set()
            for gid, label in cur.fetchall():
                self._inp_genre.addItem(label, gid)
                loaded.add(gid)
            # Si le genre existant de l'élève n'est pas dans la langue, l'ajouter
            if include_gid is not None and include_gid not in loaded:
                cur.execute("SELECT label FROM larcauth_gender WHERE id = %s", (include_gid,))
                row = cur.fetchone()
                if row:
                    self._inp_genre.addItem(row[0], include_gid)
        except Exception as e:
            log(f"StudentEditDialog._load_genders: {e}")

    def _load_data(self):
        """Pré-remplit le formulaire avec les données existantes."""
        d = self._data
        sid = d["id"]

        # Photo
        px = QPixmap(get_photo_path(sid))
        if px.isNull():
            px = _make_avatar(d["last_name"], d["first_name"], 120)
        else:
            px = px.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._photo.setPixmap(px)

        # Identité — Nom en majuscules, prénom en plus grand
        self._id_prenom.setText(d.get("first_name", "") or "")
        self._id_nom.setText((d.get("last_name", "") or "").upper())
        self._id_classe.setText(_("student_form.class_label").format(label=d.get("classroom", "—")))
        self._id_id.setText(_("student_form.id_label").format(id=sid))

        # Champs
        self._inp_nom.setText(d.get("last_name", ""))
        self._inp_prenom.setText(d.get("first_name", ""))
        self._inp_email.setText(d.get("email", ""))
        self._inp_emailperso.setText(d.get("emailperso", "") or "")
        self._inp_tel.setText(d.get("tel_smartphone_1", "") or "")
        self._inp_tel2.setText(d.get("tel_maison", "") or "")
        raw_joined = d.get("date_joined", "")
        if raw_joined:
            self._inp_date_joined.setDate(QDate.fromString(str(raw_joined), "yyyy-MM-dd"))
        else:
            self._inp_date_joined.setDate(QDate())
        raw_date = d.get("date_entree", "")
        if raw_date:
            self._inp_date.setDate(QDate.fromString(str(raw_date), "yyyy-MM-dd"))
        else:
            self._inp_date.setDate(QDate())
        raw_birth = d.get("date_of_birth", "")
        if raw_birth:
            self._inp_birthdate.setDate(QDate.fromString(str(raw_birth), "yyyy-MM-dd"))
        else:
            self._inp_birthdate.setDate(QDate())
        # Recharger les genres selon la langue de la classe
        classroom_id = d.get("s_classroom_id")
        current_gid = d.get("fk_gender_id")
        if classroom_id:
            lang_id = self._get_class_language(classroom_id)
            self._load_genders(lang_id, include_gid=current_gid)
        gid = current_gid or 0
        idx = self._inp_genre.findData(gid)
        if idx >= 0:
            self._inp_genre.setCurrentIndex(idx)
        self._inp_addr1.setPlainText(d.get("address_line1", "") or "")
        self._inp_addr2.setText(d.get("address_line2", "") or "")
        self._inp_cp.setText(d.get("postal_code", "") or "")
        self._inp_ville.setText(d.get("city", "") or "")
        self._inp_pays.setText(d.get("country", "") or _("student_form.default_country"))
        raw_notes_json = d.get("notes_json") or None
        if raw_notes_json:
            if isinstance(raw_notes_json, str):
                import json

                try:
                    raw_notes_json = json.loads(raw_notes_json)
                except json.JSONDecodeError:
                    raw_notes_json = None
        if raw_notes_json and isinstance(raw_notes_json, dict):
            self._dossier_panel.set_data(raw_notes_json)
        else:
            # Fallback : importer les anciennes notes TEXT dans la section Autre
            old_notes = d.get("notes", "") or ""
            if old_notes:
                import json

                old_data = {
                    "autre": {
                        "intro": "<p>Notes importées de l'ancien système.</p>",
                        "entries": [
                            {
                                "no": 1,
                                "date": "",
                                "titre": "Anciennes notes",
                                "doc": old_notes[:500] + ("…" if len(old_notes) > 500 else ""),
                            }
                        ],
                    }
                }
                self._dossier_panel.set_data(old_data)
            else:
                self._dossier_panel.clear()

        # Initialiser les dossiers de fichiers
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "students", str(self._sid))
        dossiers_dir = os.path.join(base_dir, "dossiers")
        os.makedirs(dossiers_dir, exist_ok=True)
        conf_dir = os.path.join(base_dir, "confidentiel")
        os.makedirs(conf_dir, exist_ok=True)
        self._dossier_panel.set_directory(dossiers_dir)
        if hasattr(self, "_conf_panel"):
            self._conf_panel.set_directory(conf_dir)
            conf = raw_notes_json.get("confidentiel", {}) if isinstance(raw_notes_json, dict) else {}
            self._conf_panel.load_entries(conf.get("entries", []))

        self._load_parents()
        self._load_events()

        # Fiche santé : vit dans la section Médical du dossier
        health = raw_notes_json.get("health", {}) if isinstance(raw_notes_json, dict) else {}
        self._dossier_panel.set_health(health)

        # Grande photo pour l'onglet Photos
        px_large = QPixmap(get_photo_path(sid))
        if px_large.isNull():
            px_large = _make_avatar(d["last_name"], d["first_name"], 240)
        else:
            px_large = px_large.scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._photo_large.setPixmap(px_large)

        # Charger les notes/résultats
        self._load_grades()

    def _load_parents(self):
        self._parent_ids = []
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT sp.parent_id,
                       aec.last_name || ' ' || aec.first_name AS name,
                       COALESCE(sp.nature, par.nature, 'parent'),
                       aec.email,
                       COALESCE(aec.tel_smartphone_1, aec.tel_maison, '')
                FROM student_parent sp
                JOIN larcauth_aecuser aec ON aec.id = sp.parent_id
                LEFT JOIN larcauth_parent par ON par.aecuser_ptr_id = aec.id
                WHERE sp.student_id = %s
                ORDER BY aec.last_name
            """,
                (self._sid,),
            )
            rows = list(cur.fetchall())
            self._parent_ids = []
            self._parents_table.setRowCount(len(rows))
            for i, (pid, name, nat, em, tel) in enumerate(rows):
                self._parent_ids.append(pid)
                self._parents_table.setItem(i, 0, QTableWidgetItem(name))
                self._parents_table.setItem(i, 1, QTableWidgetItem(nat or ""))
                self._parents_table.setItem(i, 2, QTableWidgetItem(em or ""))
                self._parents_table.setItem(i, 3, QTableWidgetItem(tel or ""))
            self._parents_table.resizeColumnsToContents()
            self._parents_table.selectRow(0)
        except Exception as e:
            log(f"StudentEditDialog._load_parents: {e}")

    def _load_events(self):
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT se.event_at, se.event_type, se.note,
                       aec.last_name || ' ' || aec.first_name AS author,
                       CASE WHEN se.validated_by IS NOT NULL THEN '✓' ELSE '—' END
                FROM student_event se
                JOIN larcauth_aecuser aec ON aec.id = se.created_by
                WHERE se.student_id = %s
                ORDER BY se.event_at DESC LIMIT 100
            """,
                (self._sid,),
            )
            rows = cur.fetchall()
            self._evt_table.setRowCount(len(rows))
            for i, (evt_at, etype, note, author, validated) in enumerate(rows):
                self._evt_table.setItem(i, 0, QTableWidgetItem(str(evt_at)[:16]))
                it = QTableWidgetItem(_event_label(etype))
                it.setForeground(QColor(_event_color(etype)))
                self._evt_table.setItem(i, 1, it)
                self._evt_table.setItem(i, 2, QTableWidgetItem(note or ""))
                self._evt_table.setItem(i, 3, QTableWidgetItem(author))
                self._evt_table.setItem(i, 4, QTableWidgetItem(validated))
            self._evt_table.resizeColumnsToContents()
        except Exception as e:
            log(f"StudentEditDialog._load_events: {e}")

    @safe_slot("StudentEditDialog.save")
    def _save(self):
        conn = db.server_conn
        if not conn:
            QMessageBox.warning(self, _("common.dialog.error_title"), _("student_form.error.no_connection"))
            return
        try:
            cur = conn.cursor()
            from datetime import datetime

            now = datetime.now().isoformat()

            aec = {
                "last_name": self._inp_nom.text().strip(),
                "first_name": self._inp_prenom.text().strip(),
                "email": self._inp_email.text().strip() or "",
                "emailperso": self._inp_emailperso.text().strip() or None,
                "tel_smartphone_1": self._inp_tel.text().strip() or None,
                "tel_maison": self._inp_tel2.text().strip() or None,
                "date_joined": (
                    self._inp_date_joined.date().toString("yyyy-MM-dd")
                    if self._inp_date_joined.date().isValid() and not self._inp_date_joined.date().isNull()
                    else None
                ),
                "date_entree": (
                    self._inp_date.date().toString("yyyy-MM-dd") if self._inp_date.date().isValid() and not self._inp_date.date().isNull() else None
                ),
                "date_of_birth": (
                    self._inp_birthdate.date().toString("yyyy-MM-dd")
                    if self._inp_birthdate.date().isValid() and not self._inp_birthdate.date().isNull()
                    else None
                ),
                "fk_gender_id": self._inp_genre.currentData() or None,
                "updated": now,
            }
            cur.execute(
                "UPDATE larcauth_aecuser SET " + ", ".join(f"{k}=%s" for k in aec) + " WHERE id=%s",
                list(aec.values()) + [self._sid],
            )
            if cur.rowcount == 0:
                raise ValueError(f"Aucun enregistrement trouve pour l'ID {self._sid}")

            addr = {
                "address_line1": self._inp_addr1.toPlainText().strip() or None,
                "address_line2": self._inp_addr2.text().strip() or None,
                "postal_code": self._inp_cp.text().strip() or None,
                "city": self._inp_ville.text().strip() or None,
                "country": self._inp_pays.text().strip() or None,
            }
            fid = self._data.get("fk_foyer_id") or self._sid
            cols = list(addr.keys())
            vals = list(addr.values())
            cur.execute(
                "INSERT INTO foyer (id, "
                + ", ".join(cols)
                + ") VALUES (%s, "
                + ", ".join("%s" for _ in cols)
                + ") ON CONFLICT (id) DO UPDATE SET "
                + ", ".join(f"{k}=EXCLUDED.{k}" for k in cols),
                [fid] + vals,
            )
            notes_data = self._dossier_panel.get_data()
            notes_data["health"] = self._dossier_panel.get_health()
            if hasattr(self, "_conf_panel"):
                notes_data["confidentiel"] = {"intro": "", "entries": self._conf_panel.get_entries()}
            notes_json = json.dumps(notes_data)
            cur.execute(
                "UPDATE larcauth_student SET notes_json = %s WHERE aecuser_ptr_id = %s",
                (notes_json, self._sid),
            )
            if cur.rowcount == 0:
                raise ValueError(f"Aucun etudiant trouve pour l'ID {self._sid}")

            cur.execute("SET LOCAL app.sync_source = 'intranet'")
            cur.execute(f"SET LOCAL app.modified_by = {session.user_id}")
            changes = []
            for k in aec:
                old_v = str(self._data.get(k, ""))
                new_v = str(aec[k] or "")
                if old_v != new_v:
                    changes.append(k)
            if changes:
                audit.update_student(self._sid, f"Modifiés : {', '.join(changes)}")
            elif any(v is not None for v in addr.values()):
                audit.update_student(self._sid, "Adresse modifiée")

            conn.commit()
            log(f"StudentEditDialog: saved #{self._sid}")
            # Dossier sauvegardé → l'indicateur « Enregistrer » s'éteint.
            self._dirty = False
            self._update_save_indicator()

            QMessageBox.information(self, _("common.label.success"), _("student_form.success_updated"))
            self.accept()
        except Exception as e:
            conn.rollback()
            log(f"StudentEditDialog._save: {e}")
            QMessageBox.critical(self, _("common.dialog.error_title"), str(e))

    # ── Notes (formatage HTML) — supprimé, remplacé par NotesPanel JSON

    # ── Fichiers élèves ──

    def _student_dir(self) -> str:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "students")
        d = os.path.join(base, str(self._sid))
        os.makedirs(d, exist_ok=True)
        return d

    @safe_slot("StudentEditDialog.copy_parent_address")
    def _copy_parent_address(self):
        sel = self._parents_table.selectedItems()
        if not sel or not self._parent_ids:
            QMessageBox.warning(self, _("student_form.copy_address_title"), _("student_form.copy_address_none"))
            return
        row = sel[0].row()
        if row >= len(self._parent_ids):
            return
        pid = self._parent_ids[row]
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT address_line1, address_line2, postal_code, city, country
                FROM foyer WHERE id = %s
            """,
                (pid,),
            )
            row = cur.fetchone()
            if row and any(row):
                addr1, addr2, cp, ville, pays = row
                self._inp_addr1.setPlainText(addr1 or "")
                self._inp_addr2.setText(addr2 or "")
                self._inp_cp.setText(cp or "")
                self._inp_ville.setText(ville or "")
                if pays:
                    self._inp_pays.setText(pays)
                log(f"Copied address from parent #{pid} to student #{self._sid}")
                if hasattr(self, "_addr_status") and self._addr_status:
                    self._addr_status.hide()
            else:
                if hasattr(self, "_addr_status") and self._addr_status:
                    self._addr_status.setText(_("student_form.copy_address_no_address"))
                    self._addr_status.show()
        except Exception as e:
            log(f"StudentEditDialog._copy_parent_address: {e}")

    # ──── Ajouter un événement ────

    @safe_slot("StudentEditDialog.on_add_event")
    def _on_add_event(self):
        """Ouvre le dialogue d'ajout d'événement pour cet élève."""
        from LarcSecretaire.views.supervisor_panel import EventDialog

        dlg = EventDialog(
            self._sid,
            f"{self._data.get('last_name', '?')} {self._data.get('first_name', '?')}",
            self,
        )
        if dlg.exec():
            self._load_events()  # Recharger le tableau

    # ──── Changer la photo ────

    @safe_slot("StudentEditDialog.on_change_photo")
    def _on_change_photo(self):
        """Ouvre un FileDialog pour changer la photo de l'élève."""
        path, _f = QFileDialog.getOpenFileName(
            self,
            _("student_form.select_photo"),
            "",
            _("student_form.photo_filter"),
        )
        if not path:
            return
        from LarcSecretaire.common.photos import save_photo

        try:
            save_photo(self._sid, path)
            # Recharger les deux affichages (petite + grande photo)
            px = QPixmap(get_photo_path(self._sid))
            if not px.isNull():
                px_small = px.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._photo.setPixmap(px_small)
                px_large = px.scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._photo_large.setPixmap(px_large)
        except Exception as e:
            log(f"StudentEditDialog._on_change_photo: {e}")
            QMessageBox.critical(self, _("common.dialog.error_title"), str(e))

    # ──── Charger les notes/résultats ────

    def _load_grades(self):
        """Charge les notes/résultats depuis la DB."""
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT
                        sub.label AS subject,
                        eg.grade,
                        eg.date_grade,
                        eg.comment
                    FROM evaluation_grade eg
                    JOIN evaluation_subject sub ON sub.id = eg.fk_subject_id
                    WHERE eg.fk_student_id = %s
                    ORDER BY eg.date_grade DESC, sub.label
                    LIMIT 100
                """,
                    (self._sid,),
                )
                rows = cur.fetchall()
            except Exception:
                rows = []
            self._grades_table.setRowCount(len(rows))
            for i, (subject, grade, date_grade, comment) in enumerate(rows):
                self._grades_table.setItem(i, 0, QTableWidgetItem(subject or ""))
                self._grades_table.setItem(i, 1, QTableWidgetItem(str(grade) if grade else ""))
                self._grades_table.setItem(i, 2, QTableWidgetItem(str(date_grade)[:10] if date_grade else ""))
                self._grades_table.setItem(i, 3, QTableWidgetItem(comment or ""))
            if not rows:
                self._grades_table.setRowCount(1)
                self._grades_table.setItem(0, 0, QTableWidgetItem(_("student_form.no_grades")))
            self._grades_table.resizeColumnsToContents()
        except Exception as e:
            log(f"StudentEditDialog._load_grades: {e}")

    # ──── Accès répertoires drive (relevés / bulletins) ────

    @safe_slot("StudentEditDialog.open_drive_dir")
    def _open_drive_dir(self, path: str):
        """Ouvre le répertoire intranet dans l'Explorateur (créé s'il manque)."""
        import subprocess

        path = path or ""
        if not path:
            QMessageBox.information(self, _("common.dialog.info_title"), _("student_form.drive_dir_missing"))
            return
        try:
            os.makedirs(path, exist_ok=True)
            subprocess.Popen(["explorer", path])
        except Exception as e:
            log(f"StudentEditDialog._open_drive_dir: {e}")
            QMessageBox.critical(self, _("common.dialog.error_title"), str(e))

    @safe_slot("StudentEditDialog.open_drive_cloud")
    def _open_drive_cloud(self, url: str):
        """Ouvre l'URL cloud (Supabase Storage) dans le navigateur par défaut."""
        import webbrowser

        if not url:
            QMessageBox.information(self, _("common.dialog.info_title"), _("student_form.drive_url_missing"))
            return
        webbrowser.open(url)

    @safe_slot("StudentEditDialog.add_parent_link")
    def _add_parent_link(self):
        dlg = M3Dialog(self)
        dlg.setWindowTitle(_("student_form.add_parent"))
        dlg.setMinimumSize(ds.golden_height(610), ds.golden_height(610))
        dlg.setStyleSheet(f"background: {ds.p.surface}; color: {ds.p.text_strong};")
        layout = QVBoxLayout(dlg)
        search_inp = M3TextField()
        search_inp.setPlaceholderText(_("student_form.search_parent_placeholder"))
        search_inp.setStyleSheet(ds.flat_input_qss())
        layout.addWidget(search_inp)
        result_list = M3ListWidget()
        result_list.setStyleSheet(ds.table_qss())
        layout.addWidget(result_list, 1)
        buttons = M3DialogButtonBox(M3DialogButtonBox.Ok | M3DialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        def on_search(text):
            if len(text.strip()) < 3:
                result_list.clear()
                return
            conn = db.server_conn
            if not conn:
                return
            try:
                cur = conn.cursor()
                q = "%" + text.strip() + "%"
                cur.execute(
                    """
                    SELECT id, last_name, first_name, email
                    FROM larcauth_aecuser
                    WHERE type_parentutor = TRUE
                      AND (LOWER(last_name) LIKE LOWER(%s)
                           OR LOWER(first_name) LIKE LOWER(%s)
                           OR LOWER(email) LIKE LOWER(%s))
                      AND id NOT IN (
                           SELECT parent_id FROM student_parent WHERE student_id = %s)
                    ORDER BY last_name, first_name
                    LIMIT 50
                """,
                    (q, q, q, self._sid),
                )
                result_list.clear()
                self._search_parents_data = []
                for pid, ln, fn, em in cur.fetchall():
                    disp = f"{ln or ''} {fn or ''} ({em or 'pas d e-mail'})"
                    result_list.addItem(disp)
                    self._search_parents_data.append(pid)
            except Exception as e:
                log(f"_add_parent_link search: {e}")

        search_inp.textChanged.connect(on_search)
        self._search_parents_data = []

        if dlg.exec() == M3Dialog.Accepted:
            cur_sel = result_list.currentRow()
            if cur_sel < 0 or cur_sel >= len(self._search_parents_data):
                return
            pid = self._search_parents_data[cur_sel]
            conn = db.server_conn
            if not conn:
                return
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO student_parent (student_id, parent_id) VALUES (%s, %s)
                    ON CONFLICT DO NOTHING""",
                    (self._sid, pid),
                )
                log(f"Linked parent #{pid} to student #{self._sid}")
            except Exception as e:
                log(f"_add_parent_link insert: {e}")
                QMessageBox.critical(self, _("common.dialog.error_title"), str(e))
            self._load_parents()

    @safe_slot("StudentEditDialog.edit_parent_nature")
    def _edit_parent_nature(self):
        sel = self._parents_table.selectedItems()
        if not sel or not self._parent_ids:
            QMessageBox.warning(self, _("student_form.nature_dialog_title"), _("parent.error.no_parent_selected"))
            return
        row = sel[0].row()
        if row >= len(self._parent_ids):
            return
        pid = self._parent_ids[row]
        nature, ok = QInputDialog.getText(self, _("student_form.nature_prompt_title"), _("student_form.nature_prompt_msg"))
        if not ok:
            return
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE student_parent SET nature = %s WHERE student_id = %s AND parent_id = %s",
                (nature.strip(), self._sid, pid),
            )
            log(f"Updated nature for parent #{pid} of student #{self._sid}: {nature.strip()}")
            self._load_parents()
        except Exception as e:
            log(f"_edit_parent_nature: {e}")
            QMessageBox.critical(self, _("common.dialog.error_title"), str(e))

    @safe_slot("StudentEditDialog.remove_parent_link")
    def _remove_parent_link(self):
        sel = self._parents_table.selectedItems()
        if not sel or not self._parent_ids:
            QMessageBox.warning(self, _("student_form.remove_parent"), _("parent.error.no_parent_selected"))
            return
        row = sel[0].row()
        if row >= len(self._parent_ids):
            return
        pid = self._parent_ids[row]
        confirm = QMessageBox.question(
            self,
            _("student_form.remove_confirm_title"),
            _("student_form.remove_confirm_msg"),
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM student_parent WHERE student_id = %s AND parent_id = %s", (self._sid, pid))
            log(f"Removed parent #{pid} from student #{self._sid}")
            self._load_parents()
        except Exception as e:
            log(f"_remove_parent_link: {e}")
            QMessageBox.critical(self, _("common.dialog.error_title"), str(e))

    def _build_full_html(self) -> str:
        d = self._data
        parts = ["<html><head><meta charset='utf-8'></head><body>"]

        def esc(s):
            import html

            return html.escape(str(s or ""))

        # En-tête
        parts.append(f"<h1>{esc(d.get('last_name', ''))} {esc(d.get('first_name', ''))}</h1>")
        parts.append("<table cellpadding='3' cellspacing='0' style='margin-bottom:12px;'>")
        parts.append(
            f"<tr><td><b>ID</b></td><td>{esc(d.get('id', ''))}</td><td style='padding-left:24px;'><b>Classe</b></td><td>{esc(d.get('classroom', ''))}</td></tr>"
        )
        parts.append(
            f"<tr><td><b>Date naissance</b></td><td>{esc(d.get('date_of_birth', ''))}</td>"
            f"<td style='padding-left:24px;'><b>Date entrée</b></td><td>{esc(d.get('date_entree', ''))}</td></tr>"
        )

        # Genre — requêter le label depuis la DB
        gid = d.get("fk_gender_id")
        gender_label = ""
        if gid:
            try:
                cur = db.server_conn.cursor()
                cur.execute("SELECT label FROM larcauth_gender WHERE id = %s", (gid,))
                row = cur.fetchone()
                if row:
                    gender_label = row[0]
            except Exception:
                pass
        parts.append(
            f"<tr><td><b>Genre</b></td><td>{esc(gender_label)}</td>"
            f"<td style='padding-left:24px;'><b>ID Foyer</b></td><td>{esc(d.get('fk_foyer_id', ''))}</td></tr>"
        )
        parts.append("</table>")

        # Contact
        parts.append("<h2>Contact</h2>")
        parts.append("<table cellpadding='3' cellspacing='0' style='margin-bottom:12px;'>")
        parts.append(f"<tr><td><b>Email</b></td><td>{esc(d.get('email', ''))}</td></tr>")
        parts.append(f"<tr><td><b>Email personnel</b></td><td>{esc(d.get('emailperso', ''))}</td></tr>")
        parts.append(f"<tr><td><b>Téléphone portable</b></td><td>{esc(d.get('tel_smartphone_1', ''))}</td></tr>")
        parts.append(f"<tr><td><b>Téléphone fixe</b></td><td>{esc(d.get('tel_maison', ''))}</td></tr>")
        parts.append("</table>")

        # Adresse
        parts.append("<h2>Adresse</h2>")
        parts.append(
            f"<p>{esc(d.get('address_line1', ''))}<br>"
            f"{esc(d.get('address_line2', ''))}<br>"
            f"{esc(d.get('postal_code', ''))} {esc(d.get('city', ''))}<br>"
            f"{esc(d.get('country', ''))}</p>"
        )

        # Parents
        parts.append("<h2>Parents / Tuteurs</h2>")
        if self._parents_table.rowCount() > 0:
            parts.append("<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;width:100%;margin-bottom:12px;'>")
            parts.append("<tr><th>Nom</th><th>Nature</th><th>Email</th><th>Téléphone</th></tr>")
            for i in range(self._parents_table.rowCount()):

                def _cell(col):
                    item = self._parents_table.item(i, col)
                    return esc(item.text()) if item and item.text() else ""

                parts.append(f"<tr><td>{_cell(0)}</td><td>{_cell(1)}</td><td>{_cell(2)}</td><td>{_cell(3)}</td></tr>")
            parts.append("</table>")
        else:
            parts.append("<p><i>Aucun parent/tuteur enregistré.</i></p>")

        # Notes structurées
        parts.append("<h2>Notes</h2>")
        section_labels = {
            "confidentielle": _("notes.section.confidential"),
            "medicale": _("notes.section.medical"),
            "pedagogique": _("notes.section.pedagogic"),
            "administrative": _("notes.section.administrative"),
            "communication": _("notes.section.communication"),
            "orientation": _("notes.section.orientation"),
            "autre": _("notes.section.other"),
        }
        notes_data = self._notes_panel.get_json() if hasattr(self, "_notes_panel") else {}
        has_notes = False
        for key, label in section_labels.items():
            sec = notes_data.get(key, {})
            raw_intro = (sec.get("intro") or "").strip()
            entries = sec.get("entries", [])
            if not raw_intro and not any(e.get("titre") or e.get("doc") for e in entries):
                continue
            has_notes = True
            parts.append(f"<h3>{esc(label)}</h3>")
            if raw_intro:
                parts.append(f"<div>{raw_intro}</div>")
            if entries:
                parts.append("<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;width:100%;margin-bottom:8px;'>")
                parts.append("<tr><th>N°</th><th>Date</th><th>Titre</th><th>Document / Note</th></tr>")
                for e in entries:
                    if e.get("titre") or e.get("doc") or e.get("date"):
                        parts.append(
                            f"<tr><td>{esc(e.get('no', ''))}</td><td>{esc(e.get('date', ''))}</td>"
                            f"<td>{esc(e.get('titre', ''))}</td><td>{esc(e.get('doc', ''))}</td></tr>"
                        )
                parts.append("</table>")
        if not has_notes:
            parts.append("<p><i>Aucune note.</i></p>")

        # Événements
        parts.append("<h2>Événements</h2>")
        if self._evt_table.rowCount() > 0:
            parts.append("<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse;width:100%;margin-bottom:12px;'>")
            parts.append("<tr><th>Date/Heure</th><th>Type</th><th>Note</th><th>Par</th><th>Validé</th></tr>")
            for i in range(self._evt_table.rowCount()):

                def _ecell(col):
                    item = self._evt_table.item(i, col)
                    return esc(item.text()) if item and item.text() else ""

                parts.append(f"<tr><td>{_ecell(0)}</td><td>{_ecell(1)}</td><td>{_ecell(2)}</td><td>{_ecell(3)}</td><td>{_ecell(4)}</td></tr>")
            parts.append("</table>")
        else:
            parts.append("<p><i>Aucun événement.</i></p>")

        parts.append("</body></html>")
        return "\n".join(parts)

    @safe_slot("StudentEditDialog.export_pdf")
    def _export_pdf(self):
        html = self._build_full_html()
        d = self._data
        default_name = _("student_form.export_pdf_file").format(last=d.get("last_name", ""), first=d.get("first_name", ""))
        path, _f = QFileDialog.getSaveFileName(self, _("student_form.pdf"), default_name, "Fichier PDF (*.pdf)")
        if not path:
            return
        try:
            doc = QTextDocument()
            doc.setHtml(html)
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            printer.setPageSize(QPrinter.A4)
            doc.print_(printer)
            log(f"Export PDF #{d['id']}: {path}")
            QMessageBox.information(self, _("student_form.pdf"), _("student_form.export_pdf_success").format(path=path))
        except Exception as e:
            log(f"Export PDF error: {e}")
            QMessageBox.critical(self, _("student_form.export_pdf_error"), str(e))

    @safe_slot("StudentEditDialog.export_word")
    def _export_word(self):
        html = self._build_full_html()
        d = self._data
        default_name = _("student_form.export_word_file").format(last=d.get("last_name", ""), first=d.get("first_name", ""))
        path, _f = QFileDialog.getSaveFileName(self, _("student_form.word"), default_name, "Document HTML (*.html *.htm)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            log(f"Export Word #{d['id']}: {path}")
            QMessageBox.information(self, _("student_form.word"), _("student_form.export_word_success").format(path=path))
        except Exception as e:
            log(f"Export Word error: {e}")
            QMessageBox.critical(self, _("student_form.export_word_error"), str(e))


# ──────────────────────────────────────────────
#   StudentCreateDialog — Création d'un élève
# ──────────────────────────────────────────────


class StudentCreateDialog(ThemedDialog):
    """
    Fenêtre de création d'élève — grand formulaire, polices larges.

    Le slot libre est détecté automatiquement.
    ID = classroom_id × 100 + slot (gabarit).
    """

    def __init__(self, parent=None, preselected_class: int | None = None):
        super().__init__(parent)
        self.setWindowTitle(_("student_form.new_student_title"))
        # 987×610 = paire dorée (610 = sidebar + golden_width(sidebar) ; 987 = golden_width(610))
        _min_h = ds.sidebar_width + ds.golden_width(ds.sidebar_width)  # 610
        self.setMinimumSize(ds.golden_width(_min_h), _min_h)  # 987×610
        self._result_data: dict | None = None
        self._class_id: int | None = None
        self._next_free: int | None = None
        self._sid: int | None = None
        self._parent_ids: list[int] = []
        self._search_parents_data: list[int] = []
        self._classes: list[tuple] = []
        self._class_btns: dict[int, M3Button] = {}
        self._preselected_class = preselected_class
        self._init_ui()
        self._load_classes()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(ds.space_md)
        layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)

        self._class_title = M3Label(_("student_form.new_student_label"), style="title_small")
        layout.addWidget(self._class_title)

        if self._preselected_class:
            self._class_info = M3Label(style="body_medium")
            self._class_info.setStyleSheet(f"padding-bottom: {ds.space_xs}px;")
            layout.addWidget(self._class_info)
            self._class_grid = None
        else:
            cl_label = M3Label(_("student_form.class_selector"), style="label_small")
            cl_label.setStyleSheet(f"font-weight: bold; color: {ds.p.text_strong};")
            layout.addWidget(cl_label)
            self._class_grid = M3Frame()
            self._class_grid_layout = QVBoxLayout(self._class_grid)
            self._class_grid_layout.setContentsMargins(0, 0, 0, 0)
            self._class_grid_layout.setSpacing(ds.space_xxs)
            layout.addWidget(self._class_grid)

        # Photo + identité + boutons (toujours visibles)
        photo_row = QHBoxLayout()
        self._photo = QLabel()
        self._photo.setFixedSize(ds.sp(SpacingToken.XXXL), ds.sp(SpacingToken.XXXL))
        self._photo.setStyleSheet(f"background: {ds.p.primary_container}; border-radius: {ds.radius_sm}px;")
        self._photo.setAlignment(Qt.AlignCenter)
        photo_row.addWidget(self._photo)

        id_col = QVBoxLayout()
        id_col.setSpacing(ds.space_xxs)
        # Ligne 1 : PRÉNOM (plus grand) + NOM (majuscules) — live depuis les champs
        name_row = QHBoxLayout()
        name_row.setSpacing(ds.space_sm)
        self._id_prenom = M3Label("", style="headline_large")
        self._id_prenom.setStyleSheet(f"font-weight: bold; color: {ds.p.text_strong};")
        name_row.addWidget(self._id_prenom)
        self._id_nom = M3Label("", style="title_large")
        self._id_nom.setStyleSheet(f"font-weight: bold; color: {ds.p.text_strong};")
        name_row.addWidget(self._id_nom)
        name_row.addStretch()
        id_col.addLayout(name_row)
        # Ligne 2 : Classe
        self._id_classe = M3Label("", style="body_medium")
        self._id_classe.setStyleSheet(f"color: {ds.p.text_strong};")
        id_col.addWidget(self._id_classe)
        # Ligne 3 : Id
        self._id_id = M3Label("", style="body_medium")
        self._id_id.setStyleSheet(f"color: {ds.p.text_strong};")
        id_col.addWidget(self._id_id)
        id_col.addStretch()
        photo_row.addLayout(id_col, 1)

        # Boutons d'action verticaux à droite
        btn_col = QVBoxLayout()
        btn_col.setSpacing(ds.space_sm)

        self._create_btn = M3Button(_("student_form.create_button"), variant=ButtonVariant.FILLED)
        self._create_btn.setEnabled(False)
        self._create_btn.clicked.connect(self._on_create)
        self._create_btn.setMinimumWidth(ds.sp(SpacingToken.XXL))
        btn_col.addWidget(self._create_btn)

        self._cancel_btn = M3Button(_("student_form.cancel_button"), variant=ButtonVariant.OUTLINED)
        self._cancel_btn.clicked.connect(self.reject)
        self._cancel_btn.setMinimumWidth(ds.sp(SpacingToken.XXL))
        btn_col.addWidget(self._cancel_btn)

        btn_col.addStretch()
        photo_row.addLayout(btn_col)

        layout.addLayout(photo_row)

        def _lbl(t):
            lbl = M3Label(t, style="body_medium")
            lbl.setStyleSheet(f"font-weight: bold; color: {ds.p.text_strong};")
            lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            return lbl

        # Champs (créés avant les onglets)
        self._inp_nom = M3TextField()
        self._inp_nom.setStyleSheet(ds.flat_input_qss())
        self._inp_nom.setPlaceholderText(_("student_form.last_name_placeholder"))
        self._inp_prenom = M3TextField()
        self._inp_prenom.setStyleSheet(ds.flat_input_qss())
        self._inp_prenom.setPlaceholderText(_("student_form.first_name_placeholder"))
        self._inp_email = M3TextField()
        self._inp_email.setStyleSheet(ds.flat_input_qss())
        self._inp_email.setPlaceholderText(_("student_form.email_placeholder"))
        self._inp_emailperso = M3TextField()
        self._inp_emailperso.setStyleSheet(ds.flat_input_qss())
        self._inp_emailperso.setPlaceholderText(_("student_form.email_personal_placeholder"))
        self._inp_tel = M3TextField()
        self._inp_tel.setStyleSheet(ds.flat_input_qss())
        self._inp_tel.setPlaceholderText(_("student_form.phone_placeholder"))
        self._inp_tel2 = M3TextField()
        self._inp_tel2.setStyleSheet(ds.flat_input_qss())
        self._inp_tel2.setPlaceholderText(_("student_form.phone_fixed_placeholder"))
        self._inp_date_joined = M3DateEdit()
        self._inp_date_joined.setDisplayFormat("yyyy-MM-dd")
        self._inp_date_joined.setCalendarPopup(True)
        self._inp_date_joined.setSpecialValueText(" ")
        self._inp_date_joined.setDate(QDate())
        self._inp_date_joined.setStyleSheet(
            f"border: 1px solid {ds.p.outline}; border-radius: {ds.radius_xs}px; padding: {ds.space_md}px; color: {ds.p.text_strong};"
        )
        self._inp_date = M3DateEdit()
        self._inp_date.setDisplayFormat("yyyy-MM-dd")
        self._inp_date.setCalendarPopup(True)
        self._inp_date.setSpecialValueText(" ")
        self._inp_date.setDate(QDate())
        self._inp_date.setStyleSheet(f"border: 1px solid {ds.p.outline}; border-radius: {ds.radius_xs}px; padding: {ds.space_md}px; color: {ds.p.text_strong};")
        self._inp_genre = M3ComboBox()
        self._inp_genre.setStyleSheet(
            f"border: 1px solid {ds.p.outline}; border-radius: {ds.radius_xs}px; padding: {ds.space_md}px; min-width: {ds.window_width * 3 // 20}px;"
        )
        self._load_genders()
        self._inp_birthdate = M3DateEdit()
        self._inp_birthdate.setDisplayFormat("yyyy-MM-dd")
        self._inp_birthdate.setCalendarPopup(True)
        self._inp_birthdate.setSpecialValueText(" ")
        self._inp_birthdate.setDate(QDate())
        self._inp_birthdate.setStyleSheet(
            f"border: 1px solid {ds.p.outline}; border-radius: {ds.radius_xs}px; padding: {ds.space_md}px; color: {ds.p.text_strong};"
        )
        self._inp_addr1 = M3TextEdit()
        self._inp_addr1.setStyleSheet(ds.flat_input_qss())
        self._inp_addr1.setFixedHeight(ds.sp(SpacingToken.XXL))
        self._inp_addr1.setPlaceholderText(_("student_form.street_placeholder"))
        self._inp_addr2 = M3TextField()
        self._inp_addr2.setStyleSheet(ds.flat_input_qss())
        self._inp_addr2.setPlaceholderText(_("student_form.address_complement"))
        self._inp_cp = M3TextField()
        self._inp_cp.setStyleSheet(ds.flat_input_qss())
        self._inp_cp.setPlaceholderText(_("student_form.zip_placeholder"))
        self._inp_ville = M3TextField()
        self._inp_ville.setStyleSheet(ds.flat_input_qss())
        self._inp_ville.setPlaceholderText(_("student_form.city_placeholder"))
        self._inp_pays = M3TextField(_("student_form.default_country"))
        self._inp_pays.setStyleSheet(ds.flat_input_qss())

        # Sidebar verticale + QStackedWidget (même pattern que StudentEditDialog)
        nav_row = QHBoxLayout()
        nav_row.setSpacing(ds.sp(SpacingToken.SM))
        nav_side = QVBoxLayout()
        nav_side.setSpacing(ds.space_sm)
        nav_side.setContentsMargins(0, 0, ds.sp(SpacingToken.SM), 0)

        self._nav_btns: list[M3Button] = []

        # --- Page 1 : Identité & Contact ---
        p1 = M3Frame()
        p1_layout = QVBoxLayout(p1)
        p1_layout.setSpacing(ds.sp(SpacingToken.MD))

        # Carte Identité
        id_card = M3Card(variant=CardVariant.ELEVATED)
        id_cl = id_card.content_layout()
        id_cl.setSpacing(ds.sp(SpacingToken.SM))
        id_cl.addWidget(M3Label(_("student_form.tab_identity"), style="title_small"))
        id_grid = QGridLayout()
        id_grid.setSpacing(ds.sp(SpacingToken.SM))
        id_grid.setColumnStretch(0, 1)
        id_grid.setColumnStretch(1, 1)
        r = 0
        id_grid.addWidget(_lbl(_("student_form.first_name_label")), r, 0)
        id_grid.addWidget(_lbl(_("student_form.last_name_label")), r, 1)
        r += 1
        id_grid.addWidget(self._inp_prenom, r, 0)
        id_grid.addWidget(self._inp_nom, r, 1)
        r += 1
        id_grid.addWidget(_lbl(_("student_form.gender_label")), r, 0)
        r += 1
        id_grid.addWidget(self._inp_genre, r, 0)
        self._inp_genre.setFixedWidth(ds.sp(SpacingToken.XXL) + ds.sp(SpacingToken.XL))
        id_cl.addLayout(id_grid)
        p1_layout.addWidget(id_card)

        # Carte Dates
        dt_card = M3Card(variant=CardVariant.ELEVATED)
        dt_cl = dt_card.content_layout()
        dt_cl.setSpacing(ds.sp(SpacingToken.SM))
        dt_cl.addWidget(M3Label("Dates", style="title_small"))
        dt_grid = QGridLayout()
        dt_grid.setSpacing(ds.sp(SpacingToken.SM))
        for i in range(6):
            dt_grid.setColumnStretch(i, 1)
        for row, (lbl, widget) in enumerate(
            [
                (_("student_form.arrival_label"), self._inp_date_joined),
                (_("student_form.entry_date"), self._inp_date),
                (_("student_form.birth_date"), self._inp_birthdate),
            ]
        ):
            dt_grid.addWidget(M3Label(lbl, style="body_medium"), row * 2, 0, 1, 3)
            dt_grid.addWidget(widget, row * 2 + 1, 0, 1, 3)
        dt_cl.addLayout(dt_grid)
        p1_layout.addWidget(dt_card)

        # Carte Contact
        ct_card = M3Card(variant=CardVariant.ELEVATED)
        ct_cl = ct_card.content_layout()
        ct_cl.setSpacing(ds.sp(SpacingToken.SM))
        ct_cl.addWidget(M3Label("Contact", style="title_small"))
        ct_grid = QGridLayout()
        ct_grid.setSpacing(ds.sp(SpacingToken.SM))
        ct_grid.setColumnStretch(0, 1)
        ct_grid.setColumnStretch(1, 1)
        r = 0
        ct_grid.addWidget(_lbl(_("student_form.email_label")), r, 0)
        ct_grid.addWidget(_lbl(_("student_form.email_personal")), r, 1)
        r += 1
        ct_grid.addWidget(self._inp_email, r, 0)
        ct_grid.addWidget(self._inp_emailperso, r, 1)
        r += 1
        ct_grid.addWidget(_lbl(_("student_form.phone_mobile")), r, 0)
        ct_grid.addWidget(_lbl(_("student_form.phone_fixed")), r, 1)
        r += 1
        ct_grid.addWidget(self._inp_tel, r, 0)
        ct_grid.addWidget(self._inp_tel2, r, 1)
        ct_cl.addLayout(ct_grid)
        p1_layout.addWidget(ct_card)
        p1_layout.addStretch()

        # --- Page 2 : Adresse & Parents ---
        p2_page = M3Frame()
        p2_page_layout = QVBoxLayout(p2_page)
        p2_page_layout.setSpacing(ds.sp(SpacingToken.MD))

        # Carte Parents
        par_card = M3Card(variant=CardVariant.ELEVATED)
        par_cl = par_card.content_layout()
        par_cl.setSpacing(ds.sp(SpacingToken.SM))
        par_cl.addWidget(M3Label(_("student_form.parents_title"), style="title_small"))

        self._parents_table = M3TableWidget()
        self._parents_table.set_headers(
            [
                _("student_form.parents_table_nom"),
                _("student_form.parents_table_nature"),
                _("student_form.parents_table_email"),
                _("student_form.parents_table_phone"),
            ]
        )
        self._parents_table.horizontalHeader().setStretchLastSection(True)
        self._parents_table.setEditTriggers(M3TableWidget.NoEditTriggers)
        self._parents_table.setSelectionBehavior(M3TableWidget.SelectRows)
        self._parents_table.setShowGrid(True)
        hh = self._parents_table.horizontalHeader()
        hh.setFixedHeight(ds.field_height)
        self._parents_table.setStyleSheet(ds.table_qss())
        self._parents_table.verticalHeader().setDefaultSectionSize(ds.table_row_min)
        self._parents_table.setMaximumHeight(ds.sp(SpacingToken.XXXL))
        par_cl.addWidget(self._parents_table)

        parent_tools = QHBoxLayout()
        parent_tools.setSpacing(ds.sp(SpacingToken.SM))
        add_par_btn = M3Button(_("student_form.add_parent"), variant=ButtonVariant.FILLED)
        add_par_btn.clicked.connect(self._add_parent_link)
        parent_tools.addWidget(add_par_btn)
        edit_par_btn = M3Button(_("student_form.edit_nature"), variant=ButtonVariant.TONAL)
        edit_par_btn.clicked.connect(self._edit_parent_nature)
        parent_tools.addWidget(edit_par_btn)
        remove_par_btn = M3Button(_("student_form.remove_parent"), variant=ButtonVariant.OUTLINED)
        remove_par_btn.clicked.connect(self._remove_parent_link)
        parent_tools.addWidget(remove_par_btn)
        copy_btn = M3Button(_("student_form.copy_address"), variant=ButtonVariant.TONAL)
        copy_btn.clicked.connect(self._copy_parent_address)
        parent_tools.addWidget(copy_btn)
        parent_tools.addStretch()
        par_cl.addLayout(parent_tools)
        # Q2 — état vide INLINE (jamais de QMessageBox modal pour zéro résultat)
        self._addr_status = M3Label("", style="body_small")
        self._addr_status.setWordWrap(True)
        self._addr_status.setStyleSheet(f"color: {ds.p.text_disabled};")
        self._addr_status.hide()
        par_cl.addWidget(self._addr_status)
        p2_page_layout.addWidget(par_card)

        # Carte Adresse
        addr_card = M3Card(variant=CardVariant.ELEVATED)
        addr_cl = addr_card.content_layout()
        addr_cl.setSpacing(ds.sp(SpacingToken.SM))
        addr_cl.addWidget(M3Label(_("student_form.address_title"), style="title_small"))

        addr_cl.addWidget(self._inp_addr1)
        addr_cl.addWidget(self._inp_addr2)
        addr_grid = QGridLayout()
        addr_grid.setSpacing(ds.sp(SpacingToken.SM))
        addr_grid.setColumnStretch(0, 1)
        addr_grid.setColumnStretch(1, 1)
        addr_grid.addWidget(_lbl(_("student_form.zip_label")), 0, 0)
        addr_grid.addWidget(_lbl(_("student_form.city_label")), 0, 1)
        addr_grid.addWidget(self._inp_cp, 1, 0)
        addr_grid.addWidget(self._inp_ville, 1, 1)
        addr_grid.addWidget(_lbl(_("student_form.country_label")), 2, 0)
        addr_grid.addWidget(self._inp_pays, 3, 0, 1, 2)
        addr_cl.addLayout(addr_grid)
        p2_page_layout.addWidget(addr_card)
        p2_page_layout.addStretch()

        # --- Page 3 : Événements (placeholder — l'élève n'existe pas encore) ---
        p3 = M3Frame()
        p3_layout = QVBoxLayout(p3)
        p3_layout.setSpacing(ds.sp(SpacingToken.SM))
        ph3 = M3Label(_("student_form.events_placeholder"), style="body_medium")
        ph3.setAlignment(Qt.AlignCenter)
        ph3.setWordWrap(True)
        p3_layout.addWidget(ph3)
        p3_layout.addStretch()

        # --- Page 4 : Dossiers (sections + fichiers) ---
        p4 = M3Frame()
        p4_layout = QVBoxLayout(p4)
        p4_layout.setContentsMargins(0, 0, 0, 0)
        from LarcSecretaire.views.dossier_panel import DossierPanel

        self._dossier_panel = DossierPanel(0)
        p4_layout.addWidget(self._dossier_panel, 1)
        self._timeline_page = self._dossier_panel.timeline

        # --- Page 7 : Notes / Résultats (répertoires drive) ---
        p7 = M3Frame()
        p7_layout = QVBoxLayout(p7)
        p7_layout.setSpacing(ds.sp(SpacingToken.SM))
        p7_layout.addWidget(M3Label(_("student_form.grades_title"), style="title_small"))

        from LarcSecretaire.common.app_config import app_config as _acfg

        drive_row = QHBoxLayout()
        drive_row.setSpacing(ds.space_sm)
        for dkey, dtitle_key in [("releves", "student_form.drive_releves"), ("bulletins", "student_form.drive_bulletins")]:
            dcard = M3Card(variant=CardVariant.ELEVATED)
            dcl = dcard.content_layout()
            dcl.setSpacing(ds.space_sm)
            dcl.addWidget(M3Label(_(dtitle_key), style="title_small"))
            ddir = _acfg.get(f"{dkey}_dir", "")
            durl = _acfg.get(f"{dkey}_cloud_url", "")
            dir_lbl = M3Label(str(ddir), style="label_small")
            dir_lbl.setWordWrap(True)
            dcl.addWidget(dir_lbl)
            btns = QHBoxLayout()
            btns.setSpacing(ds.space_xs)
            b_intra = M3Button(_("student_form.drive_intranet"), variant=ButtonVariant.TONAL)
            b_intra.clicked.connect(lambda _=False, p=ddir: self._open_drive_dir(p))
            btns.addWidget(b_intra)
            b_cloud = M3Button(_("student_form.drive_cloud"), variant=ButtonVariant.FILLED)
            b_cloud.clicked.connect(lambda _=False, u=durl: self._open_drive_cloud(u))
            btns.addWidget(b_cloud)
            btns.addStretch()
            dcl.addLayout(btns)
            drive_row.addWidget(dcard, 1)
        p7_layout.addLayout(drive_row)
        p7_layout.addStretch()

        # --- Page 8 : Photos ---
        p8 = M3Frame()
        p8_layout = QVBoxLayout(p8)
        p8_layout.setSpacing(ds.sp(SpacingToken.MD))
        p8_layout.setAlignment(Qt.AlignCenter)

        self._photo_large = QLabel()
        self._photo_large.setFixedSize(ds.sp(SpacingToken.XXXL) * 2, ds.sp(SpacingToken.XXXL) * 2)
        self._photo_large.setStyleSheet(f"background: {ds.p.primary_container}; border-radius: {ds.radius_sm}px;")
        self._photo_large.setAlignment(Qt.AlignCenter)
        p8_layout.addWidget(self._photo_large, 0, Qt.AlignCenter)

        photo_btn_row = QHBoxLayout()
        photo_btn_row.setAlignment(Qt.AlignCenter)
        self._upload_photo_btn = M3Button(_("student_form.change_photo"), variant=ButtonVariant.FILLED)
        self._upload_photo_btn.clicked.connect(self._on_change_photo)
        photo_btn_row.addWidget(self._upload_photo_btn)
        p8_layout.addLayout(photo_btn_row)
        p8_layout.addStretch()

        # --- Page 5 : Confidentiel (restreint) ---
        p5 = M3Frame()
        p5_layout = QVBoxLayout(p5)
        p5_layout.setSpacing(ds.sp(SpacingToken.SM))
        from LarcSecretaire.common.session import UserRole
        from LarcSecretaire.common.session import session as _ses

        if _ses.role in (UserRole.ADMIN, UserRole.COORD, UserRole.SECR):
            conf_label = M3Label(_("student_form.confidential_notes"), style="headline_large")
            p5_layout.addWidget(conf_label)
            conf_info = M3Label(_("student_form.confidential_desc"), style="body_medium")
            conf_info.setStyleSheet(f"padding-bottom: {ds.sp(SpacingToken.SM)}px;")
            conf_info.setWordWrap(True)
            p5_layout.addWidget(conf_info)
            from LarcSecretaire.views.dossier_panel import ConfidentialPanel

            self._conf_panel = ConfidentialPanel(0)
            p5_layout.addWidget(self._conf_panel, 1)
        else:
            deny = M3Label(_("student_form.confidential_restricted"), style="title_small")
            deny.setStyleSheet(f"padding: {ds.space_xl}px;")
            deny.setAlignment(Qt.AlignCenter)
            deny.setWordWrap(True)
            p5_layout.addWidget(deny)

        # Construire la sidebar + stack (même ordre que StudentEditDialog)
        self._nav_stack = M3StackedWidget()
        nav_pages = [
            (p1, "badge", _("student_form.tab_identity")),
            (p2_page, "home", _("student_form.tab_address")),
            (p3, "event", _("student_form.tab_events")),
            (p4, "folder", _("student_form.tab_documents")),
            (self._timeline_page, "timeline", _("dossier.timeline.title")),
            (p5, "lock", _("student_form.tab_confidential")),
            (p7, "school", _("student_form.tab_grades")),
            (p8, "photo_camera", _("student_form.tab_photos")),
        ]
        icon_sz = theme_manager.image.icon_btn
        self._dossier_nav_index = 0
        self._timeline_nav_index = 0
        for idx, (page, icon_name, label) in enumerate(nav_pages):
            if page is p4:
                self._dossier_nav_index = idx
            if page is self._timeline_page:
                self._timeline_nav_index = idx
            btn = M3Button(label, variant=ButtonVariant.TONAL)
            btn.setIcon(md3_icon(icon_name, color=theme_manager.palette.text_soft, size=icon_sz))
            btn.setIconSize(QSize(icon_sz, icon_sz))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.setChecked(idx == 0)
            btn.clicked.connect(lambda checked, i=idx: self._on_nav(i))
            nav_side.addWidget(btn)
            self._nav_btns.append(btn)
            self._nav_stack.addWidget(page)

        self._nav_stack.setCurrentIndex(0)
        nav_side.addStretch()
        nav_row.addLayout(nav_side)
        nav_row.addWidget(self._nav_stack, 1)
        layout.addLayout(nav_row, 1)

        # ── Chronologie : bouton du rail Dossiers → onglet du dialogue ──
        self._dossier_panel.timeline_requested.connect(self._open_timeline_tab)

        # Infos slot
        self._slot_info = M3Label(_("student_form.select_class"), style="body_medium")
        self._slot_info.setStyleSheet(f"padding: {ds.space_xs}px; font-style: italic;")
        layout.addWidget(self._slot_info)

        # Header élève : prénom/nom mis à jour en direct pendant la saisie
        def _update_name_header(_t=""):
            if hasattr(self, "_id_prenom"):
                self._id_prenom.setText(self._inp_prenom.text().strip())
                self._id_nom.setText(self._inp_nom.text().strip().upper())

        self._inp_nom.textChanged.connect(_update_name_header)
        self._inp_prenom.textChanged.connect(_update_name_header)

        ds.theme_changed.connect(self._restyle)

    @safe_slot("Unknown._restyle")
    def _restyle(self):
        if hasattr(self, "_photo") and self._photo:
            self._photo.setStyleSheet(f"background: {ds.p.primary_container}; border-radius: {ds.radius_sm}px;")
        if hasattr(self, "_photo_large") and self._photo_large:
            self._photo_large.setStyleSheet(f"background: {ds.p.primary_container}; border-radius: {ds.radius_sm}px;")
        # Header élève : couleurs réactives au thème
        for lbl in (self._id_prenom, self._id_nom):
            lbl.setStyleSheet(f"font-weight: bold; color: {ds.p.text_strong};")
        for lbl in (self._id_classe, self._id_id):
            lbl.setStyleSheet(f"color: {ds.p.text_strong};")
        if hasattr(self, "_parents_table") and self._parents_table:
            self._parents_table.setStyleSheet(ds.table_qss())
        for w in self._inp_fields():
            w.setStyleSheet(ds.flat_input_qss())
        for w in self._date_fields():
            w.setStyleSheet(
                f"border: 1px solid {ds.p.outline}; border-radius: {ds.radius_xs}px; "
                f"padding: {ds.space_md}px; color: {ds.p.text_strong}; background: {ds.p.surface}; "
                f"QDateEdit QLineEdit {{ color: {ds.p.text_strong}; background: {ds.p.surface}; }}"
            )
            w.setFixedWidth(ds.sp(SpacingToken.XXL) + ds.sp(SpacingToken.MD))
        if hasattr(self, "_inp_genre") and self._inp_genre:
            self._inp_genre.setStyleSheet(
                f"border: 1px solid {ds.p.outline}; border-radius: {ds.radius_xs}px; "
                f"padding: {ds.space_md}px; min-width: {ds.window_width * 3 // 20}px; "
                f"color: {ds.p.text_strong};"
            )
            self._inp_genre.setFixedWidth(ds.sp(SpacingToken.XXL) + ds.sp(SpacingToken.MD))
        if hasattr(self, "_addr_status") and self._addr_status:
            self._addr_status.setStyleSheet(f"color: {ds.p.text_disabled};")

    def _on_nav(self, index: int):
        self._nav_stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_btns):
            btn.setChecked(i == index)
        if index == getattr(self, "_timeline_nav_index", None):
            self._dossier_panel.refresh_timeline()

    @safe_slot("Unknown._open_timeline_tab")
    def _open_timeline_tab(self):
        self._on_nav(self._timeline_nav_index)

    @safe_slot("StudentCreateDialog.on_change_photo")
    def _on_change_photo(self):
        if not self._sid:
            QMessageBox.information(self, _("student_form.save_first"), _("student_form.save_first_msg"))
            return
        path, _f = QFileDialog.getOpenFileName(
            self,
            _("student_form.select_photo"),
            "",
            _("student_form.photo_filter"),
        )
        if not path:
            return
        from LarcSecretaire.common.photos import save_photo

        try:
            save_photo(self._sid, path)
            px = QPixmap(get_photo_path(self._sid))
            if not px.isNull():
                px_small = px.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._photo.setPixmap(px_small)
                px_large = px.scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._photo_large.setPixmap(px_large)
        except Exception as e:
            log(f"StudentCreateDialog._on_change_photo: {e}")
            QMessageBox.critical(self, _("common.dialog.error_title"), str(e))

    @safe_slot("StudentCreateDialog.open_drive_dir")
    def _open_drive_dir(self, path: str):
        import subprocess

        path = path or ""
        if not path:
            QMessageBox.information(self, _("common.dialog.info_title"), _("student_form.drive_dir_missing"))
            return
        try:
            os.makedirs(path, exist_ok=True)
            subprocess.Popen(["explorer", path])
        except Exception as e:
            log(f"StudentCreateDialog._open_drive_dir: {e}")
            QMessageBox.critical(self, _("common.dialog.error_title"), str(e))

    @safe_slot("StudentCreateDialog.open_drive_cloud")
    def _open_drive_cloud(self, url: str):
        import webbrowser

        if not url:
            QMessageBox.information(self, _("common.dialog.info_title"), _("student_form.drive_url_missing"))
            return
        webbrowser.open(url)

    def _inp_fields(self):
        fields = []
        for attr in [
            "_inp_nom",
            "_inp_prenom",
            "_inp_email",
            "_inp_emailperso",
            "_inp_tel",
            "_inp_tel2",
            "_inp_addr2",
            "_inp_cp",
            "_inp_ville",
            "_inp_pays",
        ]:
            if hasattr(self, attr):
                fields.append(getattr(self, attr))
        return fields

    def _date_fields(self):
        fields = []
        for attr in ["_inp_date_joined", "_inp_date", "_inp_birthdate"]:
            if hasattr(self, attr):
                fields.append(getattr(self, attr))
        return fields

    def _load_classes(self):
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            if self._preselected_class:
                # Mode classe connue : pas de grille, juste le label
                cur.execute(
                    """
                    SELECT c.label
                    FROM larcauth_classroom c
                    WHERE c.id = %s
                """,
                    (self._preselected_class,),
                )
                row = cur.fetchone()
                if row:
                    self._class_info.setText(_("student_form.class_slot").format(label=row[0]))
                self._on_class_changed(self._preselected_class)
            else:
                # Mode libre : grille de boutons
                cur.execute("""
                    SELECT c.id, c.label, l.fk_program_id, pr.sigle
                    FROM larcauth_classroom c
                    JOIN larcauth_level l ON l.id = c.fk_level_id
                    JOIN larcauth_program pr ON pr.id = l.fk_program_id
                    WHERE pr.sigle IN ('PEI', 'MYP', 'DPEn', 'DPFr')
                      AND c.enabled = TRUE
                    ORDER BY pr.sigle, l.label, c.label
                """)
                self._classes = list(cur.fetchall())
                self._build_class_buttons()
        except Exception as e:
            log(f"StudentCreateDialog._load_classes: {e}")

    def _build_class_buttons(self):
        if not hasattr(self, "_class_grid_layout") or not self._class_grid:
            return

        prog_style = {
            "PEI": (ds.p.primary, ds.p.primary_container, ds.p.on_primary),
            "MYP": (ds.p.secondary, ds.p.secondary_container, ds.p.on_secondary),
            "DPFr": (ds.p.error, ds.p.error_container, ds.p.on_error),
            "DPEn": (ds.p.tertiary, ds.p.tertiary_container, ds.p.on_tertiary),
        }

        groups = {k: [] for k in ["PEI", "MYP", "DPEn", "DPFr"]}
        for cid, label, pid, sigle in self._classes:
            if sigle in groups:
                groups[sigle].append((cid, label))

        sections = [
            (_("sec_main.college"), [("PEI", "PEI"), ("MYP", "MYP")]),
            (_("sec_main.lycee"), [("DP", "DPFr"), ("DPEn", "DPEn")]),
        ]

        self._clear_class_grid()
        self._class_btns.clear()

        for sec_name, columns in sections:
            sec_hdr = M3Label(sec_name, style="label_small")
            sec_hdr.setStyleSheet(
                f"font-weight: bold; color: {ds.p.text_strong}; border-bottom: 2px solid {ds.p.outline_variant}; padding: {ds.space_xxs // 2}px 0;"
            )
            self._class_grid_layout.addWidget(sec_hdr)

            grd = QGridLayout()
            grd.setSpacing(ds.space_xxs)

            for col_idx, (hdr_text, prog_key) in enumerate(columns):
                if prog_key not in groups:
                    continue
                fg, bg, on_fg = prog_style[prog_key]
                items = groups[prog_key]

                col_hdr = M3Label(hdr_text, style="label_small")
                col_hdr.setStyleSheet(f"background: {fg}; color: {on_fg}; border-radius: {ds.radius_sm}px; font-weight: bold; padding: {ds.space_xxs}px;")
                col_hdr.setAlignment(Qt.AlignCenter)
                col_hdr.setFixedHeight(ds.table_row_min)
                grd.addWidget(col_hdr, 0, col_idx)

                for i, (cid, label) in enumerate(items):
                    btn = M3Button(label, variant=ButtonVariant.TONAL)
                    btn.setFixedHeight(theme_manager.image.theme_btn)
                    btn.setStyleSheet(
                        f"M3Button {{ background: {bg}; color: {fg}; border: 2px solid transparent; "
                        f"border-radius: {ds.radius_sm}px; font-size: {ds.font_px_sm}px; padding: {ds.space_xxs // 2}px; }}"
                        f"M3Button:hover {{ background: {fg}; color: {bg}; }}"
                    )
                    btn.clicked.connect(lambda checked, c=cid: self._on_class_changed(c))
                    self._class_btns[cid] = btn
                    grd.addWidget(btn, i + 1, col_idx)

            self._class_grid_layout.addLayout(grd)
            self._class_grid_layout.addSpacing(ds.space_xxs)

        self._class_grid_layout.addStretch()

    def _clear_class_grid(self):
        if not self._class_grid:
            return
        while self._class_grid_layout.count():
            item = self._class_grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _on_class_changed(self, class_id: int):
        if not class_id:
            return
        self._class_id = class_id

        # Header élève : Classe mise à jour dès la sélection
        _label = ""
        for _c in self._classes:
            if _c[0] == class_id:
                _label = _c[1]
                break
        self._id_classe.setText(_("student_form.class_label").format(label=_label or "—"))

        # Mettre à jour la sélection visuelle (si grille de boutons)
        if self._class_btns:
            for cid, btn in self._class_btns.items():
                _, _, _, sigle = next((c for c in self._classes if c[0] == cid), (None, None, None, None))
                prog_map = {
                    "PEI": (ds.p.primary, ds.p.primary_container, ds.p.on_primary),
                    "MYP": (ds.p.secondary, ds.p.secondary_container, ds.p.on_secondary),
                    "DPFr": (ds.p.error, ds.p.error_container, ds.p.on_error),
                    "DPEn": (ds.p.tertiary, ds.p.tertiary_container, ds.p.on_tertiary),
                }
                fg, bg, on_fg = prog_map.get(sigle, (ds.p.text_strong, ds.p.surface_variant, ds.p.text_strong))
                if cid == class_id:
                    btn.setStyleSheet(
                        f"M3Button {{ background: {fg}; color: {bg}; border: 2px solid {fg}; "
                        f"border-radius: {ds.radius_sm}px; font-size: {ds.font_px_sm}px; padding: {ds.space_xxs // 2}px; }}"
                        f"M3Button:hover {{ background: {fg}; color: {bg}; }}"
                    )
                else:
                    btn.setStyleSheet(
                        f"M3Button {{ background: {bg}; color: {fg}; border: 2px solid transparent; "
                        f"border-radius: {ds.radius_sm}px; font-size: {ds.font_px_sm}px; padding: {ds.space_xxs // 2}px; }}"
                        f"M3Button:hover {{ background: {fg}; color: {bg}; }}"
                    )

        # Filtrer les genres selon la langue de la classe
        lang_id = self._get_class_language(class_id)
        self._load_genders(lang_id)

        conn = db.server_conn
        if not conn:
            return

        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT s.aecuser_ptr_id, aec.last_name, s.enabled
                FROM larcauth_student s
                JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id
                WHERE s.s_classroom_id = %s
                ORDER BY s.aecuser_ptr_id
            """,
                (self._class_id,),
            )
            all_rows = list(cur.fetchall())

            # Prochain slot libre (01→40) : enabled=FALSE et nom placeholder
            free = None
            for rid, ln, en in all_rows:
                slot = rid % 100
                if 1 <= slot <= 40 and not en and ("Name of" in (ln or "")):
                    free = slot
                    break

            self._next_free = free
            if free:
                self._sid = self._class_id * 100 + free
                self._id_id.setText(_("student_form.id_label").format(id=self._sid))
                base_dir = self._student_dir()
                dossiers_dir = os.path.join(base_dir, "dossiers")
                os.makedirs(dossiers_dir, exist_ok=True)
                conf_dir = os.path.join(base_dir, "confidentiel")
                os.makedirs(conf_dir, exist_ok=True)
                self._dossier_panel.set_directory(dossiers_dir)
                if hasattr(self, "_conf_panel"):
                    self._conf_panel.set_directory(conf_dir)
            else:
                self._sid = None

            if free:
                self._slot_info.setText(_("student_form.free_slot").format(n=free, id=self._class_id * 100 + free))
                self._slot_info.setStyleSheet(f"font-size: {ds.font_px_md}px; color: {ds.p.success}; padding: {ds.space_xs}px; font-weight: bold;")
                self._create_btn.setEnabled(True)
            else:
                self._slot_info.setText(_("student_form.no_slot"))
                self._slot_info.setStyleSheet(f"font-size: {ds.font_px_md}px; color: {ds.p.error}; padding: {ds.space_xs}px;")
                self._create_btn.setEnabled(False)
        except Exception as e:
            log(f"StudentCreateDialog._on_class_changed: {e}")

    def _get_class_language(self, classroom_id: int) -> int | None:
        conn = db.server_conn
        if not conn:
            return None
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT l.fk_language_id
                FROM larcauth_classroom c
                JOIN larcauth_level l ON l.id = c.fk_level_id
                WHERE c.id = %s
            """,
                (classroom_id,),
            )
            row = cur.fetchone()
            return row[0] if row else None
        except Exception as e:
            log(f"StudentCreateDialog._get_class_language: {e}")
            return None

    def _load_genders(self, lang_id: int | None = None):
        self._inp_genre.clear()
        self._inp_genre.addItem(_("student_form.gender_not_specified"), 0)
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            if lang_id:
                cur.execute("SELECT id, label FROM larcauth_gender WHERE fk_language_id = %s ORDER BY id", (lang_id,))
            else:
                cur.execute("SELECT id, label FROM larcauth_gender ORDER BY id")
            for gid, label in cur.fetchall():
                self._inp_genre.addItem(label, gid)
        except Exception as e:
            log(f"StudentCreateDialog._load_genders: {e}")

    @safe_slot("Unknown._on_create")
    def _on_create(self):
        nom = self._inp_nom.text().strip()
        prenom = self._inp_prenom.text().strip()
        if not nom or not prenom:
            QMessageBox.warning(self, _("common.dialog.confirm_title"), _("student_form.validation_required"))
            return
        self._create_student()

    # ── Notes (formatage HTML) — supprimé, remplacé par NotesPanel JSON

    def _student_dir(self) -> str:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "students")
        d = os.path.join(base, str(self._sid))
        os.makedirs(d, exist_ok=True)
        return d

    def _create_student(self):
        slot = self._next_free
        if slot is None:
            return
        student_id = self._class_id * 100 + slot

        nom = self._inp_nom.text().strip()
        prenom = self._inp_prenom.text().strip()
        email = self._inp_email.text().strip()
        emailperso = self._inp_emailperso.text().strip() or None
        tel = self._inp_tel.text().strip() or None
        tel2 = self._inp_tel2.text().strip() or None
        date_str = self._inp_date.date().toString("yyyy-MM-dd") if self._inp_date.date().isValid() and not self._inp_date.date().isNull() else None

        conn = db.server_conn
        if not conn:
            return

        try:
            cur = conn.cursor()
            from datetime import datetime

            now = datetime.now().isoformat()
            birth_str = (
                self._inp_birthdate.date().toString("yyyy-MM-dd") if self._inp_birthdate.date().isValid() and not self._inp_birthdate.date().isNull() else None
            )
            username = email or f"student.{nom.lower()}.{prenom.lower()}"

            joined_str = (
                self._inp_date_joined.date().toString("yyyy-MM-dd")
                if self._inp_date_joined.date().isValid() and not self._inp_date_joined.date().isNull()
                else None
            )
            cur.execute(
                """
                UPDATE larcauth_aecuser SET
                    first_name = %s, last_name = %s, email = %s,
                    username = %s, is_active = TRUE, updated = %s,
                    emailperso = %s, tel_smartphone_1 = %s, tel_maison = %s,
                    date_joined = %s, date_entree = %s, date_of_birth = %s, fk_gender_id = %s
                WHERE id = %s
            """,
                (
                    prenom,
                    nom,
                    email or "",
                    username,
                    now,
                    emailperso,
                    tel,
                    tel2,
                    joined_str,
                    date_str,
                    birth_str,
                    self._inp_genre.currentData() or None,
                    student_id,
                ),
            )

            notes_data = self._dossier_panel.get_data()
            notes_data["health"] = self._dossier_panel.get_health()
            if hasattr(self, "_conf_panel"):
                notes_data["confidentiel"] = {"intro": "", "entries": self._conf_panel.get_entries()}
            notes_json = json.dumps(notes_data)
            cur.execute(
                """
                UPDATE larcauth_student SET enabled = TRUE, updated_s = %s, notes_json = %s
                WHERE aecuser_ptr_id = %s
            """,
                (now, notes_json, student_id),
            )

            cur.execute(
                """
                INSERT INTO foyer (id, enabled, address_line1, address_line2,
                                   postal_code, city, country)
                VALUES (%s, TRUE, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    address_line1 = EXCLUDED.address_line1,
                    address_line2 = EXCLUDED.address_line2,
                    postal_code = EXCLUDED.postal_code,
                    city = EXCLUDED.city,
                    country = EXCLUDED.country
            """,
                (
                    student_id,
                    self._inp_addr1.toPlainText().strip() or None,
                    self._inp_addr2.text().strip() or None,
                    self._inp_cp.text().strip() or None,
                    self._inp_ville.text().strip() or None,
                    self._inp_pays.text().strip() or None,
                ),
            )
            cur.execute("UPDATE larcauth_aecuser SET fk_foyer_id = %s WHERE id = %s", (student_id, student_id))

            cur.execute("SET LOCAL app.sync_source = 'intranet'")
            cur.execute(f"SET LOCAL app.modified_by = {session.user_id}")
            audit.create_student(student_id, f"Création {prenom} {nom}")

            conn.commit()
            self._result_data = {"id": student_id, "last_name": nom, "first_name": prenom}
            self._sid = student_id
            log(f"StudentCreateDialog: activated #{student_id} (slot {slot:02d})")

            # Charger les parents maintenant que l'élève existe
            self._load_parents()

            QMessageBox.information(self, _("student_form.created"), _("student_form.created_msg").format(f=prenom, l=nom, sid=student_id, slot=slot))

            # Réinitialiser le formulaire pour une autre saisie
            for w in [
                self._inp_nom,
                self._inp_prenom,
                self._inp_email,
                self._inp_emailperso,
                self._inp_tel,
                self._inp_tel2,
                self._inp_date,
                self._inp_addr1,
                self._inp_addr2,
                self._inp_cp,
                self._inp_ville,
            ]:
                w.clear()
            self._dossier_panel.clear()
            if hasattr(self, "_conf_panel"):
                self._conf_panel.clear()
            self._inp_pays.setText("Togo")
            self._sid = None
            self._parent_ids = []
            self._parents_table.setRowCount(0)
            # Re-vérifier le slot libre
            self._on_class_changed(self._class_id)

        except Exception as e:
            conn.rollback()
            log(f"StudentCreateDialog._create_student: {e}")
            QMessageBox.critical(self, _("common.dialog.error_title"), str(e))

    def _load_parents(self):
        self._parent_ids = []
        conn = db.server_conn
        if not conn or not self._sid:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT aec.id, aec.last_name || ' ' || aec.first_name, sp.nature, aec.email, aec.tel_smartphone_1
                FROM student_parent sp
                JOIN larcauth_aecuser aec ON aec.id = sp.parent_id
                WHERE sp.student_id = %s
                ORDER BY aec.last_name, aec.first_name
            """,
                (self._sid,),
            )
            rows = cur.fetchall()
            self._parent_ids = []
            self._parents_table.setRowCount(len(rows))
            for i, (pid, name, nat, em, tel) in enumerate(rows):
                self._parent_ids.append(pid)
                self._parents_table.setItem(i, 0, QTableWidgetItem(name))
                if nat:
                    self._parents_table.setItem(i, 1, QTableWidgetItem(nat))
                self._parents_table.setItem(i, 2, QTableWidgetItem(em or ""))
                self._parents_table.setItem(i, 3, QTableWidgetItem(tel or ""))
            self._parents_table.resizeColumnsToContents()
            if rows:
                self._parents_table.selectRow(0)
        except Exception as e:
            log(f"StudentCreateDialog._load_parents: {e}")

    @safe_slot("StudentEditDialog.copy_parent_address")
    def _copy_parent_address(self):
        if not self._sid:
            QMessageBox.information(self, _("student_form.save_first"), _("student_form.save_first_msg"))
            return
        sel = self._parents_table.selectedItems()
        if not sel or not self._parent_ids:
            QMessageBox.warning(self, _("student_form.copy_address_title"), _("student_form.copy_address_none"))
            return
        row = sel[0].row()
        if row >= len(self._parent_ids):
            return
        pid = self._parent_ids[row]
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT address_line1, address_line2, postal_code, city, country
                FROM foyer WHERE id = %s
            """,
                (pid,),
            )
            row = cur.fetchone()
            if row and any(row):
                addr1, addr2, cp, ville, pays = row
                self._inp_addr1.setPlainText(addr1 or "")
                self._inp_addr2.setText(addr2 or "")
                self._inp_cp.setText(cp or "")
                self._inp_ville.setText(ville or "")
                if pays:
                    self._inp_pays.setText(pays)
                if hasattr(self, "_addr_status") and self._addr_status:
                    self._addr_status.hide()
            else:
                if hasattr(self, "_addr_status") and self._addr_status:
                    self._addr_status.setText(_("student_form.copy_address_no_address"))
                    self._addr_status.show()
        except Exception as e:
            log(f"StudentCreateDialog._copy_parent_address: {e}")

    @safe_slot("StudentEditDialog.add_parent_link")
    def _add_parent_link(self):
        if not self._sid:
            QMessageBox.information(self, _("student_form.save_first"), _("student_form.save_first_msg"))
            return
        dlg = M3Dialog(self)
        dlg.setWindowTitle(_("student_form.add_parent"))
        dlg.setMinimumSize(ds.golden_height(610), ds.golden_height(610))
        dlg.setStyleSheet(f"background: {ds.p.surface}; color: {ds.p.text_strong};")
        layout = QVBoxLayout(dlg)
        search_inp = M3TextField()
        search_inp.setPlaceholderText(_("student_form.search_parent_placeholder"))
        search_inp.setStyleSheet(ds.flat_input_qss())
        layout.addWidget(search_inp)
        result_list = M3ListWidget()
        result_list.setStyleSheet(ds.table_qss())
        layout.addWidget(result_list, 1)
        buttons = M3DialogButtonBox(M3DialogButtonBox.Ok | M3DialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        def on_search(text):
            if len(text.strip()) < 3:
                result_list.clear()
                return
            conn = db.server_conn
            if not conn:
                return
            try:
                cur = conn.cursor()
                q = "%" + text.strip() + "%"
                cur.execute(
                    """
                    SELECT id, last_name, first_name, email
                    FROM larcauth_aecuser
                    WHERE type_parentutor = TRUE
                      AND (LOWER(last_name) LIKE LOWER(%s) OR LOWER(first_name) LIKE LOWER(%s) OR LOWER(email) LIKE LOWER(%s))
                      AND id NOT IN (SELECT parent_id FROM student_parent WHERE student_id = %s)
                    ORDER BY last_name, first_name LIMIT 50
                """,
                    (q, q, q, self._sid),
                )
                result_list.clear()
                self._search_parents_data = []
                for pid, ln, fn, em in cur.fetchall():
                    result_list.addItem(f"{ln or ''} {fn or ''} ({em or 'pas d e-mail'})")
                    self._search_parents_data.append(pid)
            except Exception as e:
                log(f"_add_parent_link search: {e}")

        search_inp.textChanged.connect(on_search)
        self._search_parents_data = []

        if dlg.exec() == M3Dialog.Accepted:
            cur_sel = result_list.currentRow()
            if cur_sel < 0 or cur_sel >= len(self._search_parents_data):
                return
            pid = self._search_parents_data[cur_sel]
            conn = db.server_conn
            if not conn:
                return
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO student_parent (student_id, parent_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (self._sid, pid),
                )
            except Exception as e:
                log(f"_add_parent_link insert: {e}")
                QMessageBox.critical(self, _("common.dialog.error_title"), str(e))
            self._load_parents()

    @safe_slot("StudentEditDialog.edit_parent_nature")
    def _edit_parent_nature(self):
        if not self._sid:
            QMessageBox.information(self, _("student_form.save_first"), _("student_form.save_first_msg"))
            return
        sel = self._parents_table.selectedItems()
        if not sel or not self._parent_ids:
            QMessageBox.warning(self, _("student_form.nature_dialog_title"), _("parent.error.no_parent_selected"))
            return
        row = sel[0].row()
        if row >= len(self._parent_ids):
            return
        pid = self._parent_ids[row]
        from PySide6.QtWidgets import QInputDialog

        nature, ok = QInputDialog.getText(self, _("student_form.nature_prompt_title"), _("student_form.nature_prompt_msg"))
        if not ok:
            return
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE student_parent SET nature = %s WHERE student_id = %s AND parent_id = %s",
                (nature.strip(), self._sid, pid),
            )
            self._load_parents()
        except Exception as e:
            log(f"_edit_parent_nature: {e}")

    @safe_slot("StudentEditDialog.remove_parent_link")
    def _remove_parent_link(self):
        if not self._sid:
            QMessageBox.information(self, _("student_form.save_first"), _("student_form.save_first_msg"))
            return
        sel = self._parents_table.selectedItems()
        if not sel or not self._parent_ids:
            QMessageBox.warning(self, _("student_form.remove_parent"), _("student_form.edit_nature"))
            return
        row = sel[0].row()
        if row >= len(self._parent_ids):
            return
        pid = self._parent_ids[row]
        confirm = QMessageBox.question(self, _("student_form.remove_confirm_title"), _("student_form.remove_confirm_msg"), QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM student_parent WHERE student_id = %s AND parent_id = %s", (self._sid, pid))
            self._load_parents()
        except Exception as e:
            log(f"_remove_parent_link: {e}")

    def get_data(self) -> dict | None:
        return self._result_data
