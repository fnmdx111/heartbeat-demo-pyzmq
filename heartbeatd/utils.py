import socket


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ret = s.getsockname()[0]

    s.close()
    return ret


def msg(act, **d):
    ret = {'act': act}
    ret.update(d)

    return ret


def unpack_ret(m):
    if m['act'] == 'ret':
        return m['status'], m['payload']
    else:
        return m


import logging


def logger():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)s:%(asctime)s:%(filename)s: '
                               '%(message)s')
    return logging.getLogger(__name__)

