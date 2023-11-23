import socket
from zeroconf import Zeroconf, ServiceStateChange
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Util.Padding import pad, unpad
import threading
from Crypto.PublicKey import RSA
import appdirs
import pathlib
import socketserver
from queue import Queue
import re
import time
import asyncio
from typing import Literal

requestHandlerQueue = Queue()

class _ImageReceiveHandler(socketserver.BaseRequestHandler):
  def __init__(self, request, client_address, server) -> None:
    super().__init__(request, client_address, server)

  def finish(self) -> None:
    return super().finish()
  
  def handle(self):
    data = self.request.recv(1)
    filename = self.request.recv(int.from_bytes(data)).decode()
    imageDir = f"{appdirs.user_data_dir(appauthor='BH',appname='SPCRemote')}/temp/{filename}"
    pathlib.Path(imageDir).parent.mkdir(parents=True, exist_ok=True)
    with open(imageDir,'wb') as f:
      data = self.request.recv(4096)
      while data:
        f.write(data)
        try:
          data = self.request.recv(4096)
        except ConnectionResetError:
          break
    requestHandlerQueue.put(imageDir)
  
class _TraceReceiveHandler(socketserver.BaseRequestHandler):
  def __init__(self, request, client_address, server) -> None:
    super().__init__(request, client_address, server)

  def finish(self) -> None:
    return super().finish()
  
  def handle(self):
    traceVals = []
    data = self.request.recv(4)
    valuesToReceive = int.from_bytes(data, byteorder='little', signed=False)
    while valuesToReceive > len(traceVals):
      try:
        data = self.request.recv(4096)
      except ConnectionResetError:
        break
      [traceVals.append(int.from_bytes(data[x:x+4], byteorder='little', signed=False)) for x in range(0, len(data), 4)]
    requestHandlerQueue.put(traceVals)

