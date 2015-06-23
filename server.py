import functools
import os
import random

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.logger import Logger, LogLevel, ILogObserver, formatEvent

from cobe.brain import Brain

from zope.interface import provider

@provider(ILogObserver)
def printing_observer(event):
  print formatEvent(event)

log = Logger(observer = printing_observer)

class MessagePool(object):
  def __init__(self, filepath):
    with open(filepath, 'r') as f:
      self.messages = [l.strip() for l in f.readlines()]

  def get_message(self):
    return random.choice(self.messages)

class Chatter(object):
  def __init__(self):
    self.brain = Brain('cobe.brain')

    with open('seed.txt', 'r') as f:
      text = [l.strip() for l in f.read().replace('\n', ' ').replace('.', '\n').replace('?', '\n').replace('\xa0', ' - ').split('\n') if l.strip()]

      for line in text:
        self.brain.learn(line)

  def reply(self, message):
    return self.brain.reply(message)

  def learn(self, line):
    self.brain.learn(line)

class VikiMasterChat(LineReceiver):
  def send_reply(self, msg):
    log.debug('master: slave says: "%s"' % msg)

    msg = 'slave> ' + msg

    self.sendLine(msg.encode('ascii', 'replace'))

  def connectionMade(self):
    VikiMasterFactory.masters.append(self)

    log.info('master connected!')

  def connectionLost(self, reason):
    VikiMasterFactory.masters.remove(self)

    log.info('master disconnected!')

  def lineReceived(self, line):
    log.debug('master: master says: "%s"' % line)

    line = line.strip()
    if not line:
      log.debug('master: line was empty, ignore')
      return

    for slave in VikiSlaveFactory.slaves:
      slave.send_reply(line)

class VikiSlaveChat(LineReceiver):
  def __init__(self, chatbot, msgpool):
    self.chatbot = chatbot
    self.msgpool = msgpool

    self.last_message = None

  def send_reply(self, msg):
    log.debug('slave: sending reply: msg="%s"' % msg)

    self.sendLine(msg.encode('ascii', 'replace'))

    if msg:
      self.last_message = msg

  def connectionMade(self):
    VikiSlaveFactory.slaves.append(self)

    for i in range(0, 80):
      self.send_reply('')

    self.send_reply(self.msgpool.get_message())
    self.send_reply('')
    self.send_reply('ROBCO INDUSTRIES UNIFIED OPERATING SYSTEM')
    self.send_reply('+++ Server #79 +++')
    self.send_reply('')
    self.send_reply('Pozdrav. Uvitani. $%^&%$&*^H^H^H^H')
    self.send_reply('Co pro vas dnes mohu udelat?')
    self.send_reply('')

  def connectionLost(self, reason):
    VikiSlaveFactory.slaves.remove(self)

  def lineReceived(self, line):
    log.debug('slave: line received: line="%s"' % line)

    line = line.strip()
    if not line:
      log.debug('slave: line was empty, ignore')
      return

    if VikiMasterFactory.masters:
      for master in VikiMasterFactory.masters:
        master.send_reply(line)

    else:
      reply = self.chatbot.reply(line)

      self.chatbot.learn(self.last_message)
      self.chatbot.learn(line)

      self.send_reply(reply)

class VikiMasterFactory(Factory):
  masters = []

  def buildProtocol(self, addr):
    return VikiMasterChat()

class VikiSlaveFactory(Factory):
  slaves = []

  def __init__(self):
    self.chatbot = Chatter()
    self.msgpool = MessagePool(os.getcwd() + '/messages.txt')

  def buildProtocol(self, addr):
    return VikiSlaveChat(self.chatbot, self.msgpool)

reactor.listenTCP(8123, VikiSlaveFactory())
reactor.listenTCP(8124, VikiMasterFactory())
reactor.run()
