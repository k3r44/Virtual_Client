from PyQt6.QtWidgets import QMessageBox


class DialogHelper:

    @staticmethod
    def info(parent, titulo, mensaje):

        QMessageBox.information(
            parent,
            titulo,
            mensaje
        )

    @staticmethod
    def warning(parent, titulo, mensaje):

        QMessageBox.warning(
            parent,
            titulo,
            mensaje
        )

    @staticmethod
    def error(parent, titulo, mensaje):

        QMessageBox.critical(
            parent,
            titulo,
            mensaje
        )

    @staticmethod
    def confirm(parent, titulo, mensaje):

        return QMessageBox.question(
            parent,
            titulo,
            mensaje,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