class BHRemoteControl():
  IMAGE_TYPES = Literal["1stMoment", "Fit", "Fitted"]

  def __init__(self, host = None, port = None):
    self.host = host
    self.port = port
    self.sock: socket.socket = None

    self.serverPublicKey = None

    self.privateKey = None
    self.privateKeySize = None

    self.serviceInfos = []
  
  def __on_service_state_change(self, zeroconf: Zeroconf, service_type, name, state_change):
    if state_change is ServiceStateChange.Added:
      a = zeroconf.get_service_info(service_type, name)
      print(a)
      name: list[str] = a.name.split('.', 1)[0].split(':')
      if name[0] == "SPCMRemoteControl":
        self.serviceInfos.append(a)
        id = name[1].split('(', 1)
        if int(id[0]) == self.mdnsServiceID:
          try:
            if int(id[1].split(')', 1)[0]) >= self.mdnsIDCounter:
              self.wait.set()
          except IndexError:
            if self.mdnsIDCounter == 0:
              self.wait.set()

  def __encrypt_msg(self, plainMsg):
    #generate session key
    sessionKey = get_random_bytes(16)
    
    #encrypt session key with public server rsa key
    cipherRsa = PKCS1_OAEP.new(self.serverPublicKey)
    enc_session_key = cipherRsa.encrypt(sessionKey)

    #encrypt public server key with session key
    cipher_aes = AES.new(sessionKey, AES.MODE_EAX)
    paddedMsg = pad(plainMsg, 16)
    encPaddedMsg, tag = cipher_aes.encrypt_and_digest(paddedMsg)
    return (enc_session_key + cipher_aes.nonce + tag + encPaddedMsg)

  def __decrypt_msg(self, encryptedMsg):
    n = self.privateKeySize
    encSessionKey = encryptedMsg[:n]
    nonce = encryptedMsg[n:n+16]
    tag = encryptedMsg[n+16:n+32]
    cipherText = encryptedMsg[n+32:]

    cipherRsa = PKCS1_OAEP.new(self.privateKey)
    sessionKey = cipherRsa.decrypt(encSessionKey)

    cipherAes = AES.new(sessionKey, AES.MODE_EAX, nonce)
    paddedData = cipherAes.decrypt_and_verify(cipherText, tag)

    return(unpad(paddedData, 16))
  
  def __send(self, data):
    msg = self.__encrypt_msg(data)
    #print(f"Sending: {data}\nTo: {self.sock}")
    self.sock.sendall(msg)

  def __receive(self):
    data = self.sock.recv(4096)
    answer = self.__decrypt_msg(data)
    #print(f"Receiving: {answer}\nFrom: {self.sock}")
    return answer
  
  def __wait_host_port(self, host, port, duration = 1):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(duration)
    try:
      s.connect((host, port))
      s.sendall("ping".encode())
      s.shutdown(socket.SHUT_RDWR)
      return True
    except Exception as e:
      print(e)
      return False
    finally:
      s.close()

  def findSpcmInstance(self, serviceID: int = 1):
    instanceFound = False
    if serviceID is None:
      serviceID = 1
    self.serviceInfos = []
    self.mdnsServiceID = serviceID
    self.mdnsIDCounter = 0
    retries = 0
    while not instanceFound and (retries < 3):
      zeroconf = Zeroconf()
      zeroconf.add_service_listener("_bhipc._tcp.local.", listener=(self.__on_service_state_change,))
      self.wait = threading.Event()
      self.wait.wait(3)
      zeroconf.remove_all_service_listeners() 
      if self.serviceInfos:
        for serviceInfo in self.serviceInfos:
          IDCount = re.findall("(?<=\()\d+(?=\))", serviceInfo.name)
          try:
            idCount = int(IDCount[0])
            if idCount > self.mdnsIDCounter:
              self.mdnsIDCounter = idCount
              bestMatch = serviceInfo
          except IndexError:
            if self.mdnsIDCounter == 0:
              bestMatch = serviceInfo

        host = bestMatch.server.split('.', 1)[0]
        if self.__wait_host_port(host, bestMatch.port):
          instanceFound = True
          self.host = host
          self.port = bestMatch.port
        else:
          retries += 1
          self.mdnsIDCounter += 1
      else:
        retries += 1

    if not instanceFound:
      self.host = None
      self.port = 54711 #TODO set to whatever is default

    return instanceFound
  
  def connectSpcmInstance(self, host: str = None, port: int = None, serviceID: int = None):
    if host is None:
      if self.host is None or self.port is None:
        self.findSpcmInstance(serviceID)
      host = self.host
    else:
      self.host = host
    
    if port is None:
      if self.host is None or self.port is None:
        self.findSpcmInstance(serviceID)
      port = self.port
    else:
      self.port = port
    
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.connect((host, port))

    self.privateKey = RSA.generate(2048)
    self.privateKeySize = self.privateKey.size_in_bytes()
    self.publicKey = self.privateKey.public_key()

    appDataDir = appdirs.user_data_dir(appauthor='BH',appname='SPCConnectPythonClient')
    pathlib.Path(appDataDir).mkdir(parents=True, exist_ok=True)
    with open(f"{appDataDir}/cli_private.pem", "wb") as f:
      f.write(self.privateKey.export_key())
    with open(f"{appDataDir}/send_cli_public.pem", "wb") as f:
      f.write(self.publicKey.export_key())
    self.sock.sendall(self.publicKey.export_key())
    encData = self.sock.recv(4096)
    data = self.__decrypt_msg(encData)
    with open(f"{appDataDir}/svr_public.pem", "wb") as f:
      f.write(data)
    self.serverPublicKey = RSA.import_key(data)
    return self.command("Version:number")
  
  def disconnectSpcmInstance(self):
    self.sock.close()
  
  def shutdownSpcmInstance(self):
    self.__send(bytearray([0xFE]))
  
  def command(self, command) -> str:
    self.__send((f"${command}$").encode("ascii"))
    answer = self.__receive().decode()

    if answer.startswith("OK"):
      if answer.startswith("OK:"):
        answer = answer.split(':')[1]
        try:
          value = float(answer)
          return value
        except:
          return answer
      return True
    else:
      raise ValueError(f'SPCM responded with:"{answer}"')
  
  def getImage(self, window = 1, cycle = 1, imageType: IMAGE_TYPES = "1stMoment"):
    fileReceiveServer = socketserver.TCPServer(('', 0), _ImageReceiveHandler, bind_and_activate=True)
    #serverThread = threading.Thread(target=fileReceiveServer.serve_forever)
    #serverThread.start()

    port = fileReceiveServer.server_address[1]
    if imageType == "Fit":
      self.command(f"getData:fitimage,{port},tiff,{window},{cycle}")
    elif imageType == "Fitted":
      self.command(f"getData:fittedimage,{port},tiff,{window},{cycle}")
    else:
      self.command(f"getData:image,{port},tiff,{window},{cycle}")
    fileReceiveServer.handle_request()
    return requestHandlerQueue.get()
    #fileReceiveServer.shutdown() # stringCommand is waiting for the response which itself is send after the image transfer is done therefore the server can be shut down
    #print(filename, end='', flush=True)
  
  def getTrace(self, traceType = 11, traceNumber = 1):
    fileReceiveServer = socketserver.TCPServer(('', 0), _TraceReceiveHandler, bind_and_activate=True)
    #serverThread = threading.Thread(target=fileReceiveServer.serve_forever)
    #serverThread.start()

    IPAddr=socket.gethostbyname(socket.gethostname())

    port = fileReceiveServer.server_address[1]
    self.command(f"getData:trace,{port},imagedecay,{traceNumber-1}")
    fileReceiveServer.handle_request()
    return requestHandlerQueue.get()
  
  def setImageSize(self, width, height):
    try:
      self.command("pressmenu:systemparameter")
      self.command(f"setparameter:pixelx,{width}")
      self.command(f"setparameter:pixely,{height}")
    except:
      pass