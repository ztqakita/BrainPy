# -*- coding: utf-8 -*-
import numpy as np

import brainpy as bp
import brainpy.math as bm
from absl.testing import parameterized
from brainpy._src.dyn.neurons import lif


class Test_lif(parameterized.TestCase):
  @parameterized.named_parameters(
    {'testcase_name': f'{name}', 'neuron': name}
    for name in lif.__all__
  )
  def test_run_shape(self, neuron):
    model = getattr(lif, neuron)(size=1)
    if neuron in ['IF', 'IFLTC']:
      runner = bp.DSRunner(model,
                           monitors=['V'],
                           progress_bar=False)
      runner.run(10.)
      self.assertTupleEqual(runner.mon['V'].shape, (100, 1))
    else:
      runner = bp.DSRunner(model,
                           monitors=['V', 'spike'],
                           progress_bar=False)
      runner.run(10.)
      self.assertTupleEqual(runner.mon['V'].shape, (100, 1))
      self.assertTupleEqual(runner.mon['spike'].shape, (100, 1))

  @parameterized.named_parameters(
    {'testcase_name': f'{name}', 'neuron': name}
    for name in lif.__all__
  )
  def test_training_shape(self, neuron):
    model = getattr(lif, neuron)(size=10, mode=bm.training_mode)
    runner = bp.DSRunner(model,
                         monitors=['V'],
                         progress_bar=False)
    runner.run(10.)
    self.assertTupleEqual(runner.mon['V'].shape, (1, 100, 10))

  @parameterized.named_parameters(
    {'testcase_name': f'{name}', 'neuron': name}
    for name in lif.__all__
  )
  def test_training_lif(self, neuron):
    if neuron not in ['IF', 'IFLTC']:
      model1 = getattr(lif, neuron)(size=1,
                                   V_initializer=bp.init.Constant(-70.),
                                   mode=bm.training_mode,
                                   spk_reset='hard',
                                   scaling=bm.Scaling.transform(V_range=[-70, 30], scaled_V_range=[0, 1]))
      model2 = getattr(lif, neuron)(size=1,
                                    V_initializer=bp.init.Constant(-70.),
                                    mode=bm.training_mode,
                                    spk_reset='hard',
                                    scaling=bm.Scaling(scale=1, bias=0))
      indices = bm.arange(5000)
      spks1 = bm.for_loop(lambda i: model1.step_run(i, 10./model1.scaling.scale), indices, jit=True)
      spks2 = bm.for_loop(lambda i: model2.step_run(i, 10./model2.scaling.scale), indices, jit=True)
      self.assertTrue(np.allclose(spks1, spks2))