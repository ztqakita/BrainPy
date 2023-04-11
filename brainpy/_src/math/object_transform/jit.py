# -*- coding: utf-8 -*-

"""
The JIT compilation tools for JAX backend.

1. Just-In-Time compilation is implemented by the 'jit()' function

"""

from functools import partial, wraps
from typing import Callable, Union, Optional, Sequence, Dict, Any, Iterable

import jax

from brainpy import tools, check
from .naming import get_stack_cache, cache_stack
from ._tools import dynvar_deprecation, node_deprecation, evaluate_dyn_vars, abstract
from .base import BrainPyObject, ObjectTransform
from .variables import Variable, VariableStack

__all__ = [
  'jit',
]


class JITTransform(ObjectTransform):
  """Object-oriented JIT transformation in BrainPy."""

  def __init__(
      self,
      fun: Callable,
      static_argnums: Union[int, Iterable[int], None] = None,
      static_argnames: Union[str, Iterable[str], None] = None,
      donate_argnums: Union[int, Iterable[int]] = (),
      device: Optional[Any] = None,
      inline: bool = False,
      keep_unused: bool = False,
      abstracted_axes: Optional[Any] = None,
      name: Optional[str] = None,
      backend: Optional[str] = None,

      # deprecated
      dyn_vars: Dict[str, Variable] = None,
      child_objs: Dict[str, BrainPyObject] = None,
  ):
    super().__init__(name=name)

    # variables and nodes
    if dyn_vars is not None:
      self.register_implicit_vars(dyn_vars)
    if child_objs is not None:
      self.register_implicit_nodes(child_objs)

    # target
    if hasattr(fun, '__self__') and isinstance(getattr(fun, '__self__'), BrainPyObject):
      self.register_implicit_nodes(getattr(fun, '__self__'))
    self.fun = fun

    # parameters
    self._backend = backend
    self._static_argnums = static_argnums
    self._static_argnames = static_argnames
    self._donate_argnums = donate_argnums
    self._device = device
    self._inline = inline
    self._keep_unused = keep_unused
    self._abstracted_axes = abstracted_axes

    # transformation function
    self._transform = None
    self._dyn_vars = None

  def _transform_function(self, variable_data: Dict, *args, **kwargs):
    for key, v in self._dyn_vars.items():
      v._value = variable_data[key]
    out = self.fun(*args, **kwargs)
    changes = self._dyn_vars.dict_data()
    return out, changes

  def __call__(self, *args, **kwargs):
    if jax.config.jax_disable_jit:
      return self.fun(*args, **kwargs)

    if self._transform is None:
      self._dyn_vars = evaluate_dyn_vars(self.fun, *args, **kwargs)
      self._transform = jax.jit(
        self._transform_function,
        static_argnums=jax.tree_util.tree_map(lambda a: a + 1, self._static_argnums),
        static_argnames=self._static_argnames,
        donate_argnums=self._donate_argnums,
        device=self._device,
        inline=self._inline,
        keep_unused=self._keep_unused,
        abstracted_axes=self._abstracted_axes,
        backend=self._backend,
      )
    out, changes = self._transform(self._dyn_vars.dict_data(), *args, **kwargs)
    for key, v in self._dyn_vars.items():
      v._value = changes[key]
    return out

  def __repr__(self):
    name = self.__class__.__name__
    f = tools.repr_object(self.fun)
    f = tools.repr_context(f, " " * (len(name) + 6))
    format_ref = (f'{name}(target={f}, \n' +
                  f'{" " * len(name)} num_of_vars={len(self.vars().unique())})')
    return format_ref


