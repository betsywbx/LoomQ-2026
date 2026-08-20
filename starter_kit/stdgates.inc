
// OpenQASM 3.0 Standard Gates
gate x a { U(pi, 0, pi) a; }
gate y a { U(pi, pi/2, pi/2) a; }
gate z a { U(0, 0, pi) a; }
gate h a { U(pi/2, 0, pi) a; }
gate s a { p(pi/2) a; }
gate sdg a { p(-pi/2) a; }
gate t a { p(pi/4) a; }
gate tdg a { p(-pi/4) a; }
gate rx(theta) a { U(theta, -pi/2, pi/2) a; }
gate ry(theta) a { U(theta, 0, 0) a; }
gate cx a, b { CX a, b; }
gate swap a, b { cx a, b; cx b, a; cx a, b; }
