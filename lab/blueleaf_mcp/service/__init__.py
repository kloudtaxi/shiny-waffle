"""The BlueLeaf lab MCP server's service layer: plain Python, shared by both servers.

Nothing in this package reads the answer key, the truth or the frozen run instruments (the
BlueLeaf MCP spec, §2.1). The lab's decision code is reached only through `service._lab`.
"""
