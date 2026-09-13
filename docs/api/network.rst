=======
Network
=======

:class:`Network <aiopaysell.client.network.Network>` builds the URL for the
Paysell API endpoints.

`Paysell <https://paysell.me/docs>`_ has a single network:

.. autodata:: aiopaysell.MAINNET
    :no-value:

The client always uses it — there's no test network to select.

.. automodule:: aiopaysell.client.network
    :members:
