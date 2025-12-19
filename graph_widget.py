from random import randint
from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import (
    QLineEdit,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QApplication,
    QPushButton,
    QCheckBox
)
from datetime import datetime
import os
import pyqtgraph as pg
import hardware as hw
import time
from enum import IntEnum
import app_logger
import queue
import threading

logger = app_logger.get_logger(__name__)


class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        logger.debug('Виджет графиков запущен')
        '''
        Переменная заполняется на старте программы
        Нужна для последющего вычисления времени прихода пакета 
        И постройки графика
        '''
        self.start_program_time = time.time()
        '''
        Очередь для входящих данных [data, time], где time текущее время системы, когда получени пакет в секундах
        Нужна, для того, что бы разделить потоки постройки графиков и получения данных, 
        при её отсутствии график обновляется в том же потоке, что и идёт получение данных с COM порта 
        '''
        self.input_data = queue.Queue()

        self.time = QLineEdit('30')
        self.time.setFixedSize(100, 25)
        self.time.setValidator(QtGui.QIntValidator())
        self.time.textChanged.connect(self.update_interval)
        label_time = QLabel('Время отображения')

        self.signal_graph = SubGraphWidget(title='Уровень сигнала', left_label='дБ', xrange=int(self.time.text()))
        self.amplitude_graph = SubGraphWidget(title='Амплитуда', left_label='Ед', xrange=int(self.time.text()))

        self.bottom_theme = QPushButton()
        self.bottom_theme.setCheckable(True)
        self.set_theme()

        self.check_box_out_graph = QCheckBox()
        self.check_box_out_graph.setChecked(True)
        label_check_box_out_graph = QLabel('Вывод графика')

        self.button_graph_data = QPushButton('Запрос данных')
        self.button_graph_data.setCheckable(True)


        # подключённые сигналы
        self.bottom_theme.clicked.connect(self.set_theme)
        self.check_box_out_graph.clicked.connect(self.out_graph)
        self.button_graph_data.clicked.connect(self.graph_data)

        layout_out_graph = QHBoxLayout()
        layout_out_graph.addWidget(self.check_box_out_graph)
        layout_out_graph.addWidget(label_check_box_out_graph)

        layout_settings = QHBoxLayout()
        layout_settings.addWidget(self.time)
        layout_settings.addWidget(label_time)
        layout_settings.addWidget(self.button_graph_data)
        layout_settings.addLayout(layout_out_graph)
        layout_settings.addWidget(self.bottom_theme)

        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_settings)
        layout_main.addWidget(self.signal_graph)
        layout_main.addWidget(self.amplitude_graph)
        self.setLayout(layout_main)

        self.timer = QtCore.QTimer()
        self.update = 20
        self.timer.setInterval(self.update)
        self.timer.timeout.connect(self.update_plot)
        self.out_graph(self.check_box_out_graph.isChecked())


    def update_plot(self):
        self.timer.stop()
        for _ in range(self.input_data.qsize()):
            if self.input_data.empty() is False:
                input_data = self.input_data.get()
                data = input_data[0]
                time_ = input_data[1]
                if isinstance(data[0], int) and isinstance(data[1], int) and isinstance(data[2], int) is True:
                    time_ = time_ - self.start_program_time
                    data = CmdLogData(data, time_)
                    if data.signal_level > 200:
                        print(data.signal_level, type(data.signal_level), input_data[2])
                    else:
                        pass
                        self.signal_graph.update_plot(data.signal_level, data.number_channel, time_,
                                                      int(self.time.text()))
                        self.amplitude_graph.update_plot(data.amplitude, data.number_channel, time_,
                                                      int(self.time.text()))
                else:
                    pass
            else:
                pass
        self.timer.start()

    def update_interval(self):
        logger.debug(f'Интервал отображения записи изменён на {self.time.text()}')
        interval = int(self.time.text())
        self.signal_graph.update_interval(interval)
        self.amplitude_graph.update_interval(interval)

    def out_graph(self, checked):
        if checked:
            self.timer.start()
        else:
            self.timer.stop()

    def graph_data(self, checked):
        if checked:
            dt_start = datetime.now().strftime('%d_%m_%Y %H_%M_%S')
            CmdLogData.file_name = f'OutFile_{dt_start}'
            self.amplitude_graph.reset_data()
            self.signal_graph.reset_data()
            self.start_program_time = time.time()
            CmdLogData.file_name = f'OutFile_{dt_start}'
            self.button_graph_data.setText('Остановка данных')
            hw.rb.send_cmd(hw.rb.Address.SENSOR, 0x1D, bytearray([0x27, 0x01]))
        else:
            self.button_graph_data.setText('Запрос данных')
            hw.rb.send_cmd(hw.rb.Address.SENSOR, 0x1D, bytearray([0x27, 0x00]))

    def set_theme(self):
        checked = self.bottom_theme.isChecked()
        if checked:
            self.bottom_theme.setText('Белая тема')
            self.signal_graph.set_theme(checked)
            self.amplitude_graph.set_theme(checked)
        else:
            self.bottom_theme.setText('Черная тема')
            self.signal_graph.set_theme(checked)
            self.amplitude_graph.set_theme(checked)

    def closeEvent(self, e):
        hw.rb.send_cmd(hw.rb.Address.SENSOR, 0x1D, bytearray([0x27, 0x00]))
        e.accept()


