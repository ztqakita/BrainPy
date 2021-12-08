# -*- coding: utf-8 -*-

import brainpy as bp

bp.math.enable_x64()
bp.math.set_platform('cpu')


def try1():
  @bp.odeint
  def int_x(x, t, Iext):
    dx = x ** 3 - x + Iext
    return dx

  analyzer = bp.analysis.PhasePlane1D(model=int_x,
                                      target_vars={'x': [-2, 2]},
                                      pars_update={'Iext': 0.},
                                      resolutions=0.001)

  analyzer.plot_vector_field()
  analyzer.plot_fixed_point(show=True)


def try2():
  @bp.odeint
  def int_x(x, t, Iext):
    return bp.math.sin(x) + Iext

  pp = bp.analysis.PhasePlane1D(model=int_x,
                                target_vars={'x': [-10, 10]},
                                pars_update={'Iext': 0.999},
                                resolutions=0.0001)

  pp.plot_vector_field()
  pp.plot_fixed_point(show=True)

  bifurcation = bp.analysis.Bifurcation1D(model=int_x,
                                          target_vars={'x': [-5, 5]},
                                          target_pars={'Iext': [0., 1.5]},
                                          resolutions=0.001)
  bifurcation.plot_bifurcation(show=True, tol_loss=1e-7)


try1()
try2()