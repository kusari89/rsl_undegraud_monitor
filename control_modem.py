from application import MainWindow, Color
import hardware as hw
import app_logger
import serial.tools.list_ports
from datetime import datetime
from PyQt6.QtCore import QTimer
logger = app_logger.get_logger(__name__)


class ControlModem:
    def __init__(self):
        logger.info("control_modem заущен")
        self.main_window = MainWindow()
        self.serial_worker = None

        self.main_window.log.log_message(Color.white, f'{datetime.time(datetime.now())} Программа запущена\n')
        self.main_window.com_parameters.com_status.clicked.connect(self.start_work)
        self.main_window.sensor_mode.button_group.buttonClicked.connect(self.change_sensor_mode)

    def start_work(self, checked):
        com_name = self.main_window.com_parameters.com_list.currentText()
        if checked:
            try:
                self.serial_worker = hw.open_port(com_name)
            except serial.serialutil.SerialException:
                self.main_window.status_show(f'Ошибка открытия {com_name}')
                self.main_window.com_parameters.com_status.setChecked(False)
            else:
                self.main_window.enable_all_element(checked)
                hw.rb.send_cmd(hw.rb.Address.SENSOR, hw.CmdSensor.ping.value)
                hw.rb.send_cmd(hw.rb.Address.MODEM, hw.CmdModem.ping.value)
                hw.rb.send_cmd(hw.rb.Address.SENSOR, 0x1B)
                hw.rb.send_cmd(hw.rb.Address.SENSOR, 0x06)
                self.main_window.status_show(f' {com_name} открыт')
        else:
            try:
                hw.close_port(self.serial_worker)
            except AttributeError:
                self.main_window.status_show(f'Ошибка закрытия {com_name}')
            except serial.serialutil.SerialException:
                self.main_window.status_show(f'Непредвиденная ошибка {com_name}')
            else:
                self.main_window.enable_all_element(checked)
                self.main_window.status_show(f' {com_name} закрыт')
            finally:
                self.serial_worker = None

    def change_sensor_mode(self):
        channel1 = self.main_window.sensor_mode.channel1_box.isChecked()
        channel2 = self.main_window.sensor_mode.channel2_box.isChecked()
        buv = self.main_window.sensor_mode.buv_box.isChecked()
        if channel1:
            channel1 = 0x01
        else:
            channel1 = 0x00
        if channel2:
            channel2 = 0x02
        else:
            channel2 = 0x00
        if buv:
            buv = 0x04
        else:
            buv = 0x00
        sensor_mode = 0x28 + channel1 + channel2 + buv
        data = bytearray([sensor_mode])
        hw.rb.send_cmd(hw.rb.Address.SENSOR, 0x07, data)
        hw.rb.send_cmd(hw.rb.Address.SENSOR, 0x06)