_jit_par = '''
  func : BrainPyObject, function, callable
    The instance of Base or a function.
  static_argnums: optional, int, sequence of int
    An optional int or collection of ints that specify which
    positional arguments to treat as static (compile-time constant).
    Operations that only depend on static arguments will be constant-folded in
    Python (during tracing), and so the corresponding argument values can be
    any Python object.
  static_argnames : optional, str, list, tuple, dict
    An optional string or collection of strings specifying which named arguments to treat
    as static (compile-time constant). See the comment on ``static_argnums`` for details.
    If not provided but ``static_argnums`` is set, the default is based on calling
    ``inspect.signature(fun)`` to find corresponding named arguments.
  donate_argnums: int, sequence of int
    Specify which positional argument buffers are "donated" to
    the computation. It is safe to donate argument buffers if you no longer
    need them once the computation has finished. In some cases XLA can make
    use of donated buffers to reduce the amount of memory needed to perform a
    computation, for example recycling one of your input buffers to store a
    result. You should not reuse buffers that you donate to a computation, JAX
    will raise an error if you try to. By default, no argument buffers are
    donated. Note that donate_argnums only work for positional arguments, and keyword
    arguments will not be donated.
  device: optional, Any
    This is an experimental feature and the API is likely to change.
    Optional, the Device the jitted function will run on. (Available devices
    can be retrieved via :py:func:`jax.devices`.) The default is inherited
    from XLA's DeviceAssignment logic and is usually to use
    ``jax.devices()[0]``.
  keep_unused: bool
    If `False` (the default), arguments that JAX determines to be
    unused by `fun` *may* be dropped from resulting compiled XLA executables.
    Such arguments will not be transferred to the device nor provided to the
    underlying executable. If `True`, unused arguments will not be pruned.
  backend: optional, str
    This is an experimental feature and the API is likely to change.
    Optional, a string representing the XLA backend: ``'cpu'``, ``'gpu'``, or
    ``'tpu'``.
  inline: bool
    Specify whether this function should be inlined into enclosing
    jaxprs (rather than being represented as an application of the xla_call
    primitive with its own subjaxpr). Default False.
'''


def jit(
    func: Callable = None,

    # original jax.jit parameters
    static_argnums: Union[int, Iterable[int], None] = None,
    static_argnames: Union[str, Iterable[str], None] = None,
    donate_argnums: Union[int, Sequence[int]] = (),
    device: Optional[Any] = None,
    inline: bool = False,
    keep_unused: bool = False,
    backend: Optional[str] = None,
    abstracted_axes: Optional[Any] = None,

    # deprecated
    dyn_vars: Optional[Union[Variable, Sequence[Variable], Dict[str, Variable]]] = None,
    child_objs: Optional[Union[BrainPyObject, Sequence[BrainPyObject], Dict[str, BrainPyObject]]] = None,
) -> JITTransform:
  """
  JIT (Just-In-Time) compilation for BrainPy computation.

  This function has the same ability to just-in-time compile a pure function,
  but it can also JIT compile a :py:class:`brainpy.DynamicalSystem`, or a
  :py:class:`brainpy.BrainPyObject` object.

  Examples
  --------

  You can JIT any object in which all dynamical variables are defined as :py:class:`~.Variable`.  

  >>> class Hello(bp.BrainPyObject):
  >>>   def __init__(self):
  >>>     super(Hello, self).__init__()
  >>>     self.a = bp.math.Variable(bp.math.array(10.))
  >>>     self.b = bp.math.Variable(bp.math.array(2.))
  >>>   def transform(self):
  >>>     self.a *= self.b
  >>>
  >>> test = Hello()
  >>> bp.math.jit(test.transform)

  Further, you can JIT a normal function, just used like in JAX.

  >>> @bp.math.jit
  >>> def selu(x, alpha=1.67, lmbda=1.05):
  >>>   return lmbda * bp.math.where(x > 0, x, alpha * bp.math.exp(x) - alpha)


  Parameters
  ----------
  {jit_par}
  dyn_vars : optional, dict, sequence of Variable, Variable
    These variables will be changed in the function, or needed in the computation.

    .. deprecated:: 2.4.0
       No longer need to provide ``dyn_vars``. This function is capable of automatically
       collecting the dynamical variables used in the target ``func``.
  child_objs: optional, dict, sequence of BrainPyObject, BrainPyObject
    The children objects used in the target function.

    .. versionadded:: 2.3.1

    .. deprecated:: 2.4.0
       No longer need to provide ``child_objs``. This function is capable of automatically
       collecting the children objects used in the target ``func``.

  Returns
  -------
  func : JITTransform
    A callable jitted function, set up for just-in-time compilation.
  """

  dynvar_deprecation(dyn_vars)
  node_deprecation(child_objs)
  if dyn_vars is not None:
    dyn_vars = check.is_all_vars(dyn_vars, out_as='dict')
  if child_objs is not None:
    child_objs = check.is_all_objs(child_objs, out_as='dict')

  if func is None:
    return lambda f: JITTransform(fun=f,
                                  dyn_vars=dyn_vars,
                                  child_objs=child_objs,
                                  static_argnums=static_argnums,
                                  static_argnames=static_argnames,
                                  donate_argnums=donate_argnums,
                                  device=device,
                                  inline=inline,
                                  keep_unused=keep_unused,
                                  backend=backend,
                                  abstracted_axes=abstracted_axes)
  else:
    return JITTransform(fun=func,
                        dyn_vars=dyn_vars,
                        child_objs=child_objs,
                        static_argnums=static_argnums,
                        static_argnames=static_argnames,
                        donate_argnums=donate_argnums,
                        device=device,
                        inline=inline,
                        keep_unused=keep_unused,
                        backend=backend,
                        abstracted_axes=abstracted_axes)


