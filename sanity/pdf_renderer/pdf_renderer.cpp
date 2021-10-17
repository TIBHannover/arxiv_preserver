#include "tensorflow/core/framework/op.h"
#include "tensorflow/core/framework/op_kernel.h"
#include "tensorflow/core/framework/shape_inference.h"

#include <memory>

using namespace tensorflow;

REGISTER_OP("PDFRenderer")
    .Input("contents: string")
    .Input("contents: string")
    .Input("contents: string")
    .Output("image: uint8")
    .Output("page_number: uint8")
    .SetShapeFn([](::tensorflow::shape_inference::InferenceContext *c) {
      c->set_output(0, c->input(0));
      return Status::OK();
    });

class PDFRendererOp : public OpKernel {
public:
  explicit PDFRendererOp(OpKernelConstruction *context) : OpKernel(context) {}

  void Compute(OpKernelContext *context) override {
    // Grab the input tensor
    const Tensor &input_tensor = context->input(0);
    auto input = input_tensor.flat<int32>();

    // Create an output tensor
    Tensor *output_tensor = NULL;
    OP_REQUIRES_OK(context, context->allocate_output(0, input_tensor.shape(), &output_tensor));
    auto output_flat = output_tensor->flat<int32>();

    // Set all but the first element of the output tensor to 0.
    const int N = input.size();
    for (int i = 1; i < N; i++) {
      output_flat(i) = 0;
    }

    // Preserve the first input value if possible.
    if (N > 0)
      output_flat(0) = input(0);
  }
};

REGISTER_KERNEL_BUILDER(Name("PDFRenderer").Device(DEVICE_CPU), PDFRendererOp);
