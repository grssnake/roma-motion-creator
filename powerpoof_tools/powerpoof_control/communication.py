import os
import errno
import time
#from  bluetooth import BluetoothSocket, RFCOMM, BluetoothError
import re


class PipeWrapper(object):
    def __init__(self):
        self.out_path = "/tmp/powerpoof_out"
        self.in_path = "/tmp/powerpoof_in"
        try:
            self.out_pipe = os.open(self.out_path, os.O_RDWR | os.O_NONBLOCK)
            self.in_pipe = os.open(self.in_path, os.O_RDWR)
        except OSError as e:
            print("Failed to create FIFO: %s" % e)

    def read(self, n):
        try:
            result = os.read(self.out_pipe, n)
        except OSError as err:
            if err.errno == errno.EAGAIN or err.errno == errno.EWOULDBLOCK:
                result = ""
            else:
                raise

        return result

    def write(self, msg):
        os.write(self.in_pipe, msg)

"""
class BluetoothWrapper(object):
    def __init__(self, address):
        self.address = address
        self.socket = None
        self.connect()

    def connect(self):
        while 1:
            try:
                self.socket = BluetoothSocket(RFCOMM)
                self.socket.connect((self.address, 1))
                self.socket.setblocking(0)
                return
            except BluetoothError:
                time.sleep(0.05)

    def read(self, num):
        try:
            return self.socket.recv(num)
        except BluetoothError:
            return b""

    def write(self, data):
        length = len(data)
        if length > 0:
            while 1:
                try:
                    sent = self.socket.send(data)
                    break
                except BluetoothError:
                    continue
            if sent != length:
                raise Exception("NOT FULL DATA SENT AT ONCE")

    def close(self):
        self.socket.close()
"""

class Communicator(object):
    """
    This object wraps real serial or pipewrapper and defines all the protocol comms
    """

    def __init__(self, path, baudrate=9600):
        if path.startswith('/tmp'):
            self.comm = PipeWrapper()
#        elif re.match(r'[0-9a-fA-f]{2}:[0-9a-fA-f]{2}:[0-9a-fA-f]{2}:[0-9a-fA-f]{2}:[0-9a-fA-f]{2}:[0-9a-fA-f]{2}',
#                      path):
#            self.comm = BluetoothWrapper(path)
        else:
            import serial
            # non-blocking io
            self.comm = serial.Serial(path, baudrate=baudrate, timeout=0)
        self._buffer = ""

    def close(self):
        self.comm.close()

    def send(self, what):
        self.comm.write(what.encode('windows-1251'))
        self.comm.write('\n'.encode())

    def read_available(self):
        # r=self.comm.read(1024)
        return self.comm.read(1024).decode('windows-1251')

    def read_line(self):
        r = self._buffer
        while True:
            r += self.read_available()
            pos = r.find("\n")
            if pos != -1:
                line = r[:pos].replace("\r", "")
                self._buffer = r[pos + 1:]
                return line
            time.sleep(0.005)

    def wait_for_line(self):
        reply_str = self.read_line()
        pos = reply_str.find(" ")
        if pos != -1:
            type = reply_str[:pos]
            reply = reply_str[pos + 1:]
        else:
            type = reply_str
            reply = None
        return type, reply

    def wait_for_reply(self, request, params=""):
        if params:
            params = " " + params
        self.send(request + params)
        type = ""
        type, data = self.wait_for_line()
        return data

    def send_and_wait(self, request, params="", headers=None, reply=None):
        self.send_request(request, params=params)
        if headers is None:
            headers = [request]
        elif type(headers) != list:
            headers = [headers]
        return self.wait_reply(headers=headers, reply=reply)

    def send_request(self, request, params=None):
        if params:
            params = " " + params
        self.send(request + params)

    def wait_reply(self, headers, reply=None):
        header_type, data = self.wait_for_line()
        if header_type in headers:
            if reply:
                if type(reply) != list:
                    reply = [reply]
                return data in reply
            else:
                return data

    def send_and_check_reply(self, request, data_to_check, params=""):
        data = self.wait_for_reply(request, params=params)
        return data_to_check == data

    def wait_for_message2(self, request, reply_header=None, reply=None):
        while 1:
            type, message = self.wait_for_line()
            to_compare = reply_header if reply_header else request
            if type == to_compare and reply == message:
                return
            elif type == to_compare and reply is None:
                return message

    def send_and_wait2(self, message, reply_header=None, reply=None, params=None):
        self.send("{} {}".format(message, params if params else ""))
        return self.wait_for_reply(message, reply_header=reply_header, reply=reply)

    def wait_for(self, what):
        r = ""
        what = unicode(what)
        while True:
            r += self.read_available()
            # print (what, r.split('\r\n'), what in r.split('\r\n'))

            if what in r.replace('\r', '').split('\n'):
                break
            time.sleep(0.005)

    def wait_for_done(self, what):
        self.wait_for("done {}".format(what))

    def go(self, what, where, time):
        self.send("go {} {} {}".format(what, where, time))

    def move(self, what, where, time):
        self.send("move {} {} {}".format(what, where, time))

    def commit(self):
        self.send("commit")

    def return_to_start(self, time=2000):
        print("returning to start")
        self.move(1, 0, 2000)
        self.move(6, 0, 2000)
        self.move(2, -80, 2000)
        self.move(7, -80, 2000)
        self.move(3, 0, 2000)
        self.move(8, 0, 2000)
        self.commit()
        self.wait_for_done(6)
        print("returning to start..done")

    def sit_down(self, D, time=2000, block=True):
        """
        Should be done from standing position
        """
        print("sitting down")
        self.move(1, D, time)
        self.move(6, D, time)
        self.move(2, -80 + 2 * D, time)
        self.move(7, -80 + 2 * D, time)
        self.move(3, -D - 10, time)
        self.move(8, -D - 10, time)
        if block:
            self.commit()
            self.wait_for_done(8)
            print("sitting down..done")
