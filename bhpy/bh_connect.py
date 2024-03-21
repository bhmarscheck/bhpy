import logging
log = logging.getLogger(__name__)

try:
    import socket
    from zeroconf import Zeroconf, ServiceStateChange
    from Crypto.Random import get_random_bytes
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.Util.Padding import pad, unpad
    import threading
    from Crypto.PublicKey import RSA
    import appdirs
    from pathlib import Path
    import socketserver
    from queue import Queue
    from typing import Literal
except ModuleNotFoundError as err:
    # Error handling
    log.error(err)
    raise

request_handler_queue = Queue()


class _ImageReceiveHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server) -> None:
        super().__init__(request, client_address, server)

    def finish(self) -> None:
        return super().finish()

    def handle(self):
        data = self.request.recv(1)
        filename = self.request.recv(int.from_bytes(data)).decode()
        image_dir = (f"{appdirs.user_data_dir(appauthor='BH',appname='bhpy')}SPCConnect/temp/"
                     f"{filename}")
        Path(image_dir).parent.mkdir(parents=True, exist_ok=True)
        with open(image_dir, 'wb') as f:
            data = self.request.recv(4096)
            while data:
                f.write(data)
                try:
                    data = self.request.recv(4096)
                except ConnectionResetError:
                    break
        request_handler_queue.put(image_dir)


class _TraceReceiveHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server) -> None:
        super().__init__(request, client_address, server)

    def finish(self) -> None:
        return super().finish()

    def handle(self):
        trace_vals = []
        data = self.request.recv(4)
        values_to_receive = int.from_bytes(data, byteorder='little', signed=False)
        while values_to_receive > len(trace_vals):
            try:
                data = self.request.recv(4096)
            except ConnectionResetError:
                break
            for x in range(0, len(data), 4):
                trace_vals.append(int.from_bytes(data[x:x+4], byteorder='little', signed=False))
        request_handler_queue.put(trace_vals)


