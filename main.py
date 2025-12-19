from colorama import init
from datetime import datetime

import graph_widget
from hardware import rb
from control_modem import ControlModem
import sys
from PyQt6.QtWidgets import QApplication
import app_logger
from application import Color as clr
import time

logger = app_logger.get_logger(__name__)

StatusAlarm = {
    'Sync1': False,
    'Sync2': False,
    'ExtWd': False,
}


class Colors:
    GREEN = "\033[92m"  # GREEN
    YELLOW = "\033[93m"  # YELLOW
    RED = "\033[91m"  # RED
    RESET = "\033[0m"  # RESET COLOR


def process_data_1C(data, time_):
    ext_wdt = data[0] & 0x20
    sync1 = data[0] & 0x08
    sync2 = data[0] & 0x10
    alarm1 = data[0] & 0x40
    alarm2 = data[0] & 0x80
    if alarm1 == 0x40:
        logger.info(f"{Colors.RED} {time_} Красная тревога канал 1{Colors.RESET}")
        window.main_window.log.log_message(clr.red, f"{time_} Красная тревога канал 1")
    if alarm2 == 0x80:
        logger.info(f"{Colors.RED} {time_} Красная тревога канал 2{Colors.RESET}")
        window.main_window.log.log_message(clr.red, f"{time_} Красная тревога канал 2")
    if ext_wdt == 0x20:
        StatusAlarm['ExtWd'] = True
        logger.info(f"{Colors.RED} {time_} БУВ включен{Colors.RESET}")
        window.main_window.log.log_message(clr.red, f"{time_} БУВ включен")
    elif ext_wdt == 0 and StatusAlarm['ExtWd'] is True:
        StatusAlarm['ExtWd'] = False
        logger.info(f"{Colors.GREEN} {time_} БУВ выключен{Colors.RESET}")
        window.main_window.log.log_message(clr.green, f"{time_} БУВ выключен")
    if sync1 == 0x08:
        StatusAlarm['Sync1'] = True
        logger.info(f"{Colors.RED} {time_} Потеря синхронизации 1 канала{Colors.RESET}")
        window.main_window.log.log_message(clr.red, f"{time_} Потеря синхронизации 1 канала")
    elif sync1 == 0 and StatusAlarm['Sync1'] is True:
        StatusAlarm['Sync1'] = False
        logger.info(f"{Colors.GREEN} {time_} Восстановление синхронизации 1 канала{Colors.RESET}")
        window.main_window.log.log_message(clr.green, f"{time_} Восстановление синхронизации 1 канала")
    if sync2 == 0x10:
        StatusAlarm['Sync2'] = True
        logger.info(f"{Colors.RED} {time_} Потеря синхронизации 2 канала{Colors.RESET}")
        window.main_window.log.log_message(clr.red, f"{time_} Потеря синхронизации 2 канала")
    elif sync2 == 0 and StatusAlarm['Sync2'] is True:
        StatusAlarm['Sync2'] = False
        logger.info(f"{Colors.GREEN} {time_} Восстановление синхронизации 2 канала{Colors.RESET}")
        window.main_window.log.log_message(clr.green, f"{time_} Восстановление синхронизации 2 канала")


def process_data_1B(data, time_):
    logger.info(f"{Colors.RESET} {time_} Начальный статус сенсоров:{Colors.RESET}")
    window.main_window.log.log_message(clr.white, f"{time_} Начальный статус сенсоров:")
    if (data[0] & 0x20) == 0x20:
        StatusAlarm['ExtWd'] = True
        logger.info(f"{Colors.RED} {time_} БУВ включен{Colors.RESET}")
        window.main_window.log.log_message(clr.red, f"{time_} БУВ включен")
    elif (data[0] & 0x20) == 0x00:
        StatusAlarm['ExtWd'] = False
        logger.info(f"{Colors.GREEN} {time_} БУВ выключен{Colors.RESET}")
        window.main_window.log.log_message(clr.green, f"{time_} БУВ выключен")
    if (data[0] & 0x10) == 0x10:
        StatusAlarm['Sync2'] = True
        logger.info(f"{Colors.RED} {time_} Отсутствует синхронизация 2 канала{Colors.RESET}")
        window.main_window.log.log_message(clr.red, f"{time_} Отсутствует синхронизация 2 канала")
    elif (data[0] & 0x10) == 0x00:
        StatusAlarm['Sync2'] = False
        logger.info(f"{Colors.GREEN} {time_} 2 канал синхронизирован{Colors.RESET}")
        window.main_window.log.log_message(clr.green, f"{time_} 2 канал синхронизирован")
    if (data[0] & 0x08) == 0x08:
        StatusAlarm['Sync1'] = True
        logger.info(f"{Colors.RED} {time_} Отсутствует синхронизация 1 канала{Colors.RESET}")
        window.main_window.log.log_message(clr.red, f"{time_} Отсутствует синхронизация 1 канала")
    elif (data[0] & 0x08) == 0x00:
        StatusAlarm['Sync1'] = False
        logger.info(f"{Colors.GREEN} {time_} 1 канал синхронизирован{Colors.RESET}")
        window.main_window.log.log_message(clr.green, f"{time_} 1 канал синхронизирован")


def on_packet_received(packet):
    global StatusAlarm
    global dt_start
    pack = rb.packet_to_dict(packet)
    cmd = rb.packet_to_dict(packet)['command']
    data = list(rb.packet_to_dict(packet)['data'])
    time_ = datetime.time(datetime.now())
    time_packet = time.time()
    if cmd == 0x1D and data[0] == 0x82:
        logger.info(f"{Colors.YELLOW} {time_} Желтая тревога{Colors.RESET}")
        window.main_window.log.log_message(clr.yellow, f"{time_} Желтая тревога")
    if cmd == 0x1B:
        process_data_1B(data, time_)
    if cmd == 0x1C:
        process_data_1C(data, time_)
    if cmd == 0x05:
        window.main_window.graph.input_data.put([data, time_packet, pack])
    if cmd == 0x06:
        window.main_window.sensor_mode.change_sensor_mode_status(data)


if __name__ == '__main__':
    logger.info("Программа стартует")
    init()
    dt_start = datetime.now().strftime('%d_%m_%Y %H_%M_%S')
    graph_widget.CmdLogData.file_name = f'OutFile_{dt_start}'
    app = QApplication(sys.argv)
    window = ControlModem()
    window.main_window.show()
    rb.on_packet_received_callback = on_packet_received
    app.exec()
