# -*- coding: utf-8 -*-
"""
Extended Czjzek distribution (Shielding and Quadrupolar)
========================================================

In this example, we illustrate the simulation of spectrum originating from an
extended Czjzek distribution of traceless symmetric tensors. We show two cases, an
extended Czjzek distribution of the shielding and quadrupolar tensor parameters,
respectively.

"""
# %%
# Import the required modules.
import matplotlib as mpl
import matplotlib.pyplot as plt
from mrsimulator import Simulator
from mrsimulator.methods import BlochDecayCentralTransitionSpectrum
from mrsimulator.methods import BlochDecaySpectrum
from mrsimulator.models import extended_czjzek_distribution
from mrsimulator.utils.collection import single_site_system_generator

# pre config the figures
mpl.rcParams["figure.figsize"] = [4.25, 3.0]

# %%
# Symmetric shielding tensor
# --------------------------
#
# Create the extended Czjzek distribution
# '''''''''''''''''''''''''''''''''''''''
#
# First, create a distribution of the zeta and eta parameters of the shielding tensors
# using the extended Czjzek distribution model as follows,
dominant = {"zeta": 60, "eta": 0.3}
zeta_dist, eta_dist = extended_czjzek_distribution(dominant, eps=0.14, n=5000)

# %%
# where `eps` is the perturbation factor, and `n` is the number of tensor parameters
# sampled from the extended Czjzek distribution model. Here, the distribution
# parameters are generated by randomly perturbing the second-rank tensor components
# about the dominant tensor.
#
# The following is the plot of the extended Czjzek distribution.
plt.scatter(zeta_dist, eta_dist, s=2)
plt.xlabel(r"$\zeta$ / ppm")
plt.ylabel(r"$\eta$")
plt.xlim(40, 80)
plt.ylim(0, 1)
plt.tight_layout()
plt.show()

# %%
# Simulate the spectrum
# '''''''''''''''''''''
#
# Create the spin-systems from the above :math:`\zeta` and :math:`\eta` parameters.
systems = single_site_system_generator(
    isotopes="13C", shielding_symmetric={"zeta": zeta_dist, "eta": eta_dist}
)

# %%
# Create a simulator object and add the above system.
sim = Simulator()
sim.spin_systems = systems  # add the systems
sim.methods = [BlochDecaySpectrum(channels=["13C"])]  # add the method
sim.run()

# %%
# The following is the static spectrum arising from a Czjzek distribution of the
# second-rank traceless shielding tensors.
plt.figure(figsize=(4.25, 3.0))
ax = plt.gca(projection="csdm")
ax.plot(sim.methods[0].simulation, color="black")
plt.tight_layout()
plt.show()

# %%
# Quadrupolar tensor
# ------------------
#
# Create the extended Czjzek distribution
# '''''''''''''''''''''''''''''''''''''''
#
# Similarly, you may also create an extended Czjzek distribution of the electric field
# gradient (EFG) tensor parameters.
dominant = {"Cq": 6.1, "eta": 0.1}
Cq_dist, eta_dist = extended_czjzek_distribution(dominant, eps=0.25, n=5000)

# The following is the plot of the extended Czjzek distribution.
plt.scatter(Cq_dist, eta_dist, s=2)
plt.xlabel(r"$C_q$ / MHz")
plt.ylabel(r"$\eta$")
plt.xlim(2, 10)
plt.ylim(0, 1)
plt.tight_layout()
plt.show()

# %%
# Simulate the spectrum
# '''''''''''''''''''''
# **Static spectrum**
# Create the spin systems.
systems = single_site_system_generator(
    isotopes="71Ga", quadrupolar={"Cq": Cq_dist * 1e6, "eta": eta_dist}
)

# %%
# Create a simulator object and add the above system.
sim = Simulator()
sim.spin_systems = systems  # add the systems
sim.methods = [
    BlochDecayCentralTransitionSpectrum(
        channels=["71Ga"],
        magnetic_flux_density=9.4,  # in T
        spectral_dimensions=[{"count": 2048, "spectral_width": 2e5}],
    )
]  # add the method
sim.run()

# %%
# The following is a static spectrum arising from an extended Czjzek distribution of
# the second-rank traceless EFG tensors.
plt.figure(figsize=(4.25, 3.0))
ax = plt.gca(projection="csdm")
ax.plot(sim.methods[0].simulation, color="black")
ax.invert_xaxis()
plt.tight_layout()
plt.show()

# %%
# **MAS spectrum**
sim.methods = [
    BlochDecayCentralTransitionSpectrum(
        channels=["71Ga"],
        magnetic_flux_density=9.4,  # in T
        rotor_frequency=25000,  # in Hz
        spectral_dimensions=[
            {"count": 2048, "spectral_width": 2e5, "reference_offset": -1e4}
        ],
    )
]  # add the method
sim.config.number_of_sidebands = 16
sim.run()

# %%
# The following is the MAS spectrum arising from an extended Czjzek distribution of the
# second-rank traceless EFG tensors.
plt.figure(figsize=(4.25, 3.0))
ax = plt.gca(projection="csdm")
ax.plot(sim.methods[0].simulation, color="black")
ax.invert_xaxis()
plt.tight_layout()
plt.show()
