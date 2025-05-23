from bhpy import SpcQcX08
from threading import Thread
from queue import Queue

modules = [0, 1]
NUMBER_OF_MODULES = len(modules)


def run_measuring(tdc: SpcQcX08, index, dur, queue: Queue):
    print(f"modul {index+1} will collect for {dur} ms")
    tdc.card_focus = index
    queue.put(tdc.run_data_collection(0, 10000)+(10*(index+1)))


def run_data_extraction(tdc: SpcQcX08, index, queue: Queue):
    i = 0
    col = 0
    total_col = 0

    while True:
        col = tdc.get_event_triplets_from_buffer_to_file(index,
                                                         f'./data{index}',
                                                         i, 1_000_000, timeout_ms=3000)[1]
        total_col += col
        if col > 0:
            i += 1
        if not queue.empty():
            break

    while True:
        col = tdc.get_event_triplets_from_buffer_to_file(index,
                                                         f'./data{index}',
                                                         i, 1_000_000, timeout_ms=3000)[1]
        total_col += col
        if col > 0:
            i += 1
        if col == 0:
            break

    print(f"modul {index+1}({queue.get()}) collected {total_col} events in {i} files")


def run_measurement(tdc: SpcQcX08):
    measuring_threads: list[Thread] = []
    data_gathering_threads: list[Thread] = []

    tdc.card_focus = 0
    print(tdc.rates)
    tdc.card_focus = 1
    print(tdc.rates)
    print(tdc.firmware_version)

    for i in range(NUMBER_OF_MODULES):
        queue = Queue()
        ex_thread = Thread(target=run_data_extraction, kwargs={'tdc': tdc, 'index': i,
                                                               'queue': queue})
        data_gathering_threads.append(ex_thread)
        meas_thread = Thread(target=run_measuring, kwargs={'tdc': tdc, 'index': i,
                                                           'dur': 100*(i+1), 'queue': queue})
        measuring_threads.append(meas_thread)
        tdc.card_focus = i
        print(tdc.card_focus)
        meas_thread.start()
        ex_thread.start()

    for thread in measuring_threads:
        thread.join()
    for thread in data_gathering_threads:
        thread.join()


def prepare_measurement():
    tdc = SpcQcX08()
    tdc.init(modules)

    for i in range(NUMBER_OF_MODULES):
        tdc.card_focus = i
        tdc.initialize_data_collection(1_000_000_000)
        tdc.sync_channel = -1
        tdc.pulsgenerator_enable = True
        tdc.channel_enables = [False] * 8
        tdc.channel_enables = (0, True)
        tdc.channel_enables = (1+i, True)
        tdc.inputmodes = ['Calibration Input'] * 8
        tdc.hardware_countdown_enable = True
        tdc.hardware_countdown_time = (1+i) * 100_000_000

    return tdc


def main():
    tdc = prepare_measurement()
    run_measurement(tdc)


if __name__ == '__main__':
    main()
