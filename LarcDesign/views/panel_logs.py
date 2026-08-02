"""Panel Logs — audit_trail."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QTableWidgetItem
from phibuilder.widgets import M3Label, M3TableWidget, M3ScrollArea
from phibuilder.phi.scale import SpacingToken
from larccommon.theme import theme_manager
from LarcDesign.common.db_access import get_logs


class LogsPanel(M3ScrollArea):
    def __init__(self, user: dict):
        super().__init__(theme=theme_manager.phi_theme)
        phi = theme_manager.phi_theme
        sp = phi.spacing.spacing

        container = QWidget()
        l = QVBoxLayout(container)
        l.setContentsMargins(sp(SpacingToken.LG), sp(SpacingToken.LG),
                             sp(SpacingToken.LG), sp(SpacingToken.LG))
        l.setSpacing(sp(SpacingToken.MD))
        l.addWidget(M3Label("Logs", theme=phi, style="headline_small"))

        table = M3TableWidget(theme=phi)
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Date", "Utilisateur", "Action", "Type", "Cible", "Detail"])
        h = table.horizontalHeader()
        for i in range(6):
            h.setSectionResizeMode(i, QHeaderView.Stretch)
        table.setAlternatingRowColors(False)

        rows = get_logs(200)
        table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(r['at'].strftime('%d/%m %H:%M') if r.get('at') else ''))
            table.setItem(i, 1, QTableWidgetItem(r.get('user', '') or ''))
            table.setItem(i, 2, QTableWidgetItem(r.get('action', '') or ''))
            table.setItem(i, 3, QTableWidgetItem(r.get('target_type', '') or ''))
            table.setItem(i, 4, QTableWidgetItem(str(r.get('target_id', '')) or ''))
            table.setItem(i, 5, QTableWidgetItem(r.get('detail', '') or ''))

        l.addWidget(table)
        self.setWidget(container)
        self.setWidgetResizable(True)
