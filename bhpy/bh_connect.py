"""SPCConnect client wrapper.

This module provides a small, typed client (`BHConnect`) to discover and talk
to an SPCConnect instance over TCP. It handles the session key exchange,
message encryption, and convenience helpers to fetch images and traces.

The lower-level TCP server handlers in this module are implementation details
used to receive large payloads (images, traces) over a temporary local port.
"""

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


class CustomTCPServer(socketserver.TCPServer):
    """Tiny TCP server used to receive streamed data.

    This server is spun up on a random local port to receive images/traces
    that SPCConnect sends back after a request. Do not use this class
    directly; it is an internal helper for `BHConnect.get_image`/`get_trace`.
    """
    def __init__(self, server_address, request_handler_class,
                 request_handler_queue, done_queue=None,
                 bind_and_activate=True, all_windows=False,
                 file_name=None):
        super().__init__(server_address, request_handler_class, bind_and_activate)
        self.file_name = file_name
        self.all_windows = all_windows
        self.request_handler_queue = request_handler_queue
        self.done_queue = done_queue


class _ImageReceiveHandler(socketserver.BaseRequestHandler):
    """Receives image bytes and writes them to a temp file.

    Enqueues the resulting file path into ``request_handler_queue`` and
    signals completion via ``done_queue`` when SPCConnect finishes sending.
    """
    def __init__(self, request, client_address, server: CustomTCPServer) -> None:
        self.file_name = server.file_name
        self.all_windows = server.all_windows
        self.request_handler_queue: Queue = server.request_handler_queue
        self.done_queue: Queue = server.done_queue
        super().__init__(request, client_address, server)

    def finish(self) -> None:
        return super().finish()

    def handle(self):
        """Receive a single image file from the remote SPCConnect instance."""
        data = self.request.recv(1)
        if self.all_windows or self.file_name is None:
            filename = self.request.recv(int.from_bytes(data)).decode()
            if filename == 'EOT':
                self.done_queue.put(True)
                return
        else:
            filename = self.file_name
            dummy_read = self.request.recv(int.from_bytes(data)).decode()
            if dummy_read == 'EOT':
                self.done_queue.put(True)
                return
        image_dir = (f"{appdirs.user_data_dir(appauthor='BH', appname='bhpy')}SPCConnect/temp/"
                     f"{filename}")
        self.request_handler_queue.put(image_dir)
        Path(image_dir).parent.mkdir(parents=True, exist_ok=True)
        with open(image_dir, 'wb') as f:
            data = self.request.recv(4096)
            while data:
                f.write(data)
                try:
                    data = self.request.recv(4096)
                except ConnectionResetError:
                    break


class _TraceReceiveHandler(socketserver.BaseRequestHandler):
    """Receives a trace as uint32 chunks into a list and enqueues it."""
    def __init__(self, request, client_address, server: CustomTCPServer) -> None:
        self.request_handler_queue: Queue = server.request_handler_queue
        super().__init__(request, client_address, server)

    def finish(self) -> None:
        return super().finish()

    def handle(self):
        """Receive a trace consisting of 32-bit little-endian values."""
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
        self.request_handler_queue.put(trace_vals)


