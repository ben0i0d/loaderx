# loaderx
Minimal data loader for Flax

## Rationale for Creating loaderx
While Flax supports various data loading backends—such as PyTorch, TensorFlow, Grain, and jax_dataloader.
1. Installing heavy frameworks like PyTorch or TensorFlow solely for data loading is undesirable.
2. Grain offers a clean API but suffers from suboptimal performance in practice.
3. jax_dataloader leverages GPU memory by default, which may lead to inefficient memory usage in certain scenarios.

## Design Goals of loaderx
loaderx is designed with simplicity and efficiency in mind.
It follows a pragmatic approach—favoring low memory overhead and minimal dependencies.
The implementation targets common use cases, with a particular focus on single-host training pipelines.

## Current Limitations
At present, loaderx only supports single-host scenarios and does not yet address multi-host training setups.

## How to integrate it with Flax.
The loaderx is mainly inspired by the design of Grain, so avoid using patterns like `for epoch in num_epochs`.

The following is a Flax code for train and valid.
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

train_loader = DataLoader(dataset = Dataset(dataset_path, data, label),batch_size=256,num_epochs=10)
for step, batch in enumerate(train_loader):
    train_step(model, optimizer, metrics, batch)
    if step > 0 and step % 500 == 0:
        train_metrics = metrics.compute()
        print("Step:{}_Train Acc@1: {} loss: {} ".format(step,train_metrics['accuracy'],train_metrics['loss']))
        metrics.reset()  # Reset the metrics for the train set.

        # Compute the metrics on the test set after each training epoch.
        val_loader = DataLoader(dataset = Dataset(dataset_path, data, label),batch_size=256)
        for val_batch in val_loader:
            eval_step(model, metrics, val_batch)
        val_metrics = metrics.compute()
        print("Step:{}_Val Acc@1: {} loss: {} ".format(step,val_metrics['accuracy'],val_metrics['loss']))
        metrics.reset()  # Reset the metrics for the val set.
```