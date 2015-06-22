from twisted.internet.protocol import ClientFactory
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.conch.telnet import TelnetProtocol
from twisted.internet import stdio

class StdinProtocol(LineReceiver):
  from os import linesep as delimiter

  def __init__(self, network):
    self.network = network

  def write(self, text):
    self.transport.write('\007' + text)

  def print_prompt(self):
    self.write('#> ')

  def connectionMade(self):
    self.print_prompt()

  def lineReceived(self, line):
    self.network.transport.write(line)
    self.network.transport.write('\r\n')

    self.print_prompt()

class VikiProtocol(LineReceiver, TelnetProtocol):
  def connectionMade(self):
    self.stdin = StdinProtocol(self)
    stdio.StandardIO(self.stdin)

  def lineReceived(self, line):
    self.stdin.write('\033[2;K' + line + '\r\n\r\n')
    self.stdin.print_prompt()

class VikiFactory(ClientFactory):
  def buildProtocol(self, addr):
    p = VikiProtocol()
    p.factory = self
    return p

def main():
  reactor.connectTCP("localhost", 8123, VikiFactory())
  reactor.run()

if __name__ == '__main__':
  main()
