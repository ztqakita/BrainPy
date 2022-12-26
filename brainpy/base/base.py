# -*- coding: utf-8 -*-

import logging
import os.path
import warnings
from collections import namedtuple
from typing import Dict, Any, Tuple

from brainpy import errors
from brainpy.base import io, naming
from brainpy.base.collector import Collector, ArrayCollector

math = None
StateLoadResult = namedtuple('StateLoadResult', ['missing_keys', 'unexpected_keys'])

__all__ = [
  'BrainPyObject',
  'Base',
]

logger = logging.getLogger('brainpy.base')


class BrainPyObject(object):
  """The BrainPyObject class for whole BrainPy ecosystem.

  The subclass of BrainPyObject includes:

  - ``DynamicalSystem`` in *brainpy.dyn.base.py*
  - ``Integrator`` in *brainpy.integrators.base.py*
  - ``FunAsObject`` in *brainpy.base.function.py*
  - ``Optimizer`` in *brainpy.optimizers.py*
  - ``Scheduler`` in *brainpy.optimizers.py*
  - and others.
  """

  _excluded_vars = ()

  def __init__(self, name=None):
    # check whether the object has a unique name.
    self._name = None
    self._name = self.unique_name(name=name)
    naming.check_name_uniqueness(name=self._name, obj=self)

    # Used to wrap the implicit variables
    # which cannot be accessed by self.xxx
    self.implicit_vars = ArrayCollector()

    # Used to wrap the implicit children nodes
    # which cannot be accessed by self.xxx
    self.implicit_nodes = Collector()

  @property
  def name(self):
    """Name of the model."""
    return self._name

  @name.setter
  def name(self, name: str = None):
    self._name = self.unique_name(name=name)
    naming.check_name_uniqueness(name=self._name, obj=self)

  def register_implicit_vars(self, *variables, **named_variables):
    global math
    if math is None: from brainpy import math

    for variable in variables:
      if isinstance(variable, math.Variable):
        self.implicit_vars[f'var{id(variable)}'] = variable
      elif isinstance(variable, (tuple, list)):
        for v in variable:
          if not isinstance(v, math.Variable):
            raise ValueError(f'Must be instance of {math.Variable.__name__}, but we got {type(v)}')
          self.implicit_vars[f'var{id(v)}'] = v
      elif isinstance(variable, dict):
        for k, v in variable.items():
          if not isinstance(v, math.Variable):
            raise ValueError(f'Must be instance of {math.Variable.__name__}, but we got {type(v)}')
          self.implicit_vars[k] = v
      else:
        raise ValueError(f'Unknown type: {type(variable)}')
    for key, variable in named_variables.items():
      if not isinstance(variable, math.Variable):
        raise ValueError(f'Must be instance of {math.Variable.__name__}, but we got {type(variable)}')
      self.implicit_vars[key] = variable

  def register_implicit_nodes(self, *nodes, node_cls: type = None, **named_nodes):
    if node_cls is None:
      node_cls = BrainPyObject
    for node in nodes:
      if isinstance(node, node_cls):
        self.implicit_nodes[node.name] = node
      elif isinstance(node, (tuple, list)):
        for n in node:
          if not isinstance(n, node_cls):
            raise ValueError(f'Must be instance of {node_cls.__name__}, but we got {type(n)}')
          self.implicit_nodes[n.name] = n
      elif isinstance(node, dict):
        for k, n in node.items():
          if not isinstance(n, node_cls):
            raise ValueError(f'Must be instance of {node_cls.__name__}, but we got {type(n)}')
          self.implicit_nodes[k] = n
      else:
        raise ValueError(f'Unknown type: {type(node)}')
    for key, node in named_nodes.items():
      if not isinstance(node, node_cls):
        raise ValueError(f'Must be instance of {node_cls.__name__}, but we got {type(node)}')
      self.implicit_nodes[key] = node

  def vars(self,
           method: str = 'absolute',
           level: int = -1,
           include_self: bool = True,
           exclude_types: Tuple[type, ...] = None):
    """Collect all variables in this node and the children nodes.

    Parameters
    ----------
    method : str
      The method to access the variables.
    level: int
      The hierarchy level to find variables.
    include_self: bool
      Whether include the variables in the self.
    exclude_types: tuple of type
      The type to exclude.

    Returns
    -------
    gather : ArrayCollector
      The collection contained (the path, the variable).
    """
    global math
    if math is None: from brainpy import math

    if exclude_types is None:
      exclude_types = (math.VariableView, )
    nodes = self.nodes(method=method, level=level, include_self=include_self)
    gather = ArrayCollector()
    for node_path, node in nodes.items():
      for k in dir(node):
        v = getattr(node, k)
        include = False
        if isinstance(v, math.Variable):
          include = True
          if len(exclude_types) and isinstance(v, exclude_types):
              include = False
        if include:
          if k not in node._excluded_vars:
            gather[f'{node_path}.{k}' if node_path else k] = v
      gather.update({f'{node_path}.{k}': v for k, v in node.implicit_vars.items()})
    return gather

  def train_vars(self, method='absolute', level=-1, include_self=True):
    """The shortcut for retrieving all trainable variables.

    Parameters
    ----------
    method : str
      The method to access the variables. Support 'absolute' and 'relative'.
    level: int
      The hierarchy level to find TrainVar instances.
    include_self: bool
      Whether include the TrainVar instances in the self.

    Returns
    -------
    gather : ArrayCollector
      The collection contained (the path, the trainable variable).
    """
    global math
    if math is None: from brainpy import math
    return self.vars(method=method, level=level, include_self=include_self).subset(math.TrainVar)

  def _find_nodes(self, method='absolute', level=-1, include_self=True, _lid=0, _paths=None):
    if _paths is None:
      _paths = set()
    gather = Collector()
    if include_self:
      if method == 'absolute':
        gather[self.name] = self
      elif method == 'relative':
        gather[''] = self
      else:
        raise ValueError(f'No support for the method of "{method}".')
    if (level > -1) and (_lid >= level):
      return gather
    if method == 'absolute':
      nodes = []
      for k, v in self.__dict__.items():
        if isinstance(v, BrainPyObject):
          path = (id(self), id(v))
          if path not in _paths:
            _paths.add(path)
            gather[v.name] = v
            nodes.append(v)
      for node in self.implicit_nodes.values():
        path = (id(self), id(node))
        if path not in _paths:
          _paths.add(path)
          gather[node.name] = node
          nodes.append(node)
      for v in nodes:
        gather.update(v._find_nodes(method=method,
                                    level=level,
                                    _lid=_lid + 1,
                                    _paths=_paths,
                                    include_self=include_self))

    elif method == 'relative':
      nodes = []
      for k, v in self.__dict__.items():
        if isinstance(v, BrainPyObject):
          path = (id(self), id(v))
          if path not in _paths:
            _paths.add(path)
            gather[k] = v
            nodes.append((k, v))
      for key, node in self.implicit_nodes.items():
        path = (id(self), id(node))
        if path not in _paths:
          _paths.add(path)
          gather[key] = node
          nodes.append((key, node))
      for k1, v1 in nodes:
        for k2, v2 in v1._find_nodes(method=method,
                                     _paths=_paths,
                                     _lid=_lid + 1,
                                     level=level,
                                     include_self=include_self).items():
          if k2: gather[f'{k1}.{k2}'] = v2

    else:
      raise ValueError(f'No support for the method of "{method}".')
    return gather

  def nodes(self, method='absolute', level=-1, include_self=True):
    """Collect all children nodes.

    Parameters
    ----------
    method : str
      The method to access the nodes.
    level: int
      The hierarchy level to find nodes.
    include_self: bool
      Whether include the self.

    Returns
    -------
    gather : Collector
      The collection contained (the path, the node).
    """
    return self._find_nodes(method=method, level=level, include_self=include_self)

  def unique_name(self, name=None, type_=None):
    """Get the unique name for this object.

    Parameters
    ----------
    name : str, optional
      The expected name. If None, the default unique name will be returned.
      Otherwise, the provided name will be checked to guarantee its uniqueness.
    type_ : str, optional
      The name of this class, used for object naming.

    Returns
    -------
    name : str
      The unique name for this object.
    """
    if name is None:
      if type_ is None:
        return naming.get_unique_name(type_=self.__class__.__name__)
      else:
        return naming.get_unique_name(type_=type_)
    else:
      naming.check_name_uniqueness(name=name, obj=self)
      return name

  def load_states(self, filename, verbose=False):
    """Load the model states.

    Parameters
    ----------
    filename : str
      The filename which stores the model states.
    verbose: bool
      Whether report the load progress.
    """
    if not os.path.exists(filename):
      raise errors.BrainPyError(f'Cannot find the file path: {filename}')
    elif filename.endswith('.hdf5') or filename.endswith('.h5'):
      io.load_by_h5(filename, target=self, verbose=verbose)
    elif filename.endswith('.pkl'):
      io.load_by_pkl(filename, target=self, verbose=verbose)
    elif filename.endswith('.npz'):
      io.load_by_npz(filename, target=self, verbose=verbose)
    elif filename.endswith('.mat'):
      io.load_by_mat(filename, target=self, verbose=verbose)
    else:
      raise errors.BrainPyError(f'Unknown file format: {filename}. We only supports {io.SUPPORTED_FORMATS}')

  def save_states(self, filename, variables=None, **setting):
    """Save the model states.

    Parameters
    ----------
    filename : str
      The file name which to store the model states.
    variables: optional, dict, ArrayCollector
      The variables to save. If not provided, all variables retrieved by ``~.vars()`` will be used.
    """
    if variables is None:
      variables = self.vars(method='absolute', level=-1)

    if filename.endswith('.hdf5') or filename.endswith('.h5'):
      io.save_as_h5(filename, variables=variables)
    elif filename.endswith('.pkl') or filename.endswith('.pickle'):
      io.save_as_pkl(filename, variables=variables)
    elif filename.endswith('.npz'):
      io.save_as_npz(filename, variables=variables, **setting)
    elif filename.endswith('.mat'):
      io.save_as_mat(filename, variables=variables)
    else:
      raise errors.BrainPyError(f'Unknown file format: {filename}. We only supports {io.SUPPORTED_FORMATS}')

  def state_dict(self):
    """Returns a dictionary containing a whole state of the module.

    Returns
    -------
    out: dict
      A dictionary containing a whole state of the module.
    """
    return self.vars().unique().dict()

  def load_state_dict(self, state_dict: Dict[str, Any], warn: bool = True):
    """Copy parameters and buffers from :attr:`state_dict` into
    this module and its descendants.

    Parameters
    ----------
    state_dict: dict
      A dict containing parameters and persistent buffers.
    warn: bool
      Warnings when there are missing keys or unexpected keys in the external ``state_dict``.

    Returns
    -------
    out: StateLoadResult
      ``NamedTuple`` with ``missing_keys`` and ``unexpected_keys`` fields:

      * **missing_keys** is a list of str containing the missing keys
      * **unexpected_keys** is a list of str containing the unexpected keys
    """
    variables = self.vars().unique()
    keys1 = set(state_dict.keys())
    keys2 = set(variables.keys())
    unexpected_keys = list(keys1 - keys2)
    missing_keys = list(keys2 - keys1)
    for key in keys2.intersection(keys1):
      variables[key].value = state_dict[key]
    if warn:
      if len(unexpected_keys):
        warnings.warn(f'Unexpected keys in state_dict: {unexpected_keys}', UserWarning)
      if len(missing_keys):
        warnings.warn(f'Missing keys in state_dict: {missing_keys}', UserWarning)
    return StateLoadResult(missing_keys, unexpected_keys)

  # def to(self, devices):
  #   global math
  #   if math is None: from brainpy import math
  #
  # def cpu(self):
  #   global math
  #   if math is None: from brainpy import math
  #
  #   all_vars = self.vars().unique()
  #   for data in all_vars.values():
  #     data[:] = math.asarray(data.value)
  #
  # def cuda(self):
  #   global math
  #   if math is None: from brainpy import math
  #
  # def tpu(self):
  #   global math
  #   if math is None: from brainpy import math


Base = BrainPyObject
