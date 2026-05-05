from calibre.customize import InterfaceActionBase

class LocalSendPlugin(InterfaceActionBase):
    name = 'Send via LocalSend'
    description = 'Envía libros al Kobo mediante el protocolo LocalSend'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Fernando Martin'
    version = (1, 0, 0)
    minimum_calibre_version = (5, 0, 0)
    actual_plugin = 'calibre_plugins.localsend_plugin.ui:LocalSendAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        from calibre_plugins.localsend_plugin.config import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()