class BHConnect():
    """Client for discovering and controlling SPCConnect.

    Typical usage:

    - Discover instance via mDNS and connect: ``connect_spcm_instance()``
    - Send simple commands: ``command("Version:number")``
    - Receive data: ``get_image(...)`` / ``get_trace(...)``

    Encryption is handled transparently. The client writes the temporary
    key files under the per-user data directory for debugging purposes.
    """
    IMAGE_TYPES = Literal["1stMoment", "Fit", "Fitted", "TauChannel"]

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
        """Discover an SPCConnect instance via mDNS.

        Args:
            service_id: The SPCConnect mDNS service suffix (default 1).

        Returns:
            ``True`` if a reachable instance was found and ``host``/``port``
            are set accordingly, otherwise ``False``.
        """
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
        """Connect to SPCConnect and perform key exchange.

        Either provide both ``host`` and ``port``, or let the client discover
        the instance via ``service_id``. On success, the SPCConnect protocol
        version is validated.

        Args:
            host: Hostname or IP of SPCConnect.
            port: TCP port of SPCConnect.
            service_id: Optional mDNS service id to auto-discover.

        Returns:
            The protocol version string (e.g. ``"OK: 2.0.0"``).

        Raises:
            ValueError: If only one of ``host`` or ``port`` is provided.
            RuntimeError: If the protocol version is unsupported.
        """
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

        app_data_dir = f"{appdirs.user_data_dir(appauthor='BH', appname='bhpy')}SPCConnect"
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
        protocol_version_str = self.command("Version:number")
        protocol_version = [int(x) for x in protocol_version_str.split(' ')[1].split('.')]
        if protocol_version[0] != 2:
            raise RuntimeError('Wrong SPCConnect protocol version ('
                               f'{protocol_version_str}). BHConnect is suited '
                               'for SPCConnect protocol V 2.0.0 up until, but '
                               'not including V 3.0.0')
        return self.command("Version:number")

    def disconnect_spcm_instance(self):
        """Close the TCP socket to SPCConnect."""
        self.sock.close()

    def shutdown_spcm_instance(self):
        """Ask SPCConnect to shut down gracefully (if supported)."""
        self.__send(bytearray([0xFE]))

    def command(self, command) -> str:
        """Send a plain SPCConnect command and return its response.

        Args:
            command: The command string without surrounding ``$`` markers.

        Returns:
            Either ``True`` for bare ``OK``, the parsed float when possible,
            or the raw string payload returned by SPCConnect.

        Raises:
            ValueError: If SPCConnect responds with an error (non-OK).
        """
        self.__send((f"${command}$").encode("ascii"))
        answer = self.__receive().decode()

        if answer.startswith("OK"):
            if answer.startswith("OK:"):
                answer = answer.split(':', 1)[1]
                try:
                    value = float(answer.strip("\x00"))
                    return value
                except ValueError:
                    return answer
                except Exception as e:
                    print(f"Adjust this to catch the specific exception: {e}")
                    return answer
            return True
        else:
            raise ValueError(f'SPCM responded with:"{answer}"')

    def get_image(self, window=1, cycle=1, image_type: IMAGE_TYPES = "1stMoment",
                  fit_config: tuple[str, int] = None, tau_channel: str = None):
        """Request image data and receive it as local temp files.

        Depending on the requested ``image_type`` and arguments, the method
        spins up a local TCP server for the duration of the transfer, and
        returns a list of file paths to the received TIFF images.

        Args:
            window: Window index (use ``-1`` for all windows).
            cycle: Cycle index for the selected window.
            image_type: One of ``"1stMoment"``, ``"Fit"``, ``"Fitted"``,
                or ``"TauChannel"``.
            fit_config: Optional tuple of (config_name, int_value) for fit images.
            tau_channel: Optional tau channel when ``image_type`` is ``TauChannel``.

        Returns:
            List of absolute file paths to the received images.
        """
        file_name = None
        all_windows = window == -1
        request_handler_queue = Queue()
        done_queue = Queue()
        file_receive_server = CustomTCPServer(('', 0), _ImageReceiveHandler,
                                              bind_and_activate=True,
                                              file_name=file_name,
                                              all_windows=all_windows,
                                              request_handler_queue=request_handler_queue,
                                              done_queue=done_queue)
        # server_thread = threading.Thread(target=file_receive_server.serve_forever)
        # server_thread.start()

        port = file_receive_server.server_address[1]
        if fit_config is None:
            fit_config_cmd = ''
        else:
            fit_config_cmd = f',config,{fit_config[0]},{fit_config[1]}'
        if all_windows:
            window_selection = ''
        else:
            window_selection = f',{window},{cycle}'
        if image_type == "Fit":
            self.command(f"getData:fitimage,{port},tiff{window_selection}{fit_config_cmd}")
        elif image_type == "Fitted":
            self.command(f"getData:fittedimage,{port},tiff{window_selection}")
        elif image_type == 'TauChannel':
            self.command(f'getData:tauchannel,{port},tiff,{window},{tau_channel}')
        elif image_type == 'TauChannels':
            all_windows = True
            response = self.command(f'getData:tauchannel,{port},tiff,{window}')
        else:
            self.command(f"getData:image,{port},tiff{window_selection}")
        while done_queue.empty():
            file_receive_server.handle_request()

        response = []
        while not request_handler_queue.empty():
            response.append(request_handler_queue.get())
        return response
        # file_receive_server.shutdown() # string_command is waiting for the response which itself
        # is
        # send after the image transfer is done therefore the server can be shut down
        # print(filename, end='', flush=True)

    def get_trace(self, trace_type=11, trace_number=1):
        """Request a trace and return the values as a list of ints.

        Args:
            trace_type: Trace type (currently unused; reserved for extension).
            trace_number: One-based trace index.

        Returns:
            List of unsigned 32-bit values representing the trace.
        """
        request_handler_queue = Queue()
        file_receive_server = CustomTCPServer(('', 0), _TraceReceiveHandler,
                                              bind_and_activate=True,
                                              request_handler_queue=request_handler_queue)
        # server_thread = threading.Thread(target=file_receive_server.serve_forever)
        # server_thread.start()

        # IPAddr = socket.gethostbyname(socket.gethostname())

        port = file_receive_server.server_address[1]
        self.command(f"getData:trace,{port},imagedecay,{trace_number-1}")
        file_receive_server.handle_request()
        return request_handler_queue.get()

    def set_image_size(self, width, height):
        """Set image dimensions in SPCConnect.

        Args:
            width: Image width in pixels.
            height: Image height in pixels.
        """
        self.command("pressmenu:systemparameter")
        self.command(f"setparameter:pixelx,{width}")
        self.command(f"setparameter:pixely,{height}")
