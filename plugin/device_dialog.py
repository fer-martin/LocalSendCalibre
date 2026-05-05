import threading

from qt.core import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                     QListWidgetItem, QDialogButtonBox, QLabel,
                     QPushButton, QLineEdit, Qt, pyqtSignal)

from calibre_plugins.localsend_plugin.discovery import discover_devices


class DeviceDialog(QDialog):
    scan_done = pyqtSignal(object, object)  # (devices_dict, error_str|None)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Selecciona dispositivo LocalSend')
        self.resize(480, 340)
        self.selected_ip = None

        layout = QVBoxLayout(self)

        self.status = QLabel()
        layout.addWidget(self.status)

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(lambda _i: self.on_accept())
        layout.addWidget(self.list)

        manual_row = QHBoxLayout()
        manual_row.addWidget(QLabel('IP manual:'))
        self.manual_ip = QLineEdit()
        self.manual_ip.setPlaceholderText('p.ej. 192.168.1.50')
        manual_row.addWidget(self.manual_ip)
        layout.addLayout(manual_row)

        btn_row = QHBoxLayout()
        self.refresh_btn = QPushButton('Re-escanear')
        self.refresh_btn.clicked.connect(self.start_scan)
        btn_row.addWidget(self.refresh_btn)
        btn_row.addStretch()

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.on_accept)
        btns.rejected.connect(self.reject)
        btn_row.addWidget(btns)
        layout.addLayout(btn_row)

        self.scan_done.connect(self._on_scan_done)
        self.start_scan()

    def start_scan(self):
        self.list.clear()
        self.status.setText('Buscando dispositivos…')
        self.refresh_btn.setEnabled(False)
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        try:
            devices = discover_devices(timeout=4)
            self.scan_done.emit(devices, None)
        except Exception as e:
            self.scan_done.emit({}, str(e))

    def _on_scan_done(self, devices, err):
        self.refresh_btn.setEnabled(True)
        if err:
            self.status.setText(f'Error: {err}')
            return
        if not devices:
            self.status.setText(
                'No se encontraron dispositivos. Verifica que LocalSend '
                'esté abierto en el Kobo o introduce la IP manualmente.'
            )
            return
        self.status.setText(f'{len(devices)} dispositivo(s) encontrado(s):')
        for ip, info in devices.items():
            alias = info.get('alias', '?')
            model = info.get('deviceModel', '')
            dtype = info.get('deviceType', '')
            label = f'{alias}  —  {model} ({dtype})  —  {ip}'
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, ip)
            self.list.addItem(item)
        self.list.setCurrentRow(0)

    def on_accept(self):
        manual = self.manual_ip.text().strip()
        if manual:
            self.selected_ip = manual
            self.accept()
            return
        item = self.list.currentItem()
        if item is not None:
            self.selected_ip = item.data(Qt.ItemDataRole.UserRole)
            self.accept()