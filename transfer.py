import asyncore
import socket
import sys

mark = '[c319q]'


def encode(bytes):
    if bytes.find(mark) is not -1:
        return bytes

    encoded_bytes = ''
    bound = 20
    for c in bytes:
        bound -= 1
        if bound > 0:
            encoded_bytes += (mark + c)
        else:
            encoded_bytes += c
    # print "Encode: " + bytes + " => " + encoded_bytes
    return encoded_bytes


def decode(bytes):
    decoded_bytes = bytes.replace(mark, '')
    # print "Decode: " + bytes + " => " + decoded_bytes
    return decoded_bytes


class Forwarder(asyncore.dispatcher):
    def __init__(self, ip, port, remoteip, remoteport, backlog=5):
        asyncore.dispatcher.__init__(self)
        self.remoteip = remoteip
        self.remoteport = remoteport
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((ip, port))
        self.listen(backlog)

    def handle_accept(self):
        conn, addr = self.accept()
        # print '--- Connect --- '
        Sender(Receiver(conn), self.remoteip, self.remoteport)


class LocalForwarder(Forwarder):

    def handle_accept(self):
        conn, addr = self.accept()
        print '--- Connect --- '
        EncodeSender(Receiver(conn), self.remoteip, self.remoteport)


class VPSForwarder(Forwarder):

    def handle_accept(self):
        conn, addr = self.accept()
        print '--- Connect --- '
        Sender(EncodeReceiver(conn), self.remoteip, self.remoteport)


class Sender(asyncore.dispatcher):
    def __init__(self, receiver, remoteaddr, remoteport):
        asyncore.dispatcher.__init__(self)
        self.receiver = receiver
        receiver.sender = self
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((remoteaddr, remoteport))

    def handle_connect(self):
        pass

    def handle_read(self):
        read = self.recv(4096)
        print '<-- %04i' % len(read)
        self.receiver.to_remote_buffer += read

    def writable(self):
        return len(self.receiver.from_remote_buffer) > 0

    def handle_write(self):
        sent = self.send(self.receiver.from_remote_buffer)
        print '--> %04i' % sent
        self.receiver.from_remote_buffer = self.receiver.from_remote_buffer[sent:]

    def handle_close(self):
        self.close()
        self.receiver.close()


class Receiver(asyncore.dispatcher):
    def __init__(self, conn):
        asyncore.dispatcher.__init__(self, conn)
        self.from_remote_buffer = ''
        self.to_remote_buffer = ''
        self.sender = None

    def handle_connect(self):
        pass

    def handle_read(self):
        read = self.recv(4096)
        print '%04i -->' % len(read)
        self.from_remote_buffer += read

    def writable(self):
        return len(self.to_remote_buffer) > 0

    def handle_write(self):
        sent = self.send(self.to_remote_buffer)
        print '%04i <--' % sent
        self.to_remote_buffer = self.to_remote_buffer[sent:]

    def handle_close(self):
        self.close()
        if self.sender:
            self.sender.close()


class EncodeSender(Sender):

    def handle_read(self):
        read = self.recv(4096)
        print '<-- %04i' % len(read)
        self.receiver.to_remote_buffer += decode(read)

    def handle_write(self):
        self.receiver.from_remote_buffer = encode(self.receiver.from_remote_buffer)

        sent = self.send(self.receiver.from_remote_buffer)
        print '--> %04i' % sent
        self.receiver.from_remote_buffer = self.receiver.from_remote_buffer[sent:]


class EncodeReceiver(Receiver):

    def handle_read(self):
        read = self.recv(4096)
        print '%04i -->' % len(read)
        self.from_remote_buffer += decode(read)

    def handle_write(self):
        self.to_remote_buffer = encode(self.to_remote_buffer)

        sent = self.send(self.to_remote_buffer)
        print '%04i <--' % sent
        self.to_remote_buffer = self.to_remote_buffer[sent:]


def help():
    print "Example:"
    print "\tpython " + sys.argv[0] + " local"
    print "\tpython " + sys.argv[0] + " vps"


if __name__ == '__main__':
    if len(sys.argv) is 2:
        if sys.argv[1] == "vps":
            local_ip = "0.0.0.0"
            local_port = 2413
            to_ip = "127.0.0.1"
            to_port = 2401

            print "vps mode: " + local_ip + ":" + str(local_port) + " => " + to_ip + ":" + str(to_port)
            VPSForwarder(local_ip, local_port, to_ip, to_port)  # VPS
            asyncore.loop()
        else:
            local_ip = "localhost"
            local_port = 2401
            to_ip = "129.226.126.132"
            to_port = 2413

            print "local mode: " + local_ip + ":" + str(local_port) + " => " + to_ip + ":" + str(to_port)
            LocalForwarder(local_ip, local_port, to_ip, to_port)  # local
            asyncore.loop()
    help()
