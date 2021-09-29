# -*- coding: utf-8 -*-

import copy
from contextlib import contextmanager
from brainpy import errors

math = None


__all__ = [
  'DictPlus',
  'Collector',
  'ArrayCollector',
]


class DictPlus(dict):
  """Python dictionaries with tutorials_advanced dot notation access.

  For example:

  >>> d = DictPlus({'a': 10, 'b': 20})
  >>> d.a
  10
  >>> d['a']
  10
  >>> d.c  # this will raise a KeyError
  KeyError: 'c'
  >>> d.c = 30  # but you can assign a value to a non-existing item
  >>> d.c
  30
  """

  def __init__(self, *args, **kwargs):
    object.__setattr__(self, '__parent', kwargs.pop('__parent', None))
    object.__setattr__(self, '__key', kwargs.pop('__key', None))
    for arg in args:
      if not arg:
        continue
      elif isinstance(arg, dict):
        for key, val in arg.items():
          self[key] = self._hook(val)
      elif isinstance(arg, tuple) and (not isinstance(arg[0], tuple)):
        self[arg[0]] = self._hook(arg[1])
      else:
        for key, val in iter(arg):
          self[key] = self._hook(val)

    for key, val in kwargs.items():
      self[key] = self._hook(val)

  def __setattr__(self, name, value):
    if hasattr(self.__class__, name):
      raise AttributeError(f"Attribute '{name}' is read-only in '{type(self)}' object.")
    else:
      self[name] = value

  def __setitem__(self, name, value):
    super(DictPlus, self).__setitem__(name, value)
    try:
      p = object.__getattribute__(self, '__parent')
      key = object.__getattribute__(self, '__key')
    except AttributeError:
      p = None
      key = None
    if p is not None:
      p[key] = self
      object.__delattr__(self, '__parent')
      object.__delattr__(self, '__key')

  def __add__(self, other):
    if not self.keys():
      return other
    else:
      self_type = type(self).__name__
      other_type = type(other).__name__
      msg = "Unsupported operand type(s) for +: '{}' and '{}'"
      raise TypeError(msg.format(self_type, other_type))

  @classmethod
  def _hook(cls, item):
    if isinstance(item, dict):
      return cls(item)
    elif isinstance(item, (list, tuple)):
      return type(item)(cls._hook(elem) for elem in item)
    return item

  def __getattr__(self, item):
    return self.__getitem__(item)

  def __delattr__(self, name):
    del self[name]

  def copy(self):
    return copy.copy(self)

  def deepcopy(self):
    return copy.deepcopy(self)

  def __deepcopy__(self, memo):
    other = self.__class__()
    memo[id(self)] = other
    for key, value in self.items():
      other[copy.deepcopy(key, memo)] = copy.deepcopy(value, memo)
    return other

  def to_dict(self):
    base = {}
    for key, value in self.items():
      if isinstance(value, type(self)):
        base[key] = value.to_dict()
      elif isinstance(value, (list, tuple)):
        base[key] = type(value)(item.to_dict() if isinstance(item, type(self)) else item
                                for item in value)
      else:
        base[key] = value
    return base

  def update(self, *args, **kwargs):
    other = {}
    if args:
      if len(args) > 1:
        raise TypeError()
      other.update(args[0])
    other.update(kwargs)
    for k, v in other.items():
      if (k not in self) or (not isinstance(self[k], dict)) or (not isinstance(v, dict)):
        self[k] = v
      else:
        self[k].update(v)

  def __getnewargs__(self):
    return tuple(self.items())

  def __getstate__(self):
    return self

  def __setstate__(self, state):
    self.update(state)

  def setdefault(self, key, default=None):
    if key in self:
      return self[key]
    else:
      self[key] = default
      return default


