from qt.core import QWidget, QVBoxLayout, QCheckBox, QLabel
from calibre.utils.config import JSONConfig


prefs = JSONConfig('plugins/localsend')
prefs.defaults['kepubify'] = True

class ConfigWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.kepubify_cb = QCheckBox(
            'Convertir EPUB → KEPUB automáticamente al enviar')
        self.kepubify_cb.setChecked(prefs['kepubify'])
        layout.addWidget(self.kepubify_cb)

        info = QLabel(
            'Si tienes instalado el plugin "KoboTouchExtended" (que aporta\n'
            'salida KEPUB), se hará una kepubificación completa con span\n'
            'wrapping. Si no, se copiará el EPUB con extensión .kepub.epub\n'
            'para que el Kobo lo reconozca como libro Kobo.\n\n'
            'Si la biblioteca ya tiene formato KEPUB para el libro, se\n'
            'usa ese directamente.'
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        layout.addStretch()

    def save_settings(self):
        prefs['kepubify'] = self.kepubify_cb.isChecked()