class SubGraphWidget(QWidget):
    def __init__(self, title, left_label, xrange):
        super().__init__()
        # graph data
        self.graph_time = []
        self.graph_time_2 = []
        self.graph_value = []
        self.graph_value_2 = []
        # theme settings
        self.color_background = None
        self.color_label = None
        self.title = title
        self.left_label = left_label
        # graph settings
        self.plot_graph = pg.PlotWidget()
        self.plot_graph.addLegend()
        self.plot_graph.showGrid(x=True, y=True)
        self.plot_graph.setXRange(-30, 0)
        pen_channel_1 = pg.mkPen(color=(0, 0, 255))
        self.plot_line_channel_1 = self.plot_graph.plot(self.graph_value, self.graph_time,
                                                        name='Канал 1', pen=pen_channel_1)
        pen_channel_2 = pg.mkPen(color=(255, 0, 0))
        self.plot_line_channel_2 = self.plot_graph.plot(self.graph_value_2, self.graph_time,
                                                        name='Канал 2', pen=pen_channel_2)
        self.plot_graph.setXRange(xrange, 0)
        lay = QVBoxLayout()
        lay.addWidget(self.plot_graph)
        self.setLayout(lay)

    def update_interval(self, interval):
        if len(self.graph_time) and len(self.graph_time_2) != 0:
            time_ = max(self.graph_time[-1], self.graph_time_2[-1])
        elif len(self.graph_time) != 0:
            time_ = self.graph_time[-1]
        elif len(self.graph_time_2) != 0:
            time_ = self.graph_time_2[-1]
        else:
            time_ = 0
        self.plot_graph.setXRange(-interval + time_, 0 + time_)

    def update_plot(self, data, number_channel, time_, interval):
        self.plot_graph.setXRange(-interval + time_, 0 + time_)
        if number_channel == Channel.channel_1:
            self.graph_value.append(data)
            self.graph_time.append(time_)
        elif number_channel == Channel.channel_2:
            self.graph_value_2.append(data)
            self.graph_time_2.append(time_)
        self.plot_line_channel_1.setData(self.graph_time, self.graph_value)
        self.plot_line_channel_2.setData(self.graph_time_2, self.graph_value_2)

    def set_theme(self, checked):
        if checked:
            self.color_background = 'White'
            self.color_label = 'Black'
            styles = {'color': self.color_label, 'font-size': '15px'}
            self.plot_graph.setBackground(background=self.color_background)
            self.plot_graph.setTitle(self.title, **styles)
            self.plot_graph.setLabel('left', self.left_label, **styles)
            self.plot_graph.setLabel('bottom', 'Время (сек)', **styles)
        else:
            self.color_background = 'Black'
            self.color_label = 'White'
            styles = {'color': self.color_label, 'font-size': '15px'}
            self.plot_graph.setBackground(background=self.color_background)
            self.plot_graph.setTitle(self.title, **styles)
            self.plot_graph.setLabel('left', self.left_label, **styles)
            self.plot_graph.setLabel('bottom', 'Время (сек)', **styles)

    def reset_data(self):
        self.graph_time = []
        self.graph_time_2 = []
        self.graph_value = []
        self.graph_value_2 = []
        self.plot_line_channel_1.setData(self.graph_time, self.graph_value)
        self.plot_line_channel_2.setData(self.graph_time_2, self.graph_value_2)


class CmdLogData:
    def __init__(self, data: list, time_pack):
        self.number_channel = None
        self.signal_level = None
        self.amplitude = None
        self.byte_a = None
        self.byte_b = None
        self.time_pack = None
        self.pars_packet(data, time_pack)
        self.save_pack_()
        self.file_name = None

    def pars_packet(self, data, time_pack):
        if data[2] & 0x01 == 0x01:
            self.number_channel = Channel.channel_1
        elif data[2] & 0x01 == 0x00:
            self.number_channel = Channel.channel_2
        self.signal_level = (((int(data[1]) * 256 + int(data[0])) * 10 / 16) * 8 / 15) / 10
        self.amplitude = (data[2] >> 1) * 100
        self.byte_a = data[0]
        self.byte_b = data[1]
        self.time_pack = time_pack

    def save_pack_(self):
        path = 'adc_data'
        if path not in os.listdir():
            try:
                os.makedirs(path)
            except OSError:
                logger.error(f'Создать директорию {path} не удалось')
            else:
                logger.info(f'Успешно создана директория {path} ')
        try:
            data = f'{self.byte_a}    {self.byte_b}    {self.number_channel}    {self.amplitude}     {self.time_pack} \n'
            if len(data) != 0:
                with open(f'{path}/{self.file_name}.txt', 'a+') as f:
                    try:
                        f.write(data)
                    except Exception as exs:
                        logger.error(exs)
        except OSError as exs:
            logger.error(exs)


class Channel(IntEnum):
    channel_1 = 0x01
    channel_2 = 0x00


def on_packet_received(packet):
    cmd = hw.rb.packet_to_dict(packet)['command']
    data = list(hw.rb.packet_to_dict(packet)['data'])
    time_packet = time.time()
    if cmd == 0x05:
        main.input_data.put([data, time_packet])


if __name__ == '__main__':
    app = QApplication([])
    main = GraphWidget()
    main.show()
    serial_worker = hw.open_port('COM33')
    hw.rb.on_packet_received_callback = on_packet_received
    hw.rb.send_cmd(hw.rb.Address.SENSOR, 0x1D, bytearray([0x27, 0x01]))
    main.start_program_time = time.time()
    app.exec()