class Collector(dict):
  """A Collector is a dictionary (name, var) with some additional methods to make manipulation
  of collections of variables easy. A Collector is ordered by insertion order. It is the object
  returned by Base.vars() and used as input in many Collector instance: optimizers, jit, etc..."""

  def __setitem__(self, key, value):
    """Overload bracket assignment to catch potential conflicts during assignment."""
    if key in self:
      if id(self[key]) != id(value):
        raise ValueError(f'Name "{key}" conflicts: same name for {value} and {self[key]}.')
    dict.__setitem__(self, key, value)

  def replace(self, key, new_value):
    """Replace the original key with the new value."""
    self.pop(key)
    self[key] = new_value
    # dict.__setitem__(self, key, new_value)

  def update(self, other, **kwargs):
    assert isinstance(other, dict)
    for key, value in other.items():
      self[key] = value
    for key, value in kwargs.items():
      self[key] = value

  def __add__(self, other):
    gather = type(self)(self)
    gather.update(other)
    return gather

  def subset(self, var_type, judge_func=None):
    """Get the subset of the (key, value) pair.

    ``subset()`` can be used to get a subset of some class:

    >>> import brainpy as bp
    >>>
    >>> # get all trainable variables
    >>> some_collector.subset(bp.math.TrainVar)
    >>>
    >>> # get all JaxArray
    >>> some_collector.subset(bp.math.Variable)

    or, it can be used to get a subset of integrators:

    >>> # get all ODE integrators
    >>> some_collector.subset(bp.integrators.ODE_INT)

    Parameters
    ----------
    var_type : Any
      The type/class to match.
    judge_func : optional, callable
    """
    global math
    if math is None:
      from brainpy import math

    gather = type(self)()
    if type(var_type) == type:
      judge_func = (lambda v: isinstance(v, var_type)) if judge_func is None else judge_func
      for key, value in self.items():
        if judge_func(value):
          gather[key] = value
    elif isinstance(var_type, str):
      judge_func = (lambda v: v.__name__.startswith(var_type)) if judge_func is None else judge_func
      for key, value in self.items():
        if judge_func(value):
          gather[key] = value
    elif isinstance(var_type, math.Variable):
      judge_func = (lambda v: var_type.issametype(v)) if judge_func is None else judge_func
      for key, value in self.items():
        if judge_func(value):
          gather[key] = value
    else:
      raise errors.UnsupportedError(f'BrainPy do not support to subset {type(var_type)}. '
                                    f'You should provide a class name, or a str.')
    return gather

  def unique(self):
    """Get a new type of collector with unique values.

    If one value is assigned to two or more keys,
    then only one pair of (key, value) will be returned.
    """
    gather = type(self)()
    seen = set()
    for k, v in self.items():
      if id(v) not in seen:
        seen.add(id(v))
        gather[k] = v
    return gather

  def dict(self):
    """Get a dict with the key and the value data.
    """
    gather = dict()
    for k, v in self.items():
      gather[k] = v.value
    return gather


class ArrayCollector(Collector):
  """A ArrayCollector is a dictionary (name, var)
  with some additional methods to make manipulation
  of collections of variables easy. A Collection
  is ordered by insertion order. It is the object
  returned by DynamicalSystem.vars() and used as input
  in many DynamicalSystem instance: optimizers, Jit, etc..."""

  def __setitem__(self, key, value):
    """Overload bracket assignment to catch potential conflicts during assignment."""
    global math
    if math is None:
      from brainpy import math

    assert isinstance(value, math.ndarray)
    if key in self:
      if id(self[key]) != id(value):
        raise ValueError(f'Name "{key}" conflicts: same name for {value} and {self[key]}.')
    dict.__setitem__(self, key, value)

  def assign(self, inputs):
    """Assign data to all values.

    Parameters
    ----------
    inputs : dict
      The data for each value in this collector.
    """
    if len(self) != len(inputs):
      raise ValueError(f'The target has {len(inputs)} data, while we got '
                       f'an input value with the length of {len(inputs)}.')
    for key, v in self.items():
      v.value = inputs[key]

  def data(self):
    """Get all data in each value."""
    return [x.value for x in self.values()]

  @contextmanager
  def replicate(self):
    """A context manager to use in a with statement that replicates
    the variables in this collection to multiple devices.

    Important: replicating also updates the random state in order
    to have a new one per device.
    """
    global math
    if math is None:
      from brainpy import math

    try:
      import jax
      import jax.numpy as jnp
    except ModuleNotFoundError as e:
      raise ModuleNotFoundError('"ArrayCollector.replicate()" is only available in '
                                'JAX backend, while JAX is not installed.') from e

    replicated, saved_states = {}, {}
    x = jnp.zeros((jax.local_device_count(), 1), dtype=math.float_)
    sharded_x = jax.pmap(lambda x: x, axis_name='device')(x)
    devices = [b.device() for b in sharded_x.device_buffers]
    num_device = len(devices)
    for k, d in self.items():
      if isinstance(d, math.random.RandomState):
        replicated[k] = jax.api.device_put_sharded([shard for shard in d.split(num_device)], devices)
        saved_states[k] = d.value
      else:
        replicated[k] = jax.api.device_put_replicated(d.value, devices)
    self.assign(replicated)
    yield
    visited = set()
    for k, d in self.items():
      # Careful not to reduce twice in case of
      # a variable and a reference to it.
      if id(d) not in visited:
        if isinstance(d, math.random.RandomState):
          d.value = saved_states[k]
        else:
          d.value = reduce_func(d)
        visited.add(id(d))