class BHConnect():
    IMAGE_TYPES = Literal["1stMoment", "Fit", "Fitted"]

    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.sock: socket.socket = None

        self.server_public_key = None

        self.private_key = None
        self.private_key_size = None

        self.service_info = None

    def __on_service_state_change(self, zeroconf: Zeroconf, service_type, name, state_change):
        if state_change is ServiceStateChange.Added:
            a = zeroconf.get_service_info(service_type, name)
            if a.name == f"SPCMRemoteControl:{self.mdns_service_id}._bhipc._tcp.local.":
                self.service_info = a
                self.wait.set()

    def __encrypt_msg(self, plain_msg):
        # generate session key
        session_key = get_random_bytes(16)

        # encrypt session key with public server rsa key
        cipher_rsa = PKCS1_OAEP.new(self.server_public_key)
        enc_session_key = cipher_rsa.encrypt(session_key)

        # encrypt public server key with session key
        cipher_aes = AES.new(session_key, AES.MODE_EAX)
        padded_msg = pad(plain_msg, 16)
        enc_padded_msg, tag = cipher_aes.encrypt_and_digest(padded_msg)
        return (enc_session_key + cipher_aes.nonce + tag + enc_padded_msg)

    def __decrypt_msg(self, encrypted_msg):
        n = self.private_key_size
        enc_session_key = encrypted_msg[:n]
        nonce = encrypted_msg[n:n+16]
        tag = encrypted_msg[n+16:n+32]
        cipher_text = encrypted_msg[n+32:]

        cipher_rsa = PKCS1_OAEP.new(self.private_key)
        session_key = cipher_rsa.decrypt(enc_session_key)

        cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
        padded_data = cipher_aes.decrypt_and_verify(cipher_text, tag)

        return (unpad(padded_data, 16))

    def __send(self, data):
        msg = self.__encrypt_msg(data)
        # print(f"Sending: {data}\nTo: {self.sock}")
        self.sock.sendall(msg)

    def __receive(self):
        data = self.sock.recv(4096)
        answer = self.__decrypt_msg(data)
        # print(f"Receiving: {answer}\nFrom: {self.sock}")
        return answer

    def __wait_host_port(self, host, port, duration=1):
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

    def find_spcm_instance(self, service_id: int = 1):
        instance_found = False
        if service_id is None:
            service_id = 1
        self.service_info = []
        self.mdns_service_id = service_id
        self.mdns_id_counter = 0
        retries = 0
        while retries < 3:
            zeroconf = Zeroconf()
            zeroconf.add_service_listener("_bhipc._tcp.local.",
                                          listener=(self.__on_service_state_change,))
            self.wait = threading.Event()
            self.wait.wait(3)
            zeroconf.remove_all_service_listeners()
            if self.service_info:
                host = self.service_info.server.split('.', 1)[0]
                if self.__wait_host_port(host, self.service_info.port):
                    instance_found = True
                    self.host = host
                    self.port = self.service_info.port
                    break
            retries += 1

        if not instance_found:
            self.host = None  # this might be redundant since both should be None anyway
            self.port = None

        return instance_found

    def connect_spcm_instance(self, host: str = None, port: int = None, service_id: int = None):
        if (host is None and port is not None) or (host is not None and port is None):
            raise ValueError("Arguments host and port must be provided or both must be None.")

        if host is None:  # when host is port is implicitly None as well
            # when self.host is None self.port is implicitly None as well (see constructor)
            if self.host is None:
                if not self.find_spcm_instance(service_id):
                    if service_id is None:
                        raise ValueError("Default instance (ID 1) not found. A discoverable ID, "
                                         "host and port, or self.host and self.port must be "
                                         "provided.")
                    else:
                        raise ValueError(f"Instance with ID {service_id} not found. A discoverable"
                                         " ID, host and port, or self.host and self.port must be "
                                         "provided.")
            host = self.host
            port = self.port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

        self.private_key = RSA.generate(2048)
        self.private_key_size = self.private_key.size_in_bytes()
        self.public_key = self.private_key.public_key()

        app_data_dir = f"{appdirs.user_data_dir(appauthor='BH',appname='bhpy')}SPCConnect"
        Path(app_data_dir).mkdir(parents=True, exist_ok=True)
        with open(f"{app_data_dir}/cli_private.pem", "wb") as f:
            f.write(self.private_key.export_key())
        with open(f"{app_data_dir}/send_cli_public.pem", "wb") as f:
            f.write(self.public_key.export_key())
        self.sock.sendall(self.public_key.export_key())
        enc_data = self.sock.recv(4096)
        data = self.__decrypt_msg(enc_data)
        with open(f"{app_data_dir}/svr_public.pem", "wb") as f:
            f.write(data)
        self.server_public_key = RSA.import_key(data)
        return self.command("Version:number")

    def disconnect_spcm_instance(self):
        self.sock.close()

    def shutdown_spcm_instance(self):
        self.__send(bytearray([0xFE]))

    def command(self, command) -> str:
        self.__send((f"${command}$").encode("ascii"))
        answer = self.__receive().decode()

        if answer.startswith("OK"):
            if answer.startswith("OK:"):
                answer = answer.split(':', 1)[1]
                try:
                    value = float(answer.strip("\x00"))
                    return value
                except Exception as e:
                    print(f"Adjust this to catch the specific exception {e}")
                    return answer
            return True
        else:
            raise ValueError(f'SPCM responded with:"{answer}"')

    def get_image(self, window=1, cycle=1, image_type: IMAGE_TYPES = "1stMoment"):
        file_receive_server = socketserver.TCPServer(('', 0), _ImageReceiveHandler,
                                                     bind_and_activate=True)
        # server_thread = threading.Thread(target=file_receive_server.serve_forever)
        # server_thread.start()

        port = file_receive_server.server_address[1]
        if image_type == "Fit":
            self.command(f"get_data:fitimage,{port},tiff,{window},{cycle}")
        elif image_type == "Fitted":
            self.command(f"get_data:fittedimage,{port},tiff,{window},{cycle}")
        else:
            self.command(f"get_data:image,{port},tiff,{window},{cycle}")
        file_receive_server.handle_request()
        return request_handler_queue.get()
        # file_receive_server.shutdown() # string_command is waiting for the response which itself
        # is
        # send after the image transfer is done therefore the server can be shut down
        # print(filename, end='', flush=True)

    def get_trace(self, trace_type=11, trace_number=1):
        file_receive_server = socketserver.TCPServer(('', 0), _TraceReceiveHandler,
                                                     bind_and_activate=True)
        # server_thread = threading.Thread(target=file_receive_server.serve_forever)
        # server_thread.start()

        # IPAddr = socket.gethostbyname(socket.gethostname())

        port = file_receive_server.server_address[1]
        self.command(f"get_data:trace,{port},imagedecay,{trace_number-1}")
        file_receive_server.handle_request()
        return request_handler_queue.get()

    def set_image_size(self, width, height):
        self.command("pressmenu:systemparameter")
        self.command(f"setparameter:pixelx,{width}")
        self.command(f"setparameter:pixely,{height}")
