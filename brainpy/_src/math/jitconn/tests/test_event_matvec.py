# -*- coding: utf-8 -*-
from functools import partial

import jax
import jax.numpy as jnp
from absl.testing import parameterized
import pytest

import brainpy.math as bm
from brainpy._src.dependency_check import import_taichi

if import_taichi(error_if_not_found=False) is None:
  pytest.skip('no taichi', allow_module_level=True)


shapes = [(100, 200), (10, 1000), (2, 1000), (1000, 10), (1000, 2)]
shapes = [(100, 200), (2, 1000), (1000, 2)]

taichi_mv_prob_homo = bm.jitconn.event_mv_prob_homo
taichi_mv_prob_uniform = bm.jitconn.event_mv_prob_uniform
taichi_mv_prob_normal = bm.jitconn.event_mv_prob_normal


class Test_event_matvec_prob_conn(parameterized.TestCase):
    def __init__(self, *args, platform='cpu', **kwargs):
        super(Test_event_matvec_prob_conn, self).__init__(*args, **kwargs)
        bm.set_platform(platform)
        print()

    @parameterized.product(
        transpose=[True, False],
        x64=[True, False],
        outdim_parallel=[True, False],
        shape=shapes,
        prob=[0.01, 0.1, 0.5],
        homo_data=[-1., ],
        bool_event=[True, False],
        seed=[1234],
    )
    def test_homo(self, shape, transpose, outdim_parallel, prob, homo_data, bool_event=True, seed=1234, x64=False):
        print(f'_test_homo: '
              f'shape = {shape}, '
              f'transpose = {transpose}, '
              f'outdim_parallel = {outdim_parallel}, '
              f'prob={prob}, '
              f'homo_data = {homo_data}, '
              f'bool_event = {bool_event}, '
              f'x64={x64}')

        if x64:
            bm.enable_x64()
        rng = bm.random.RandomState()
        events = bm.as_jax(rng.random(shape[0] if transpose else shape[1])) < 0.1
        if not bool_event:
            events = events.astype(float)

        r1 = taichi_mv_prob_homo(events,
                                 homo_data,
                                 conn_prob=prob,
                                 shape=shape,
                                 seed=seed,
                                 outdim_parallel=outdim_parallel,
                                 transpose=transpose)
        r1 = jax.block_until_ready(r1)

        r2 = taichi_mv_prob_homo(events,
                                 homo_data,
                                 conn_prob=prob,
                                 shape=shape,
                                 seed=seed,
                                 outdim_parallel=outdim_parallel,
                                 transpose=transpose)
        r2 = jax.block_until_ready(r2)
        self.assertTrue(jnp.allclose(r1, r2, atol=1e-6))

        # indices, indptr = bp.conn.FixedProb(prob)(*shape).require('pre2post')
        # indices = bm.as_jax(indices)
        # indptr = bm.as_jax(indptr)
        # r3 = event_ops.event_csr_matvec(homo_data, indices, indptr, events,
        #                                 shape=shape, transpose=transpose)
        # print('Homo difference: ', bm.abs(r1 - r3).sum() / r1.size)

        if x64:
            bm.disable_x64()
        bm.clear_buffer_memory()

    @parameterized.product(
        transpose=[True, False],
        x64=[True, False],
        outdim_parallel=[True, False],
        shape=shapes,
        prob=[0.01, 0.1, 0.5],
        bool_event=[True, False],
        seed=[1234],
    )
    def test_homo_vmap(self, shape, transpose, outdim_parallel, prob, bool_event=True, seed=1234, x64=False):
        print(f'_test_homo_vmap: '
              f'shape = {shape}, '
              f'transpose = {transpose}, '
              f'outdim_parallel = {outdim_parallel}, '
              f'prob={prob}, '
              f'bool_event = {bool_event}, '
              f'x64={x64}')
        if x64:
            bm.enable_x64()
        rng = bm.random.RandomState()
        events = rng.random((10, shape[0] if transpose else shape[1])) < 0.1
        events = bm.as_jax(events)
        if not bool_event:
            events = events.astype(float)
        weights = bm.as_jax(rng.random(10))

        f1 = jax.vmap(
            lambda event, data: taichi_mv_prob_homo(
                event, data, conn_prob=prob, shape=shape, seed=seed,
                transpose=transpose, outdim_parallel=outdim_parallel
            )[0]
        )
        r1 = f1(events, weights)
        r1 = jax.block_until_ready(r1)
        r2 = f1(events, weights)
        r2 = jax.block_until_ready(r2)
        self.assertTrue(jnp.allclose(r1, r2, atol=1e-6))
        if x64:
            bm.disable_x64()
        bm.clear_buffer_memory()

    @parameterized.named_parameters(
        dict(testcase_name=f'_test_homo_grad: '
                           f'shape = {shape}, '
                           f'transpose = {transpose}, '
                           f'outdim_parallel = {outdim_parallel}, '
                           f'prob={prob}, x64={x64}',
             shape=shape, transpose=transpose,
             outdim_parallel=outdim_parallel,
             prob=prob, seed=1234,
             x64=x64)
        for transpose in [True, False]
        for x64 in [True, False]
        for outdim_parallel in [True, False]
        for shape in shapes
        for prob in [0.01, 0.1, 0.5]
    )
    def test_homo_grad(self, shape, transpose, outdim_parallel, prob, seed=1234, x64=False):
        print(f'_test_homo_grad: '
              f'shape = {shape}, '
              f'transpose = {transpose}, '
              f'outdim_parallel = {outdim_parallel}, '
              f'prob={prob}, x64={x64}')
        if x64:
            bm.enable_x64()
        rng = bm.random.RandomState()
        events = rng.random(shape[0] if transpose else shape[1]) < 0.5
        events = bm.as_jax(events)
        events = events.astype(float)

        f1 = jax.grad(
            lambda event, data: taichi_mv_prob_homo(
                event, data, conn_prob=prob, shape=shape, seed=seed,
                outdim_parallel=outdim_parallel, transpose=transpose)[0].sum(),
            argnums=0
        )
        r1 = f1(events, 1.)
        r1 = jax.block_until_ready(r1)

        r2 = f1(events, 2.)
        r2 = jax.block_until_ready(r2)

        r3 = f1(events, 3.)
        r3 = jax.block_until_ready(r3)

        self.assertTrue(jnp.allclose(r1 * 3., r3, atol=1e-6))
        self.assertTrue(jnp.allclose(r1 * 2., r2, atol=1e-6))
        if x64:
            bm.disable_x64()
        bm.clear_buffer_memory()

    @parameterized.named_parameters(
        dict(testcase_name=f'test_uniform: '
                           f'shape = {shape}, '
                           f'transpose = {transpose}, '
                           f'outdim_parallel = {outdim_parallel}, '
                           f'prob={prob}, '
                           f'w_low = {w_low}, '
                           f'w_high = {w_high}, '
                           f'bool_event = {bool_event}, '
                           f'x64={x64}',
             shape=shape,
             transpose=transpose,
             outdim_parallel=outdim_parallel,
             prob=prob,
             w_low=w_low,
             w_high=w_high,
             bool_event=bool_event,
             seed=1234,
             x64=x64
             )
        for transpose in [True, False]
        for x64 in [True, False]
        for outdim_parallel in [True, False]
        for shape in shapes
        for prob in [0.01, 0.1, 0.4]
        for w_low, w_high in [(-1., 0.), (0., 1.), (-1., 1.)]
        for bool_event in [True, False]
    )
    def test_uniform(self, shape, transpose, outdim_parallel, prob, w_low, w_high,
                     bool_event=True, seed=1234, x64=False):
        print(f'_test_uniform: '
              f'shape = {shape}, '
              f'transpose = {transpose}, '
              f'outdim_parallel = {outdim_parallel}, '
              f'prob={prob}, '
              f'w_low = {w_low}, '
              f'w_high = {w_high}, '
              f'x64={x64}')
        if x64:
            bm.enable_x64()
        rng = bm.random.RandomState()
        events = rng.random(shape[0] if transpose else shape[1]) < 0.1
        events = bm.as_jax(events)
        if not bool_event:
            events = events.astype(float)

        r1 = taichi_mv_prob_uniform(events,
                                    w_low=w_low,
                                    w_high=w_high,
                                    conn_prob=prob,
                                    shape=shape,
                                    seed=seed,
                                    outdim_parallel=outdim_parallel,
                                    transpose=transpose)
        r1 = jax.block_until_ready(r1)

        r2 = taichi_mv_prob_uniform(events,
                                    w_low=w_low,
                                    w_high=w_high,
                                    conn_prob=prob,
                                    shape=shape,
                                    seed=seed,
                                    outdim_parallel=outdim_parallel,
                                    transpose=transpose)
        r2 = jax.block_until_ready(r2)
        self.assertTrue(jnp.allclose(r1, r2, atol=1e-6))

        if x64:
            bm.disable_x64()
        bm.clear_buffer_memory()

    @parameterized.named_parameters(
        dict(shape=shape, transpose=transpose,
             outdim_parallel=outdim_parallel, prob=prob,
             bool_event=bool_event,
             x64=x64,
             seed=1234,
             testcase_name=f'_test_uniform_vmap: '
                           f'shape={shape}, '
                           f'transpose={transpose}, '
                           f'bool_event={bool_event}, '
                           f'outdim_parallel={outdim_parallel}, '
                           f'prob={prob}, '
                           f'x64={x64}')
        for transpose in [True, False]
        for x64 in [True, False]
        for outdim_parallel in [True, False]
        for shape in shapes
        for prob in [0.01, 0.1]
        for bool_event in [True, False]
    )
    def test_uniform_vmap(self, shape, transpose, outdim_parallel, prob,
                          bool_event=True, seed=1234, x64=False):
        print(f'_test_uniform_vmap: '
              f'shape = {shape}, '
              f'transpose = {transpose}, '
              f'outdim_parallel = {outdim_parallel}, '
              f'prob={prob}, x64={x64}')
        if x64:
            bm.enable_x64()
        rng = bm.random.RandomState()
        events = rng.random((10, shape[0] if transpose else shape[1])) < 0.1
        events = bm.as_jax(events)
        if not bool_event:
            events = events.astype(float)

        f1 = jax.vmap(
            lambda e: taichi_mv_prob_uniform(e,
                                             w_low=0.,
                                             w_high=1.,
                                             conn_prob=prob,
                                             shape=shape,
                                             seed=seed,
                                             outdim_parallel=outdim_parallel,
                                             transpose=transpose)
        )

        r1 = f1(events)
        r1 = jax.block_until_ready(r1)
        r2 = f1(events)
        r2 = jax.block_until_ready(r2)
        self.assertTrue(jnp.allclose(r1, r2, atol=1e-6))
        if x64:
            bm.disable_x64()
        bm.clear_buffer_memory()

    @parameterized.named_parameters(
        dict(shape=shape,
             transpose=transpose,
             outdim_parallel=outdim_parallel,
             prob=prob,
             seed=1234,
             testcase_name=f'_test_uniform_grad: '
                           f'shape = {shape}, '
                           f'transpose = {transpose}, '
                           f'outdim_parallel = {outdim_parallel}, '
                           f'prob={prob}, x64={x64}')
        for transpose in [True, False]
        for x64 in [True, False]
        for outdim_parallel in [True, False]
        for shape in shapes
        for prob in [0.01, 0.1]
    )
    def test_uniform_grad(self, shape, transpose, outdim_parallel, prob, seed=1234, x64=False):
        print(f'_test_uniform_grad: '
              f'shape = {shape}, '
              f'transpose = {transpose}, '
              f'outdim_parallel = {outdim_parallel}, '
              f'prob={prob}, x64={x64}')
        if x64:
            bm.enable_x64()
        rng = bm.random.RandomState()
        events = rng.random(shape[0] if transpose else shape[1]) < 0.1
        events = bm.as_jax(events)
        events = events.astype(float)

        f1 = jax.grad(
            lambda e, w_high: taichi_mv_prob_uniform(
                e,
                w_low=0.,
                w_high=w_high,
                conn_prob=prob,
                shape=shape,
                seed=seed,
                outdim_parallel=outdim_parallel,
                transpose=transpose).sum()
        )

        r1 = f1(events, 1.)
        r1 = jax.block_until_ready(r1)
        r2 = f1(events, 2.)
        r2 = jax.block_until_ready(r2)
        self.assertTrue(bm.allclose(r1 * 2., r2, atol=1e-6))
        # print(r1)
        if x64:
            bm.disable_x64()
        bm.clear_buffer_memory()

    @parameterized.named_parameters(
        dict(shape=shape,
             transpose=transpose,
             outdim_parallel=outdim_parallel,
             prob=prob,
             w_mu=w_mu,
             w_sigma=w_sigma,
             bool_event=bool_event,
             x64=x64,
             seed=1234,
             testcase_name=f'_test_normal: '
                           f'shape={shape}, '
                           f'transpose={transpose}, '
                           f'outdim_parallel={outdim_parallel}, '
                           f'prob={prob}, '
                           f'w_mu={w_mu}, '
                           f'w_sigma={w_sigma}, '
                           f'bool_event={bool_event}, '
                           f'x64={x64}')
        for transpose in [True, False]
        for x64 in [True, False]
        for outdim_parallel in [True, False]
        for shape in shapes
        for prob in [0.01, 0.1, ]
        for w_mu, w_sigma in [(-1., 1.), (0., 0.1), (0., 0.5)]
        for bool_event in [True, False]
    )
    def test_normal(self, shape, transpose, outdim_parallel, prob, w_mu, w_sigma,
                    bool_event=True, seed=1234, x64=False):
        print(f'_test_normal: shape = {shape}, '
              f'transpose = {transpose}, outdim_parallel = {outdim_parallel}, prob={prob}, '
              f'w_mu = {w_mu}, w_sigma = {w_sigma}, x64={x64}')
        if x64:
            bm.enable_x64()
        rng = bm.random.RandomState()
        events = rng.random(shape[0] if transpose else shape[1]) < 0.1
        events = bm.as_jax(events)
        if not bool_event:
            events = events.astype(float)

        r1 = taichi_mv_prob_normal(events,
                                   w_mu=w_mu,
                                   w_sigma=w_sigma,
                                   conn_prob=prob,
                                   shape=shape,
                                   seed=seed,
                                   outdim_parallel=outdim_parallel,
                                   transpose=transpose)
        r1 = jax.block_until_ready(r1)

        r2 = taichi_mv_prob_normal(events,
                                   w_mu=w_mu,
                                   w_sigma=w_sigma,
                                   conn_prob=prob,
                                   shape=shape,
                                   seed=seed,
                                   outdim_parallel=outdim_parallel,
                                   transpose=transpose)
        r2 = jax.block_until_ready(r2)
        self.assertTrue(jnp.allclose(r1, r2, atol=1e-6))

        if x64:
            bm.disable_x64()
        bm.clear_buffer_memory()

    @parameterized.named_parameters(
        dict(shape=shape,
             transpose=transpose,
             outdim_parallel=outdim_parallel,
             prob=prob,
             bool_event=bool_event,
             x64=x64,
             seed=1234,
             testcase_name=f'_test_normal_vmap: '
                           f'shape={shape}, '
                           f'transpose={transpose}, '
                           f'outdim_parallel={outdim_parallel}, '
                           f'prob={prob}, '
                           f'bool_event={bool_event}, '
                           f'x64={x64}')
        for transpose in [True, False]
        for x64 in [True, False]
        for outdim_parallel in [True, False]
        for shape in shapes
        for prob in [0.01, 0.1]
        for bool_event in [True, False]
    )
    def test_normal_vmap(self, shape, transpose, outdim_parallel, prob,
                         bool_event=True, seed=1234, x64=False):
        print(f'_test_normal_vmap: '
              f'shape = {shape}, '
              f'transpose = {transpose}, '
              f'outdim_parallel = {outdim_parallel}, '
              f'prob={prob}, x64={x64}')
        if x64:
            bm.enable_x64()
        rng = bm.random.RandomState()
        events = rng.random((10, shape[0] if transpose else shape[1])) < 0.1
        events = bm.as_jax(events)
        if not bool_event:
            events = events.astype(float)

        f1 = jax.vmap(lambda e: taichi_mv_prob_normal(e,
                                                      w_mu=0.,
                                                      w_sigma=1.,
                                                      conn_prob=prob,
                                                      shape=shape,
                                                      seed=seed,
                                                      outdim_parallel=outdim_parallel,
                                                      transpose=transpose))
        r1 = f1(events)
        r1 = jax.block_until_ready(r1)
        r2 = f1(events)
        r2 = jax.block_until_ready(r2)
        self.assertTrue(jnp.allclose(r1, r2, atol=1e-6))
        if x64:
            bm.disable_x64()
        bm.clear_buffer_memory()

    @parameterized.named_parameters(
        dict(shape=shape,
             transpose=transpose,
             outdim_parallel=outdim_parallel,
             prob=prob,
             x64=x64,
             seed=1234,
             testcase_name=f'_test_normal_grad: '
                           f'shape = {shape}, '
                           f'transpose = {transpose}, '
                           f'outdim_parallel = {outdim_parallel}, '
                           f'prob={prob}, x64={x64}')
        for transpose in [True, False]
        for x64 in [True, False]
        for outdim_parallel in [True, False]
        for shape in shapes
        for prob in [0.01, 0.1]
    )
    def test_normal_grad(self, shape, transpose, outdim_parallel, prob, seed=1234, x64=False):
        print(f'_test_normal_grad: '
              f'shape = {shape}, '
              f'transpose = {transpose}, '
              f'outdim_parallel = {outdim_parallel}, '
              f'prob={prob}, x64={x64}')
        if x64:
            bm.enable_x64()
        rng = bm.random.RandomState()
        events = rng.random(shape[0] if transpose else shape[1]) < 0.1
        events = bm.as_jax(events)
        events = events.astype(float)

        f1 = jax.jit(
            jax.grad(
                lambda e, w_sigma: taichi_mv_prob_normal(
                    e,
                    w_mu=0.,
                    w_sigma=w_sigma,
                    conn_prob=prob,
                    shape=shape,
                    seed=seed,
                    outdim_parallel=outdim_parallel,
                    transpose=transpose).sum()
            )
        )
        r1 = f1(events, 1.)
        r1 = jax.block_until_ready(r1)
        r2 = f1(events, 2.)
        r2 = jax.block_until_ready(r2)
        self.assertTrue(bm.allclose(r1 * 2, r2, atol=1e-6))
        if x64:
            bm.disable_x64()
        bm.clear_buffer_memory()
