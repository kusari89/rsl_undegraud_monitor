from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSlider,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QGroupBox,
    QButtonGroup,
    QTextEdit,
    QTabWidget,
    QTextBrowser,
)
import serial.tools.list_ports
from PyQt6.QtGui import QColor
import hardware as hw
import app_logger
from datetime import datetime
import os
from graph_widget import GraphWidget
logger = app_logger.get_logger(__name__)


class Color:
    red = QColor(255, 0, 0)
    green = QColor(0, 255, 0)
    yellow = QColor(255, 255, 0)
    white = QColor(255, 255, 255)

class MyComboBox(QComboBox):
    def __init__(self):
        super().__init__()

    def showPopup(self):
        self.clear()
        com_list = [element.device for element in serial.tools.list_ports.comports()]
        com_list.sort()
        self.addItems(com_list)
        super().showPopup()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info('Главное окно создано')
        self.setWindowTitle('Com port FT2 monitoring')

        self.statusBar()
        self.status_show('Программа запущена')

        self.com_parameters = ComParameters()
        self.log = Log()
        self.log.setFixedSize(400, 400)

        self.graph = GraphWidget()
        self.sensor_mode = SensorMode()

        layout_left_top = QHBoxLayout()
        layout_left_top.addWidget(self.com_parameters)
        layout_left_top.addWidget(self.sensor_mode)

        layout_left = QVBoxLayout()
        layout_left.addLayout(layout_left_top)
        layout_left.addWidget(self.log)

        layout_main = QHBoxLayout()
        layout_main.addLayout(layout_left)
        layout_main.addWidget(self.graph)

        container = QWidget()
        container.setLayout(layout_main)
        # Устанавливаем центральный виджет Window.
        self.setCentralWidget(container)

    def status_show(self, text):
        self.statusBar().showMessage(text)

    def enable_all_element(self, checked):
        self.com_parameters.enable_all_element(checked)
        self.log.enable_all_element(checked)

    def closeEvent(self, e):
        self.log.save_log_()
        e.accept()


class ComParameters(QWidget):
    def __init__(self):
        super().__init__()
        self.com_list = MyComboBox()
        com_list = hw.com_list()
        com_list.sort()
        self.com_list.addItems(com_list)

        self.com_status = QPushButton('Открыть')
        self.com_status.setCheckable(True)

        port_label = QLabel('Порт')
        groupbox = QGroupBox(port_label.text())

        group_layout = QVBoxLayout(groupbox)
        group_layout.addWidget(self.com_list)
        group_layout.addWidget(self.com_status)
        groupbox.setFixedSize(150, 110)

        lay = QVBoxLayout()
        lay.addWidget(groupbox)
        self.setLayout(lay)

    def enable_all_element(self, checked):
        if checked:
            self.com_status.setChecked(True)
            self.com_status.setText('Закрыть')
            self.com_list.setDisabled(True)
        else:
            self.com_status.setChecked(False)
            self.com_status.setText('Открыть')
            self.com_list.setEnabled(True)


