
![Logo](docs/_static/logo.png)

[![LICENSE](https://anaconda.org/brainpy/brainpy/badges/license.svg)](https://github.com/PKU-NIP-Lab/BrainPy)    [![Documentation](https://readthedocs.org/projects/brainpy/badge/?version=latest)](https://brainpy.readthedocs.io/en/latest/?badge=latest)   [![PyPI version](https://badge.fury.io/py/brain-py.svg)](https://badge.fury.io/py/brain-py)   [![Build Status](https://travis-ci.com/PKU-NIP-Lab/BrainPy.svg?branch=master)](https://travis-ci.com/PKU-NIP-Lab/BrainPy)



# Why to use BrainPy

``BrainPy`` is an integrative framework for computational neuroscience and brain-inspired computation based on Just-In-Time (JIT) compilation (built on the top of [JAX](https://github.com/google/jax) and [Numba](https://github.com/numba/)). Core functions provided in BrainPy includes

- **JIT compilation** for functions and class objects. 
- **Numerical solvers** for ODEs, SDEs, and others. 
- **Dynamics simulation tools** for various brain objects, like neurons, synapses, networks, soma, dendrites, channels, and even more. 
- **Dynamics analysis tools** for differential equations, including phase plane analysis and bifurcation analysis, and linearization analysis.
- **Seamless integration with deep learning models**, and has the speed benefit on JIT compilation.
- And more ......

`BrainPy` is designed to effectively satisfy your basic requirements: 

- **Easy to learn and use**: BrainPy is only based on Python language and has little dependency requirements. 
- **Flexible and transparent**: BrainPy endows the users with the fully data/logic flow control. Users can code any logic they want with BrainPy. 
- **Extensible**: BrainPy allow users to extend new functionality just based on Python coding. For example, we extend the same code with the ability to do numerical analysis (whatever low- or high-dimensional system). 
- **Efficient**: All codes in BrainPy can be just-in-time compiled (based on [JAX](https://github.com/google/jax) and [Numba](https://github.com/numba/)) to run on CPU, GPU or TPU devices, thus guaranteeing its running efficiency. 



# How to use BrainPy

## Step 1: installation

``BrainPy`` is based on Python (>=3.6), and the following packages are required to be installed to use ``BrainPy``:

- NumPy >= 1.15
- Matplotlib >= 3.4

*The installation details please see documentation: [Quickstart/Installation](https://brainpy.readthedocs.io/en/latest/quickstart/installation.html)*



**Method 1**: install ``BrainPy`` by using ``pip``:

To install the stable release of BrainPy, please use

```bash
> pip install -U brain-py
```

**Method 2**: install ``BrainPy`` from source:

```bash
> pip install git+https://github.com/PKU-NIP-Lab/BrainPy
>
> # or
>
> git clone https://github.com/PKU-NIP-Lab/BrainPy
> cd BrainPy
> python setup.py install
```



**Other dependencies**: you want to get the full supports by BrainPy, please install the following packages:

- `JAX >= 0.2.10`,  needed for "jax" backend and many other supports ([how to install jax?](https://brainpy.readthedocs.io/en/latest/quickstart/installation.html#jax))
- `Numba >= 0.52`,  needed for JIT compilation on "numpy" backend ([how to install numba?](https://brainpy.readthedocs.io/en/latest/quickstart/installation.html#numba))
- `SymPy >= 1.4`, needed for dynamics "analysis" module and Exponential Euler method ([how to install sympy?](https://brainpy.readthedocs.io/en/latest/quickstart/installation.html#sympy))



## Step 2: useful links

- **Documentation:** https://brainpy.readthedocs.io/
- **Bug reports:** https://github.com/PKU-NIP-Lab/BrainPy/issues
- **Examples from papers**: https://brainpy-examples.readthedocs.io/en/latest/
- **Canonical brain models**: https://brainmodels.readthedocs.io/en/latest/



## Step 3: inspirational examples

Here list several examples of BrainPy. More detailed examples and tutorials please see [**BrainModels**](https://brainmodels.readthedocs.io) or [**BrainPy-Examples**](https://brainpy-examples.readthedocs.io/en/latest/). 



### Neuron models

- [Leaky integrate-and-fire neuron model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.neurons.LIF.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/neurons/LIF.py)
- [Exponential integrate-and-fire neuron model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.neurons.ExpIF.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/neurons/ExpIF.py)
- [Quadratic integrate-and-fire neuron model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.neurons.QuaIF.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/neurons/QuaIF.py)
- [Adaptive Quadratic integrate-and-fire model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.neurons.AdQuaIF.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/neurons/AdQuaIF.py)
- [Adaptive Exponential integrate-and-fire model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.neurons.AdExIF.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/neurons/AdExIF.py)
- [Generalized integrate-and-fire model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.neurons.GIF.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/neurons/GIF.py)
- [Hodgkin–Huxley neuron model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.neurons.HH.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/neurons/HH.py)
- [Izhikevich neuron model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.neurons.Izhikevich.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/neurons/Izhikevich.py)
- [Morris-Lecar neuron model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.neurons.MorrisLecar.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/neurons/MorrisLecar.py)
- [Hindmarsh-Rose bursting neuron model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.neurons.HindmarshRose.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/neurons/HindmarshRose.py)

See [brainmodels.neurons](https://brainmodels.readthedocs.io/en/latest/apis/neurons.html) to find more.



### Synapse models

- [Voltage jump synapse model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.synapses.VoltageJump.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/synapses/voltage_jump.py)
- [Exponential synapse model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.synapses.ExpCUBA.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/synapses/exponential.py)
- [Alpha synapse model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.synapses.AlphaCUBA.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/synapses/alpha.py)
- [Dual exponential synapse model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.synapses.DualExpCUBA.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/synapses/dual_exp.py)
- [AMPA synapse model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.synapses.AMPA.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/synapses/AMPA.py)
- [GABAA synapse model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.synapses.GABAa.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/synapses/GABAa.py)
- [NMDA synapse model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.synapses.NMDA.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/synapses/NMDA.py)
- [Short-term plasticity model](https://brainmodels.readthedocs.io/en/latest/apis/generated/brainmodels.synapses.STP.html), [source code](https://github.com/PKU-NIP-Lab/BrainModels/blob/main/brainmodels/synapses/STP.py)

See [brainmodels.synapses](https://brainmodels.readthedocs.io/en/latest/apis/synapses.html) to find more.



### Network models

- **[CANN]** [*(Si Wu, 2008)* Continuous-attractor Neural Network](https://brainpy-examples.readthedocs.io/en/latest/cann/Wu_2008_CANN.html)
- [*(Vreeswijk & Sompolinsky, 1996)* E/I balanced network](https://brainpy-examples.readthedocs.io/en/latest/ei_nets/Vreeswijk_1996_EI_net.html)
- [*(Sherman & Rinzel, 1992)* Gap junction leads to anti-synchronization](https://brainpy-examples.readthedocs.io/en/latest/gj_nets/Sherman_1992_gj_antisynchrony.html)
- [*(Wang & Buzsáki, 1996)* Gamma Oscillation](https://brainpy-examples.readthedocs.io/en/latest/oscillation_synchronization/Wang_1996_gamma_oscillation.html)
- [*(Brunel & Hakim, 1999)* Fast Global Oscillation](https://brainpy-examples.readthedocs.io/en/latest/oscillation_synchronization/Brunel_Hakim_1999_fast_oscillation.html)
- [*(Diesmann, et, al., 1999)* Synfire Chains](https://brainpy-examples.readthedocs.io/en/latest/oscillation_synchronization/Diesmann_1999_synfire_chains.html)
- **[Working Memory]** [*(Mi, et. al., 2017)* STP for Working Memory Capacity](https://brainpy-examples.readthedocs.io/en/latest/working_memory/Mi_2017_working_memory_capacity.html)
- **[Working Memory]** [*(Bouchacourt & Buschman, 2019)* Flexible Working Memory Model](https://brainpy-examples.readthedocs.io/en/latest/working_memory/Bouchacourt_2019_Flexible_working_memory.html)
- **[Decision Making]** [*(Wang, 2002)* Decision making spiking model](https://brainpy-examples.readthedocs.io/en/latest/decision_making/Wang_2002_decision_making_spiking.html)



### Dynamics learning

- [Train Integrator RNN with BP](https://brainpy-examples.readthedocs.io/en/latest/recurrent_networks/integrator_rnn.html)

- [*(Sussillo & Abbott, 2009)* FORCE Learning](https://brainpy-examples.readthedocs.io/en/latest/recurrent_networks/Sussillo_Abbott_2009_FORCE_Learning.html)

- [*(Laje & Buonomano, 2013)* Robust Timing in RNN](https://brainpy-examples.readthedocs.io/en/latest/recurrent_networks/Laje_Buonomano_2013_robust_timing_rnn.html)
- [*(Song, et al., 2016)*: Training excitatory-inhibitory recurrent network](https://brainpy-examples.readthedocs.io/en/latest/recurrent_networks/Song_2016_EI_RNN.html)
- **[Working Memory]** [*(Masse, et al., 2019)*: RNN with STP for Working Memory](https://brainpy-examples.readthedocs.io/en/latest/recurrent_networks/Masse_2019_STP_RNN.html)




### Low-dimension dynamics analysis

- [1D system bifurcation](https://brainmodels.readthedocs.io/en/latest/low_dim_analysis/1D_system_bifurcation.html)
- [Codimension 1 bifurcation analysis of FitzHugh Nagumo model](https://brainpy-examples.readthedocs.io/en/latest/low_dim_analysis/FitzHugh_Nagumo_analysis.html)
- [Codimension 2 bifurcation analysis of FitzHugh Nagumo model](https://brainpy-examples.readthedocs.io/en/latest/low_dim_analysis/FitzHugh_Nagumo_analysis.html#Codimension-2-bifurcation-analysis)
- **[Decision Making Model]** [*(Wong & Wang, 2006)* Decision making rate model](https://brainpy-examples.readthedocs.io/en/latest/decision_making/Wang_2006_decision_making_rate.html)



### High-dimension dynamics analysis

- [*(Yang, 2020)*: Dynamical system analysis for RNN](https://brainpy-examples.readthedocs.io/en/latest/recurrent_networks/Yang_2020_RNN_Analysis.html)