jit.__doc__ = jit.__doc__.format(jit_par=_jit_par.strip())


def cls_jit(
    func: Callable = None,
    static_argnums: Union[int, Iterable[int], None] = None,
    static_argnames: Union[str, Iterable[str], None] = None,
    device: Optional[Any] = None,
    inline: bool = False,
    keep_unused: bool = False,
    abstracted_axes: Optional[Any] = None,
) -> Callable:
  """Just-in-time compile a function and then the jitted function as a bound method for a class. 
  
  Examples
  --------
  
  This transformation can be put on any class function. For example,
  
  >>> import brainpy.math as bm
  >>> 
  >>> class SomeProgram(bp.BrainPyObject):
  >>>   def __init__(self):
  >>>      super(SomeProgram, self).__init__()
  >>>      self.a = bm.zeros(2)
  >>>      self.b = bm.Variable(bm.ones(2))
  >>> 
  >>>   @bm.cls_jit(inline=True)
  >>>   def __call__(self, *args, **kwargs):
  >>>      a = bm.random.uniform(size=2)
  >>>      a = a.at[0].set(1.)
  >>>      self.b += a
  >>>      return self.b
  >>> 
  >>> program = SomeProgram()
  >>> program()
  
  Parameters
  ----------
  {jit_pars}

  Returns
  -------
  func : JITTransform
    A callable jitted function, set up for just-in-time compilation.
  """
  if func is None:
    return lambda f: _make_jit_fun(fun=f,
                                   static_argnums=static_argnums,
                                   static_argnames=static_argnames,
                                   device=device,
                                   inline=inline,
                                   keep_unused=keep_unused,
                                   abstracted_axes=abstracted_axes)
  else:
    return _make_jit_fun(fun=func,
                         static_argnums=static_argnums,
                         static_argnames=static_argnames,
                         device=device,
                         inline=inline,
                         keep_unused=keep_unused,
                         abstracted_axes=abstracted_axes)


cls_jit.__doc__ = cls_jit.__doc__.format(jit_pars=_jit_par)


def _make_jit_fun(
    fun: Callable,
    static_argnums: Union[int, Iterable[int], None] = None,
    static_argnames: Union[str, Iterable[str], None] = None,
    device: Optional[Any] = None,
    inline: bool = False,
    keep_unused: bool = False,
    abstracted_axes: Optional[Any] = None,
):
  @wraps(fun)
  def call_fun(self, *args, **kwargs):
    fun2 = partial(fun, self)
    if jax.config.jax_disable_jit:
      return fun2(*args, **kwargs)
    cache = get_stack_cache(fun2)  # TODO: better cache mechanism
    if cache is None:
      with jax.ensure_compile_time_eval():
        args_, kwargs_ = jax.tree_util.tree_map(abstract, (args, kwargs))
        with VariableStack() as stack:
          _ = jax.eval_shape(fun2, *args_, **kwargs_)
        del args_, kwargs_
      _transform = jax.jit(
        _make_transform(fun2, stack),
        static_argnums=jax.tree_util.tree_map(lambda a: a + 1, static_argnums),
        static_argnames=static_argnames,
        device=device,
        inline=inline,
        keep_unused=keep_unused,
        abstracted_axes=abstracted_axes
      )
      cache_stack(fun2, (stack, _transform))  # cache
    else:
      stack, _transform = cache
    del cache
    out, changes = _transform(stack.dict_data(), *args, **kwargs)
    for key, v in stack.items():
      v._value = changes[key]
    return out

  return call_fun


def _make_transform(fun, stack):
  def _transform_function(variable_data: dict, *args, **kwargs):
    for key, v in stack.items():
      v._value = variable_data[key]
    out = fun(*args, **kwargs)
    changes = stack.dict_data()
    return out, changes

  return _transform_function
