#ifndef _BRAINPY_ATOMIC_PROD_KERNELS_H_
#define _BRAINPY_ATOMIC_PROD_KERNELS_H_

#include <cstddef>
#include <cstdint>
#include "pybind11_kernel_helpers.h"
#include "kernel_helpers_gpu.h"

namespace brainpy_lib {
    struct COOAtomicProdDescriptor {
        std::uint32_t conn_size;
        std::uint32_t post_size;
    };

    // homogeneous
    void
    gpu_coo_atomic_prod_homo_f32_i32(cudaStream_t stream, void **buffers, const char *opaque, std::size_t opaque_len);
    void
    gpu_coo_atomic_prod_homo_f32_i64(cudaStream_t stream, void **buffers, const char *opaque, std::size_t opaque_len);
    void
    gpu_coo_atomic_prod_homo_f64_i32(cudaStream_t stream, void **buffers, const char *opaque, std::size_t opaque_len);
    void
    gpu_coo_atomic_prod_homo_f64_i64(cudaStream_t stream, void **buffers, const char *opaque, std::size_t opaque_len);

    // heterogeneous
    void
    gpu_coo_atomic_prod_heter_f32_i32(cudaStream_t stream, void **buffers, const char *opaque, std::size_t opaque_len);
    void
    gpu_coo_atomic_prod_heter_f32_i64(cudaStream_t stream, void **buffers, const char *opaque, std::size_t opaque_len);
    void
    gpu_coo_atomic_prod_heter_f64_i32(cudaStream_t stream, void **buffers, const char *opaque, std::size_t opaque_len);
    void
    gpu_coo_atomic_prod_heter_f64_i64(cudaStream_t stream, void **buffers, const char *opaque, std::size_t opaque_len);

    // descriptors
    pybind11::bytes build_coo_atomic_prod_descriptor(std::uint32_t conn_size, std::uint32_t post_size);

}  // namespace brainpy_lib

#endif