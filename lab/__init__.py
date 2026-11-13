"""lab - RESEARCH AND THE LADDER. It judges strategies using the core's own code.

Owns: nothing itself. The modules beside it own one thing each, named in manifest.toml.
Does NOT own: any trading decision, order or position - those are desk/.

It may import desk/, and must, because a verdict reached by a second implementation of
the strategy is a verdict about that second implementation. The first desk's simulator
ran different code from the desk it was certifying.
"""
