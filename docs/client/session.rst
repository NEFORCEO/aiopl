=======
Session
=======

**aiopaysell** uses `aiohttp <https://docs.aiohttp.org/en/stable/index.html>`_ as its
session by default. Implement your own by inheriting
:class:`BaseSession <aiopaysell.client.session.BaseSession>` and overriding
:meth:`request <aiopaysell.client.session.BaseSession.request>`.

.. automodule:: aiopaysell.client.session
    :show-inheritance:
    :members:
