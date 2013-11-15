from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.wsgi import WSGIContainer
import argparse
import datetime
import logging
import math
import os
import signal
import sys

logger = logging.getLogger('revere')

root = logging.getLogger()
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.setLevel(logging.DEBUG)
root.addHandler(ch)

argparser = argparse.ArgumentParser(description='Revere - general purpose monitoring and alerting')
subparsers = argparser.add_subparsers(help='sub-command help', dest='subparser_name')

parser_run = subparsers.add_parser('run', help="run the server")
parser_run.add_argument("-p", "--port", default=5000, type=int, help="port to run the server on")

parser_init = subparsers.add_parser('init', help="initialize Revere - create a sqlite database and table")

argparser.add_argument("-c", "--config", default='config.py', help="specify config file")

args = argparser.parse_args()

config_path = args.config
if config_path[0] != '/':
    config_path = os.path.join(os.getcwd(), config_path)

if not os.environ.get('REVERE_CONFIG_FILE'):
    os.environ['REVERE_CONFIG_FILE'] = config_path
    print 'SET CONFIG PATH'
    
if True: # to keep this from being organized to the top of the file by PyDev
    from revere import app, db, initialize, scheduler

## Allow clean exiting
is_closing = False


def signal_handler(signum, frame):
    global is_closing
    logger.info('exiting...')
    is_closing = True


def try_exit():
    global is_closing
    if is_closing:
        # clean up here
        logger.info('Stopping ')
        IOLoop.instance().stop()
        scheduler.shutdown()
        logger.info('exit success')


if args.subparser_name == 'init':
    db.create_all()
    sys.exit(0)

if args.subparser_name == 'run':
    signal.signal(signal.SIGINT, signal_handler)
    initialize(app)
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(int(args.port))
    PeriodicCallback(try_exit, 100).start()
    logger.info('Tornado (webserver) starting')
    logger.info('Revere Server running on port %s' % args.port)
    IOLoop.instance().start()
    sys.exit(0)
