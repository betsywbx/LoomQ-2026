import pyqpanda as pq
print([x for x in dir(pq.real_chip_type) if not x.startswith('_')])