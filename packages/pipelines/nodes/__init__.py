"""Reusable RocketRide custom nodes.

Each node is a small, testable unit that a pipeline canvas wires together. Node
functions take a typed input dict and return a typed output dict; they perform I/O
only through the shared clients in ``common`` and the sponsor SDK wrappers here.
"""
