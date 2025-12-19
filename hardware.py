import serial.tools.list_ports
from serial import Serial
from pyrb.rb.rb_device import RbDevice
from serial.threaded import ReaderThread, Protocol
from enum import Enum
import app_logger

logger = app_logger.get_logger(__name__)


def com_list():
    com_list_ = [element.device for element in serial.tools.list_ports.comports()]
    com_list_.sort()
    return com_list_


class SerialReader(Protocol):
    def connection_made(self, transport):
        logger.info("Connected, ready to receive data...")

    def data_received(self, data):
        rb.process_raw_data(data)

    def connection_lost(self, exc):
        logger.info("Connection lost... Error: " + str(exc))
        pass


def open_port(number_port):
    try:
        serial_port = Serial(number_port, 4800)
    except serial.serialutil.SerialException as exs:
        raise exs
    else:
        serial_worker = ReaderThread(serial_port, SerialReader)
        serial_worker.name = 'Thread COM'
        serial_worker.start()
        serial_worker_name = serial_worker.name
        logger.info(f'{serial_worker_name} запущен...')
        rb.send_raw_data_callback = serial_port.write
        return serial_worker


def choice_port():
    com_list_ = com_list()
    for i, number in enumerate(com_list_, start=1):
        print(f"Порт №{i} = {number}")
    while True:
        try:
            com_number = int(input('Введите номер компорта из списка\n')) - 1
            port = com_list_[com_number]
            port = open_port(port)
        except ValueError:
            print('Введено некорректное значение')
        except IndexError:
            print('Введено некорректное значение')
        except serial.serialutil.SerialException:
            print('Ошибка открытия порта')
        else:
            rb.send_cmd(rb.Address.SENSOR, 0x1B)
            break
    return port


def close_port(serial_worker):
    serial_worker.close()


rb = RbDevice()

Status_CMD_Modem = {
    'ping': False,
            }

Status_CMD_Sensor = {
    'ping': False,
            }


class CmdModem(Enum):
    ping = 0x00


class CmdSensor(Enum):
    ping = 0x00
