"""Base Site class."""
from typing import ClassVar
from typing import Dict

from mrsimulator.utils.parseable import Parseable
from pydantic import validator

from .isotope import Isotope
from .tensors import AntisymmetricTensor
from .tensors import SymmetricTensor

__author__ = "Deepansh Srivastava"
__email__ = "srivastava.89@osu.edu"


class Site(Parseable):
    """Base class representing a single-site nuclear spin interaction tensor parameters.
    The single-site nuclear spin interaction tensors include the nuclear shielding
    and the electric quadrupolar tensor.

    .. rubric:: Attribute Documentation

    Attributes
    ----------

    isotope: str (optional).
        A string expressed as an atomic number followed by an isotope symbol, eg.,
        `'13C'`, `'17O'`. The default value is `'1H'`.

        Example
        -------

        >>> site = Site(isotope='2H')

    isotropic_chemical_shift: float (optional).
        The isotropic chemical shift of the site in ppm. The default value is 0.

        Example
        -------

        >>> site.isotropic_chemical_shift = 43.3

    shielding_symmetric: :ref:`sy_api` or equivalent dict object (optional).
        The attribute represents the parameters of the irreducible second-rank traceless
        symmetric part of the nuclear shielding tensor. The default value is None.

        The allowed attributes of the :ref:`sy_api` class for `shielding_symmetric` are
        ``zeta``, ``eta``, ``alpha``, ``beta``, and ``gamma``, where ``zeta`` is the
        shielding anisotropy, in ppm, and ``eta`` is the shielding asymmetry parameter
        defined using the Haeberlen convention. The Euler angles ``alpha``, ``beta``,
        and ``gamma`` are in radians.

        Example
        -------

        >>> site.shielding_symmetric = {'zeta': 10, 'eta': 0.5}

        >>> # or equivalently
        >>> site.shielding_symmetric = SymmetricTensor(zeta=10, eta=0.5)

    shielding_antisymmetric: :ref:`asy_api` or equivalent dict object (optional).
        The attribute represents the parameters of the irreducible first-rank
        antisymmetric part of the nuclear shielding tensor. The default value is None.

        The allowed attributes of the :ref:`asy_api` class for
        `shielding_antisymmetric` are ``zeta``, ``alpha``, and ``beta``, where ``zeta``
        is the anisotropy parameter, in ppm, of the anti-symmetric first-rank tensor.
        The angles ``alpha`` and ``beta`` are in radians.

        Example
        -------

        >>> site.shielding_antisymmetric = {'zeta': 20}

        >>> # or equivalently
        >>> site.shielding_antisymmetric = AntisymmetricTensor(zeta=20)

    quadrupolar: :ref:`sy_api` or equivalent dict object (optional).
        The attribute represents the parameters of the traceless irreducible second-rank
        symmetric part of the electric-field gradient tensor. The default value is None.

        The allowed attributes of the :ref:`sy_api` class for `quadrupolar` are ``Cq``,
        ``eta``, ``alpha``, ``beta``, and ``gamma``, where ``Cq`` is the quadrupolar
        coupling constant, in Hz, and ``eta`` is the quadrupolar asymmetry parameter.
        The Euler angles ``alpha``, ``beta``, and ``gamma`` are in radians.

        Example
        -------

        >>> site.quadrupolar = {'Cq': 3.2e6, 'eta': 0.52}

        >>> # or equivalently
        >>> site.quadrupolar = SymmetricTensor(Cq=3.2e6, eta=0.52)

    name: str (optional).
        The name or id of the site. The default value is None.

        Example
        -------

        >>> site.name = '2H-0'
        >>> site.name
        '2H-0'

    label: str (optional).
        The label for the site. The default value is None.

        Example
        -------

        >>> site.label = 'Quad site'
        >>> site.label
        'Quad site'

    description: str (optional).
        A description of the site. The default value is None.

        Example
        -------

        >>> site.description = 'An example Quadrupolar site.'
        >>> site.description
        'An example Quadrupolar site.'

    Example
    -------

    The following are a few examples of the site object.

    >>> site1 = Site(
    ...     isotope='33S',
    ...     isotropic_chemical_shift=20, # in ppm
    ...     shielding_symmetric={
    ...         "zeta": 10, # in ppm
    ...         "eta": 0.5
    ...     },
    ...     quadrupolar={
    ...         "Cq": 5.1e6, # in Hz
    ...         "eta": 0.5
    ...     }
    ... )

    Using SymmetricTensor objects.

    >>> site1 = Site(
    ...     isotope='13C',
    ...     isotropic_chemical_shift=20, # in ppm
    ...     shielding_symmetric=SymmetricTensor(zeta=10, eta=0.5),
    ... )
    """

    isotope: str = "1H"
    isotropic_chemical_shift: float = 0.0
    shielding_symmetric: SymmetricTensor = None
    shielding_antisymmetric: AntisymmetricTensor = None
    quadrupolar: SymmetricTensor = None

    property_unit_types: ClassVar[Dict] = {"isotropic_chemical_shift": "dimensionless"}
    property_default_units: ClassVar[Dict] = {"isotropic_chemical_shift": "ppm"}
    property_units: Dict = {"isotropic_chemical_shift": "ppm"}

    class Config:
        extra = "forbid"
        validate_assignment = True

    @validator("quadrupolar")
    def spin_must_be_at_least_one(cls, v, values):
        if v is None:
            return v
        property_values = (
            set(v.values())
            if isinstance(v, dict)
            else {getattr(v, prop) for prop in v.property_units}
        )
        if property_values == {None}:  # All values of symmetric tensor are None
            return None
        isotope = values["isotope"]
        isotope = Isotope(**isotope) if isinstance(isotope, dict) else isotope
        spin_I = isotope.spin
        if spin_I < 1:
            message = (
                f"with spin quantum number {spin_I} does not allow quadrupolar tensor."
            )
            raise ValueError(f"{isotope} {message}")
        _ = [
            v.property_units.pop(item) if item in v.property_units else None
            for item in ["D", "zeta"]
        ]
        return v

    @validator("shielding_symmetric", "shielding_antisymmetric")
    def shielding_symmetric_must_not_contain_Cq_and_D(cls, v, values):
        if v is None:
            return v
        _ = [
            v.property_units.pop(item) if item in v.property_units else None
            for item in ["Cq", "D"]
        ]
        return v

    @validator("isotope", always=True)
    def validate_isotope(cls, v, *, values, **kwargs):
        return Isotope(symbol=v)

    @classmethod
    def parse_dict_with_units(cls, py_dict: dict):
        """Parse the physical quantity from a dictionary representation of the Site
        object, where the physical quantity is expressed as a string with a number and
        a unit.

        Args:
            dict py_dict: A required python dict object.

        Returns:
            :ref:`site_api` object.

        Example
        -------

        >>> site_dict = {
        ...    "isotope": "13C",
        ...    "isotropic_chemical_shift": "20 ppm",
        ...    "shielding_symmetric": {"zeta": "10 ppm", "eta":0.5}
        ... }
        >>> site1 = Site.parse_dict_with_units(site_dict)
        """
        prop_mapping = {
            "shielding_symmetric": SymmetricTensor,
            "shielding_antisymmetric": AntisymmetricTensor,
            "quadrupolar": SymmetricTensor,
        }

        for k, v in prop_mapping.items():
            if k in py_dict:
                py_dict[k] = v.parse_dict_with_units(py_dict[k])

        return super().parse_dict_with_units(py_dict)

    def rotate(self, euler_angles: list) -> None:
        """Rotate the site tensors (shielding, quadrupolar) by the given list of Euler
        angle rotations. Euler angles are given as a list of (alpha, beta, gamma)
        tuples, and rotations happen in the Haeberlen (ZYZ) convention.

        Arguments:
            (list) euler_angles: An ordered list of angle tuples (alpha, beta, gamma)
                to rotate through each tensor through.

        Example
        -------

        >>> site = Site(isotope="13C", shielding_symmetric={"zeta": 5, "eta": 0.2})
        >>> angles = [(3.1415, 0, -3.1415), (1.5701, 1.5701, 1.5701)]
        >>> site.rotate(angles)
        """
        if self.shielding_symmetric:  # not None
            self.shielding_symmetric.rotate(euler_angles)

        if self.quadrupolar:  # not None
            self.quadrupolar.rotate(euler_angles)

    # Deprecated
    # def to_freq_dict(self, B0):
    #     """
    #     Serialize the Site object to a JSON compliant python dictionary object, where
    #     the attribute value is a number expressed in the attribute's default unit.
    #     The default unit for the attributes with respective dimensionalities is:

    #     - frequency: ``Hz``
    #     - angle: ``rad``

    #     Args:
    #         float B0: A required macroscopic magnetic flux density in units of T.

    #     Return:
    #         Python dict object.

    #     Example
    #     -------

    #     >>> pprint(site1.to_freq_dict(B0=9.4))
    #     {'description': None,
    #      'isotope': '13C',
    #      'isotropic_chemical_shift': -2013.1791999999998,
    #      'label': None,
    #      'name': None,
    #      'quadrupolar': None,
    #      'shielding_antisymmetric': None,
    #      'shielding_symmetric': {'alpha': None,
    #                              'beta': None,
    #                              'eta': 0.5,
    #                              'gamma': None,
    #                              'zeta': -1006.5895999999999}}
    #     """
    #     temp_dict = self.dict(exclude={"isotope"})
    #     temp_dict["isotope"] = self.isotope.symbol
    #     larmor_frequency = -self.isotope.gyromagnetic_ratio * B0  # in MHz
    #     for k in ["shielding_symmetric", "shielding_antisymmetric", "quadrupolar"]:
    #         if getattr(self, k):
    #             temp_dict[k] = getattr(self, k).to_freq_dict(larmor_frequency)
    #             if k == "shielding_symmetric":
    #                 temp_dict[k].pop("Cq")

    #     temp_dict["isotropic_chemical_shift"] *= larmor_frequency
    #     temp_dict.pop("property_units")
    #     return temp_dict
