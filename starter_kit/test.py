import pyqpanda as pq

qasm = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
x q[0];
measure q[0] -> c[0];
measure q[1] -> c[1];
"""

machine = pq.CPUQVM()
machine.init_qvm()
prog, qubits, cbits = pq.convert_qasm_string_to_qprog(qasm, machine)
result = machine.run_with_configuration(prog, cbits, 1000)
print(result)
machine.finalize()