class Log(QWidget):
    def __init__(self):
        super().__init__()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet('QTextEdit { color: white; background-color: black; font: Times New Roman 12px}')
        self.cursor = self.log.textCursor()

        self.clear_log = QPushButton('Очистить')
        self.clear_log.setCheckable(False)
        self.clear_log.setDisabled(True)
        self.save_log = QPushButton('Сохранить')
        self.save_log.setCheckable(False)
        self.save_log.setDisabled(True)
        self.auto_scroll = QCheckBox()
        self.auto_scroll.setChecked(True)
        self.auto_scroll.setDisabled(True)
        auto_scroll_label = QLabel('Автопрокрутка')

        log_label = QLabel('Лог')
        groupbox = QGroupBox(log_label.text())

        layout_scroll = QHBoxLayout()
        layout_scroll.addWidget(self.auto_scroll)
        layout_scroll.addWidget(auto_scroll_label)

        layout_button = QHBoxLayout()
        layout_button.addWidget(self.save_log)
        layout_button.addWidget(self.clear_log)

        layout_bar = QHBoxLayout()
        layout_bar.addLayout(layout_button)
        layout_bar.addLayout(layout_scroll)

        group_layout = QVBoxLayout(groupbox)
        group_layout.addLayout(layout_bar)
        group_layout.addWidget(self.log)

        lay = QVBoxLayout()
        lay.addWidget(groupbox)
        self.setLayout(lay)

        # сигналы
        self.clear_log.clicked.connect(self.clear_log_)
        self.save_log.clicked.connect(self.save_log_)

    def enable_all_element(self, checked):
        if checked:
            self.clear_log.setEnabled(True)
            self.save_log.setEnabled(True)
            self.auto_scroll.setEnabled(True)
        else:
            self.clear_log.setDisabled(True)
            self.save_log.setDisabled(True)
            self.auto_scroll.setDisabled(True)

    def log_message(self, color, message):
        if self.auto_scroll.isChecked():
            self.log.setTextColor(color)
            self.log.append(message)
            self.log.setTextCursor(self.cursor)
        else:
            self.log.setTextColor(color)
            self.log.append(message)

    def clear_log_(self):
        self.log.clear()

    def save_log_(self):
        path = 'log'
        dt = datetime.now().strftime('%d_%m_%Y %H_%M_%S')
        if path not in os.listdir():
            try:
                os.makedirs(path)
            except OSError:
                logger.error(f'Создать директорию {path} не удалось')
            else:
                logger.info(f'Успешно создана директория {path} ')
        try:
            data = str(self.log.toPlainText())
            if len(data) != 0:
                with open(f'log/{dt}.txt', 'a+') as lg:
                    try:
                        lg.write(data)
                    except Exception as exs:
                        logger.error(exs)
        except OSError as exs:
            logger.error(exs)


class SensorMode(QWidget):
    def __init__(self):
        super().__init__()
        self.channel1_box = QCheckBox()
        self.channel1_box.setCheckable(True)
        self.channel1_label = QLabel('Канал 1')

        self.channel2_box = QCheckBox()
        self.channel2_box.setCheckable(True)
        self.channel2_label = QLabel('Канал 2')

        self.buv_box = QCheckBox()
        self.buv_box.setCheckable(True)
        self.buv_label = QLabel('БУВ')

        self.button_group = QButtonGroup()
        self.button_group.setExclusive(False)
        self.button_group.addButton(self.channel1_box)
        self.button_group.addButton(self.channel2_box)
        self.button_group.addButton(self.buv_box)

        channel1_layout = QHBoxLayout()
        channel1_layout.addWidget(self.channel1_box)
        channel1_layout.addWidget(self.channel1_label)
        channel1_layout.addStretch(0)

        channel2_layout = QHBoxLayout()
        channel2_layout.addWidget(self.channel2_box)
        channel2_layout.addWidget(self.channel2_label)
        channel2_layout.addStretch(0)

        buv_layout = QHBoxLayout()
        buv_layout.addWidget(self.buv_box)
        buv_layout.addWidget(self.buv_label)
        buv_layout.addStretch(0)

        sensor_mode_label = QLabel('Режим работы')
        groupbox = QGroupBox(sensor_mode_label.text())

        group_layout = QVBoxLayout(groupbox)
        group_layout.addLayout(channel1_layout)
        group_layout.addLayout(channel2_layout)
        group_layout.addLayout(buv_layout)
        groupbox.setFixedSize(150, 110)

        lay = QHBoxLayout()
        lay.addWidget(groupbox)
        self.setLayout(lay)

    def change_sensor_mode_status(self, data):
        channel1 = data[0] & 0x29
        channel2 = data[0] & 0x2A
        buv = data[0] & 0x2C
        if channel1 == 0x29:
            self.channel1_box.setChecked(True)
        else:
            self.channel1_box.setChecked(False)
        if channel2 == 0x2A:
            self.channel2_box.setChecked(True)
        else:
            self.channel2_box.setChecked(False)
        if buv == 0x2C:
            self.buv_box.setChecked(True)
        else:
            self.buv_box.setChecked(False)
