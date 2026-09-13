from .base import PaysellMethod
from .cancel_invoice import CancelInvoice
from .create_invoice import CreateInvoice
from .get_invoice import ReadInvoice
from .get_public_invoice import ReadPublicInvoice


class Methods(CreateInvoice, ReadInvoice, CancelInvoice, ReadPublicInvoice):
    """All Paysell API methods, bound to :class:`aiopaysell.Paysell`."""


__all__ = ("Methods", "PaysellMethod")
