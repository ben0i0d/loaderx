# mloader
Minimal data loader for Flax

## Rationale for Creating mloader
While Flax supports various data loading backends—such as PyTorch, TensorFlow, Grain, and jax_dataloader—these often come with nontrivial dependencies.
1. Installing heavy frameworks like PyTorch or TensorFlow solely for data loading is undesirable.
2. Grain offers a clean API but suffers from suboptimal performance in practice.
3. jax_dataloader leverages GPU memory by default, which may lead to inefficient memory usage in certain scenarios.

## Design Goals of mloader
mloader is designed with simplicity and efficiency in mind.
It follows a pragmatic approach—favoring low memory overhead and minimal dependencies.
The implementation targets common use cases, with a particular focus on single-host training pipelines.

## Current Limitations
At present, mloader only supports single-host scenarios and does not yet address multi-host training setups.

## How to integrate it with Flax. 
Below is a code example.

The mloader is mainly inspired by the design of Grain, so avoid using patterns like `for epoch in num_epochs`.

```
def loss_fn(model: CNN, batch):
  logits = model(batch['data'])
  loss = optax.softmax_cross_entropy_with_integer_labels(logits=logits, labels=batch['label']).mean()
  return loss, logits

@nnx.jit
def train_step(model: CNN, optimizer: nnx.Optimizer, metrics: nnx.MultiMetric, batch):
  """Train for a single step."""
  grad_fn = nnx.value_and_grad(loss_fn, has_aux=True)
  (loss, logits), grads = grad_fn(model, batch)
  metrics.update(loss=loss, logits=logits, labels=batch['label'])  # In-place updates.
  optimizer.update(grads)  # In-place updates.

@nnx.jit
def eval_step(model: CNN, metrics: nnx.MultiMetric, batch):
  loss, logits = loss_fn(model, batch)
  metrics.update(loss=loss, logits=logits, labels=batch['label'])  # In-place updates.

@nnx.jit
def pred_step(model: CNN, batch):
  logits = model(batch['data'])
  return logits.argmax(axis=1)
```